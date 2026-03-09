"""Overlay and fallback mixin for GeminiRenderer.

Handles branding overlays (logo, product, text, CTA) and fallback image video generation.
"""
import os
import subprocess
import sys
import time
from typing import Dict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from utils.logger import logger


class OverlayMixin:
    """Mixin: applies branding overlays and generates fallback static-image videos."""

    async def _generate_fallback_image_video(self, scene: Dict, idx: int, temp_dir: str) -> str:
        """Generates a static image via Imagen (saved to GridFS) and animates it."""
        from api.services.db_mongo_service import get_file_from_gridfs
        from api.services.ai_assist_service import ai_assist_service
        
        prompt = self._build_prompt(scene)
        duration_str = scene.get("duration", "5s")
        try:
            duration_sec = int(duration_str.replace("s", ""))
        except:
            duration_sec = 5
        
        logger.info(f"       Fallback: Generating static image for scene {idx} ({duration_sec}s)...")
        try:
            grid_file_id = await ai_assist_service.generate_fallback_image(prompt)
            
            if not grid_file_id:
                return None
                
            img_data, _ = await get_file_from_gridfs(grid_file_id)
            
            img_temp = os.path.join(temp_dir, f"fallback_{idx}_{int(time.time())}.jpg")
            with open(img_temp, "wb") as f:
                f.write(img_data)
                
            out_video = os.path.join(temp_dir, f"scene_fallback_{idx}_{int(time.time())}.mp4")
            fps = 25
            frames = fps * duration_sec
            cmd = [
                "ffmpeg", "-y", "-loop", "1", "-i", img_temp,
                "-vf", f"zoompan=z='zoom+0.0005':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=720x1280",
                "-c:v", "libx264", "-t", str(duration_sec), "-pix_fmt", "yuv420p", "-preset", "medium",
                out_video
            ]
            subprocess.run(cmd, capture_output=True)
            return out_video if os.path.exists(out_video) else None
        except Exception as e:
            logger.error(f"       Fallback Error: {e}")
            return None

    async def _apply_audio_and_overlay(self, idx: int, scene: Dict, video_path: str, temp_dir: str) -> str:
        """Applies overlays BRAND logo/product images on the video."""
        from api.services.db_mongo_service import get_file_from_gridfs
        output_path = video_path
        
        try:
            # ── BRAND LOGO OVERLAY (Dynamic position) ──
            logo_ids = self.assets.get("logo", [])
            product_ids = self.assets.get("product", [])
            brand_name = self.context.get("product_understanding", {}).get("brand_name", "")
            product_name = self.context.get("product_understanding", {}).get("product_name", "")
            product_info = self.context.get("product_understanding", {})
            scene_name = scene.get("scene", "")

            overlay_inputs = []
            filter_complex = "[0:v]"
            input_idx = 1
            
            # A. Logo Overlay
            if logo_ids:
                img_bytes, metadata = await get_file_from_gridfs(logo_ids[0])
                if img_bytes:
                    logo_path = os.path.join(temp_dir, f"overlay_logo_{idx}.png")
                    with open(logo_path, "wb") as f:
                        f.write(img_bytes)
                    overlay_inputs += ["-i", logo_path]
                    curr_logo_idx = input_idx
                    filter_complex += f"[{curr_logo_idx}:v]scale=150:-1[logo];{filter_complex}[logo]overlay=W-w-20:20[v_with_logo]"
                    filter_complex = "[v_with_logo]"
                    input_idx += 1

            # B. Product Image Overlay (Solution/Proof/CTA scenes)
            relevant_scenes = ["Solution", "Proof", "CTA", "Introduce product", "Show results", "Drive action"]
            if scene_name in relevant_scenes and product_ids:
                img_data, _ = await get_file_from_gridfs(product_ids[0])
                if img_data:
                    img_path = os.path.join(temp_dir, f"overlay_product_{idx}.png")
                    with open(img_path, "wb") as f:
                        f.write(img_data)
                    overlay_inputs += ["-i", img_path]
                    curr_img_idx = input_idx
                    filter_complex += f"[{curr_img_idx}:v]scale=200:-1[prod];{filter_complex}[prod]overlay=W-w-20:H-h-20[v_with_prod]"
                    filter_complex = "[v_with_prod]"
                    input_idx += 1
            
            # C. Product Name Text
            if scene_name in ["Solution", "CTA", "Introduce product", "Drive action"]:
                text_to_show = f"{brand_name} {product_name}".strip().upper()
                if text_to_show:
                    font_path = "C\\\\:/Windows/Fonts/arial.ttf"
                    filter_complex += f",drawtext=text='{text_to_show}':fontfile='{font_path}':fontsize=36:fontcolor=white:shadowcolor=black@0.5:shadowx=2:shadowy=2:x=(w-text_w)/2:y=H-th-80"
            
            # D. BUY NOW CTA Banner
            if scene_name in ["CTA", "Drive action"]:
                product_url = product_info.get("product_url", "") or self.context.get("product_input", {}).get("product_url", "")
                if product_url:
                    from urllib.parse import urlparse
                    domain = urlparse(product_url).netloc or product_url
                    buy_text = f"BUY NOW  {domain}".replace("'", "").replace(":", "\\\\:")
                    font_path = "C\\\\:/Windows/Fonts/arialbd.ttf"
                    filter_complex += (
                        f",drawbox=x=0:y=H-60:w=W:h=60:color=black@0.7:t=fill"
                        f",drawtext=text='{buy_text}':fontfile='{font_path}':fontsize=28:fontcolor=white:x=(w-text_w)/2:y=H-45"
                    )

            if input_idx > 1 or "drawtext" in filter_complex:
                if filter_complex != "[0:v]":
                    overlay_out = os.path.join(temp_dir, f"scene_{idx}_branded.mp4")
                    cmd = ["ffmpeg", "-y", "-i", output_path] + overlay_inputs + [
                        "-filter_complex", filter_complex,
                        "-c:a", "copy", overlay_out
                    ]
                    subprocess.run(cmd, capture_output=True)
                    if os.path.exists(overlay_out):
                        output_path = overlay_out
                        
            return output_path
        except Exception as e:
            logger.error(f"       Failed to apply branding overlay: {e}")
            return video_path
