"""Video merging mixin for GeminiRenderer.

Handles video normalization, fast binary-stitch merge, and download.
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import requests
from typing import List

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from utils.logger import logger


class VideoMergerMixin:
    """Mixin: normalizes, downloads, and merges scene videos via FFmpeg."""

    def _download_video(self, video_uri: str, output_path: str) -> bool:
        """Downloads a generated video using requests with API key."""
        try:
            url = video_uri
            if '?' in url:
                url += f"&key={self.api_key}"
            else:
                url += f"?key={self.api_key}"
            
            response = requests.get(url, stream=True, timeout=120)
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                logger.info(f"       Downloaded: {os.path.basename(output_path)}")
                return True
            else:
                logger.error(f"       Download failed: HTTP {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"       Download error: {e}")
            return False

    def _normalize_videos(self, video_paths: List[str]) -> List[str]:
        """Normalizes all scene videos to identical resolution/fps/codec for safe concat.
        
        Converts each to: 720x1280 (9:16), 30fps, h264, aac.
        Only re-encodes if the video doesn't match target specs.
        """
        normalized = []
        for i, vp in enumerate(video_paths):
            try:
                probe_cmd = [
                    "ffprobe", "-v", "error",
                    "-select_streams", "v:0",
                    "-show_entries", "stream=width,height,r_frame_rate,codec_name",
                    "-of", "json", vp
                ]
                probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
                probe_data = json.loads(probe_result.stdout) if probe_result.stdout.strip() else {}
                
                streams = probe_data.get("streams", [{}])
                if streams:
                    w = streams[0].get("width", 0)
                    h = streams[0].get("height", 0)
                    codec = streams[0].get("codec_name", "")
                else:
                    w, h, codec = 0, 0, ""
                
                if w == self.TARGET_WIDTH and h == self.TARGET_HEIGHT and codec == "h264":
                    normalized.append(vp)
                    continue
                
                norm_path = os.path.join(tempfile.gettempdir(), f"norm_{int(time.time()*100)}_{i}.mp4")
                cmd = [
                    "ffmpeg", "-y", "-i", vp,
                    "-vf", f"scale={self.TARGET_WIDTH}:{self.TARGET_HEIGHT}:force_original_aspect_ratio=decrease,"
                           f"pad={self.TARGET_WIDTH}:{self.TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps={self.TARGET_FPS}",
                    "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
                    norm_path
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0 and os.path.exists(norm_path):
                    logger.info(f"     📐 Normalized scene {i+1}: {w}x{h} → {self.TARGET_WIDTH}x{self.TARGET_HEIGHT}")
                    normalized.append(norm_path)
                else:
                    logger.warning(f"     ⚠️ Normalization failed for scene {i+1}, using original")
                    normalized.append(vp)
            except Exception as e:
                logger.warning(f"     ⚠️ Normalization error for scene {i+1}: {e}")
                normalized.append(vp)
        
        return normalized

    def merge_videos(self, video_paths: List[str], final_output_path: str):
        """Merges multiple video files using FFmpeg.
        
        Strategy (priority order):
        1. NORMALIZE: Scale all scenes to 720x1280@30fps (ensures codec match)
        2. FAST BINARY STITCH: concat demuxer with -c copy (~1 sec)
        3. FALLBACK: Re-encode concat (handles remaining mismatches)
        """
        logger.info(f"   🔗 Merging {len(video_paths)} scenes into final video...")
        
        if len(video_paths) == 1:
            import shutil
            shutil.copy2(video_paths[0], final_output_path)
            logger.info(f"     Single scene — copied directly.")
            return
        
        # ── STEP 0: Normalize all videos to same resolution/codec ──
        logger.info(f"     📐 Normalizing {len(video_paths)} scenes to {self.TARGET_WIDTH}x{self.TARGET_HEIGHT}@{self.TARGET_FPS}fps...")
        video_paths = self._normalize_videos(video_paths)
        
        # ── METHOD 1: Fast Binary Stitch (no re-encoding) ──
        try:
            logger.info("     ⚡ Attempting fast binary-stitch merge (no re-encoding)...")
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                for path in video_paths:
                    safe_path = path.replace('\\', '/').replace("'", "'\\''")
                    f.write(f"file '{safe_path}'\n")
                concat_file = f.name
            
            cmd = [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", concat_file,
                "-c", "copy",
                final_output_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if os.path.exists(concat_file):
                os.remove(concat_file)
            
            if result.returncode == 0 and os.path.exists(final_output_path):
                file_size = os.path.getsize(final_output_path)
                if file_size > 1000:
                    logger.info(f"     ✅ Fast merge complete! ({file_size // 1024}KB)")
                    return
                else:
                    logger.warning(f"     ⚠️ Fast merge produced invalid file ({file_size}B). Trying fallback...")
            else:
                logger.warning(f"     ⚠️ Fast merge failed (rc={result.returncode}). Trying re-encode fallback...")
                if result.stderr:
                    logger.debug(f"     FFmpeg stderr: {result.stderr[:200]}")
        except Exception as e:
            logger.warning(f"     ⚠️ Fast merge error: {e}. Trying re-encode...")
        
        # ── METHOD 2: Re-encode concat fallback ──
        try:
            logger.info("     🔄 Attempting re-encode concat fallback...")
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                for path in video_paths:
                    safe_path = path.replace('\\', '/').replace("'", "'\\''")
                    f.write(f"file '{safe_path}'\n")
                concat_file = f.name
            
            cmd = [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", concat_file,
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",
                "-c:a", "aac", "-b:a", "128k",
                final_output_path
            ]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"     ✅ Re-encode concat merge complete!")
        except Exception as e:
            logger.error(f"     ❌ FFmpeg merge error: {e}")
        finally:
            if os.path.exists(concat_file):
                os.remove(concat_file)
