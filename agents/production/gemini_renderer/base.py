import asyncio
import json
import os
import subprocess
import tempfile
import requests
import glob
import time
from typing import Dict, List, Any
from google import genai
from google.genai import types
from dotenv import load_dotenv
from datetime import datetime

def render_log(message: str):
    """Writes rendering logs to a dedicated file for the user to review."""
    print(message)
    try:
        with open("render_stages.log", "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%H:%M:%S")
            f.write(f"[{timestamp}] {message}\n")
    except Exception:
        pass

# Load .env from root directory (parent of src)
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(dotenv_path)

class BaseRenderer:
    """Base class for ad rendering using Google Gemini (Veo 3.1) API.
    
    Contains shared logic for asset loading, merging, and audio pipeline.
    Subclasses should override _get_reference_images_for_scene and _generate_scene_prompts.
    """
    
    DEFAULT_MODEL = "veo-3.1-generate-preview"
    MAX_POLL_TIME = 600  # 10 minutes max per scene
    POLL_INTERVAL = 30   # Check every 30 seconds
    
    def __init__(self, variants_output, avatar_config, campaign_context):
        self.variants = variants_output
        if isinstance(avatar_config, list):
            self.avatar_list = avatar_config
            self.avatar = avatar_config[0] if avatar_config else {}
        elif isinstance(avatar_config, dict):
            avatar_data = avatar_config.get("selected_avatars")
            if not avatar_data:
                avatar_data = avatar_config.get("results", avatar_config)
            
            if isinstance(avatar_data, list):
                self.avatar_list = avatar_data
                self.avatar = avatar_data[0] if avatar_data else {}
            else:
                self.avatar = avatar_data
                self.avatar_list = [avatar_data] if avatar_data else []
        else:
            self.avatar = {}
            self.avatar_list = []

        self.avatar_config_raw = avatar_config 
        self.context = campaign_context
        
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None
            
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.video_dir = os.path.join(self.base_dir, "video")
        os.makedirs(self.video_dir, exist_ok=True)

        self._ffmpeg_available = self._check_ffmpeg()
        self.assets = {"product": [], "logo": [], "lifestyle": []}

    @staticmethod
    def _safe_float(val, default: float = 5.0) -> float:
        """Safely convert a value to float. Handles '5s', '4-6', etc."""
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            import re
            # Strip units like 's', 'sec', 'seconds'
            cleaned = re.sub(r'[^\d.\-]', '', val.split('-')[0].strip())
            try:
                return float(cleaned) if cleaned else default
            except ValueError:
                return default
        return default

    @staticmethod 
    def _check_ffmpeg() -> bool:
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
            subprocess.run(["ffprobe", "-version"], capture_output=True, timeout=5)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print("   [BaseRenderer] WARNING: ffmpeg/ffprobe not found.")
            return False

    async def initialize(self):
        self.assets = await self._load_assets()

    async def _load_assets(self) -> Dict:
        from api.services.db_mongo_service import get_user_assets
        context = self.context if isinstance(self.context, dict) else {}
        campaign_id = context.get("campaign_id") or context.get("_id")
        user_id = context.get("user_id") or context.get("owner_id")
        
        if campaign_id: campaign_id = str(campaign_id)
        if user_id: user_id = str(user_id)
            
        loaded = {"product": [], "logo": [], "lifestyle": []}
        if not user_id: return loaded

        try:
            items = await get_user_assets(user_id)
            for item in items:
                metadata = item.get("metadata", {})
                item_campaign_id = metadata.get("campaign_id")
                
                # Rule: If campaign_id is provided, only use its assets OR assets with NO campaign_id (Global)
                if campaign_id and item_campaign_id and str(item_campaign_id) != str(campaign_id):
                    continue
                
                # Check for 'asset_type' OR 'type'
                a_type = metadata.get("asset_type") or metadata.get("type")
                file_id = str(item["_id"])
                if a_type in loaded:
                    loaded[a_type].append(file_id)
            
            print(f"       ✅ Assets loaded for user {user_id} (Campaign: {campaign_id}): { {k: len(v) for k, v in loaded.items()} }")
        except Exception as e:
            print(f"       ⚠️ Failed to load assets: {e}")

        # Local Fallback
        import glob
        # ONLY fallback to global if campaign_id is NONE or folder doesn't exist AND we have NO assets yet
        assets_base = os.path.join(self.base_dir, "assets", campaign_id if campaign_id else "NONE")
        if not os.path.exists(assets_base):
             # If we already loaded assets from DB for this campaign, DO NOT fallback to global folder 
             # because global folder might contain assets from OTHER campaigns.
             if any(loaded.values()):
                 print(f"       ℹ️ Using DB assets for campaign {campaign_id}, skipping global folder fallback.")
                 return loaded
             assets_base = os.path.join(self.base_dir, "assets")

        image_exts = ("*.png", "*.jpg", "*.jpeg", "*.webp")
        for asset_type in ["product", "logo", "lifestyle"]:
            local_dir = os.path.join(assets_base, asset_type)
            if os.path.exists(local_dir):
                for ext in image_exts:
                    for img_path in glob.glob(os.path.join(local_dir, ext)):
                        if img_path not in loaded[asset_type]:
                            loaded[asset_type].append(img_path)
        return loaded

    async def _load_image_for_veo(self, asset_id: str):
        if os.path.exists(asset_id):
            try:
                import mimetypes
                mime_type, _ = mimetypes.guess_type(asset_id)
                mime_type = mime_type or "image/jpeg"
                with open(asset_id, "rb") as f:
                    return types.Image(image_bytes=f.read(), mime_type=mime_type)
            except Exception: return None

        from api.services.db_mongo_service import get_file_from_gridfs
        try:
            image_bytes, metadata = await get_file_from_gridfs(asset_id)
            mime_type = metadata.get("content_type", "image/jpeg")
            return types.Image(image_bytes=image_bytes, mime_type=mime_type)
        except Exception: return None

    async def _get_reference_images_for_scene(self, scene: Dict) -> List:
        """DEFAULT: Subclasses should override this."""
        return []

    def _get_scene_context(self) -> Dict:
        product_info = self.context.get("product_understanding", {})
        offer_info = self.context.get("offer_and_risk_reversal", {})
        offers = offer_info.get("offers", [])
        discount = offers[0].get("discount", "") if offers else ""
        gender = self.avatar.get("gender") or self.avatar.get("avatar_preferences", {}).get("gender", "young person")
        language = self.avatar.get("voice_preferences", {}).get("language", "Hindi")

        return {
            "product_name": product_info.get("product_name") or self.context.get("product_name", "the product"),
            "brand": product_info.get("brand_name") or self.context.get("brand_name", "the brand"),
            "category": product_info.get("category", "consumer product"),
            "user_problem": self.context.get("user_problem_raw", "a common problem"),
            "language": language,
            "gender": gender,
            "discount": discount,
        }

    def _get_character_description(self) -> str:
        ctx = self._get_scene_context()
        return (
            f"A {ctx['gender']} in their late 20s with natural skin, "
            f"speaking {ctx['language']}, wearing casual attire. Maintain absolute identity consistency."
        )

    def _generate_scene_prompts(self, scene_list: List[Dict]) -> Dict[str, str]:
        """DEFAULT: Subclasses should override this."""
        return {}

    def _build_prompt(self, scene: Dict) -> str:
        # Re-use logic from original renderer but use subclass hooks
        scene_name = scene.get("scene", "")
        copy_text = scene.get("voiceover", "")
        language = self.avatar.get("voice_preferences", {}).get("language", "Hindi")
        shot_type = scene.get("shot_type", "")
        is_avatar_scene = "avatar" in shot_type.lower()
        
        storyboard = []
        variants = self.variants.get("variants", [])
        if variants: storyboard = variants[0].get("storyboard", [])
        
        scene_prompts = self._generate_scene_prompts(storyboard)
        fallback_prompt = scene.get("visual_description", scene.get("scene", "Cinematic product shot"))
        prompt = scene_prompts.get(scene_name, f"{fallback_prompt} for {self._get_scene_context()['brand']}.")

        if is_avatar_scene:
            prompt += f" STABILITY RULES: {self._get_character_description()} Speaking directly to camera."
            if copy_text: prompt += f' The person says: "{copy_text}" in {language}.'
        else:
            prompt += " Focus purely on the product and the environment. NO humans, NO faces, NO people in the frame."
        
        # Add basic movement/style
        env = scene.get("environment", "")
        cam = scene.get("camera_shot", "")
        if env: prompt += f" Environment: {env}."
        if cam: prompt += f" Camera: {cam}."

        global_style = self.variants.get("global_style", "")
        if global_style: prompt += f" STYLE: {global_style}"

        # ── Inject Template Rules ──
        ad_template = self.context.get("ad_template", {})
        if ad_template:
            common_rules = ad_template.get("common_rules", [])
            humanization = ad_template.get("humanization", {})
            if common_rules:
                prompt += f" RULES: {', '.join(common_rules)}."
            if humanization:
                prompt += f" HUMANIZATION: {humanization}."

        prompt += " Shot on Arri Alexa 65, 4k, photorealistic, cinematic lighting."
        return prompt

    def _download_video(self, video_uri: str, output_path: str) -> bool:
        """Downloads the generated video from the URI."""
        try:
            url = video_uri
            url += f"&key={self.api_key}" if '?' in url else f"?key={self.api_key}"
            response = requests.get(url, stream=True, timeout=120)
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192): f.write(chunk)
                return True
            return False
        except Exception: return False

    def _conform_video_duration(self, input_path: str, target_duration: float, output_path: str) -> bool:
        """Trims or stretches a video to match the exact target duration."""
        if not self._ffmpeg_available: return False
        try:
            # We use setpts for video and atempo for audio to avoid sync drift
            # Also ensures 9:16 aspect ratio and 720x1280 scale
            cmd = [
                "ffmpeg", "-y", "-i", input_path,
                "-t", str(target_duration),
                "-vf", "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setpts=PTS-STARTPTS",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                output_path
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return os.path.exists(output_path)
        except Exception: return False

    async def generate_scene_video(self, scene: Dict, output_path: str) -> bool:
        if not self.client: return False
        
        target_duration = self._safe_float(scene.get("duration", 5))
        prompt = self._build_prompt(scene)
        reference_images = await self._get_reference_images_for_scene(scene)
        
        temp_raw = output_path.replace(".mp4", "_raw.mp4")
        try:
            # Veo 3.1 only supports duration_seconds of 4, 6, or 8.
            # Snap to the nearest supported value to avoid API rejection.
            VEO_SUPPORTED_DURATIONS = [4, 6, 8]
            duration = int(target_duration)
            duration = min(VEO_SUPPORTED_DURATIONS, key=lambda x: abs(x - duration))

            config = types.GenerateVideosConfig(
                number_of_videos=1,
                duration_seconds=duration,
                aspect_ratio="9:16"
                # reference_images=None # veo-2.0-generate-001 does not currently support reference_images
            )
            operation = self.client.models.generate_videos(model=self.DEFAULT_MODEL, prompt=prompt, config=config)
            while not operation.done:
                await asyncio.sleep(self.POLL_INTERVAL)
                operation = self.client.operations.get(operation)
            if operation.error: return False
            result = operation.result
            if result and result.generated_videos:
                if self._download_video(result.generated_videos[0].video.uri, temp_raw):
                    # CONFORM to strict timing
                    success = self._conform_video_duration(temp_raw, target_duration, output_path)
                    if os.path.exists(temp_raw): os.remove(temp_raw)
                    render_log(f"       ✅ Veo Video Generated | Output: {success}")
                    return success
            render_log(f"       ❌ Veo API Request Failed or Returned No Video")
            return False
        except Exception as e: 
            render_log(f"       ❌ Veo Generation Exception: {e}")
            return False

    def merge_videos(self, video_paths: List[str], final_output_path: str):
        """Merges multiple video files using FFmpeg with smooth cross-fade transitions.
        Strictly maintains scene durations from the storyboard."""
        import shutil
        print(f"   Merging {len(video_paths)} scenes into {final_output_path}...")

        if len(video_paths) == 1:
            shutil.copy2(video_paths[0], final_output_path)
            return

        if not self._ffmpeg_available:
            shutil.copy2(video_paths[0], final_output_path)
            return

        FADE_DURATION = 0.5  # overlap duration in seconds

        try:
            # 1. Probe durations for all scenes
            durations = []
            for vp in video_paths:
                probe_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", vp]
                res = subprocess.run(probe_cmd, capture_output=True, text=True)
                durations.append(self._safe_float(res.stdout.strip(), 5.0))

            # 2. Build xfade filter chain
            # Filter chain: [v0][v1]xfade...[v12]; [v12][v2]xfade...[outv]
            inputs = []
            for vp in video_paths: inputs += ["-i", vp]
            
            n = len(video_paths)
            video_filters = []
            
            offsets = []
            cumulative = 0
            for i in range(n - 1):
                cumulative += durations[i] - FADE_DURATION
                offsets.append(cumulative)

            # Build the chain
            if n == 2:
                video_filters.append(f"[0:v][1:v]xfade=transition=fade:duration={FADE_DURATION}:offset={offsets[0]}[v_out]")
            else:
                video_filters.append(f"[0:v][1:v]xfade=transition=fade:duration={FADE_DURATION}:offset={offsets[0]}[v1]")
                for i in range(2, n - 1):
                    video_filters.append(f"[v{i-1}][{i}:v]xfade=transition=fade:duration={FADE_DURATION}:offset={offsets[i-1]}[v{i}]")
                video_filters.append(f"[v{n-2}][{n-1}:v]xfade=transition=fade:duration={FADE_DURATION}:offset={offsets[n-2]}[v_out]")

            filter_complex = ";".join(video_filters)
            
            # Post-processing: Subtle film grain and contrast for extra "Premium" feel
            filter_complex += ";[v_out]eq=contrast=1.05:saturation=1.05,noise=alls=1:allf=t+u[final_v]"

            cmd = ["ffmpeg", "-y"] + inputs + [
                "-filter_complex", filter_complex,
                "-map", "[final_v]",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "slow",
                final_output_path
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            render_log("     ✅ Merged all scenes with Cinematic Cross-fade successfully.")
            return
        except Exception as e:
            render_log(f"     ⚠️ Cross-fade failed: {e}. Falling back to simple merge.")
            # Fallback simple concat
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                for path in video_paths:
                    safe_path = path.replace("'", "'\\''")
                    f.write(f"file '{safe_path}'\n")
                concat_file = f.name
            try:
                subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file, "-c", "copy", final_output_path], check=True)
            finally:
                if os.path.exists(concat_file): os.remove(concat_file)

    async def _generate_fallback_image_video(self, scene: Dict, idx: int, temp_dir: str) -> str:
        """Generates a static image via Imagen and animates it."""
        if not self._ffmpeg_available: return None
        from api.services.db_mongo_service import get_file_from_gridfs
        from api.services.ai_assist_service import ai_assist_service

        prompt = self._build_prompt(scene)
        try:
            grid_file_id = await ai_assist_service.generate_fallback_image(prompt)
            if not grid_file_id: return None
            img_data, _ = await get_file_from_gridfs(grid_file_id)
            img_temp = os.path.join(temp_dir, f"fallback_{idx}.jpg")
            with open(img_temp, "wb") as f: f.write(img_data)
            out_video = os.path.join(temp_dir, f"scene_fallback_{idx}.mp4")
            cmd = [
                "ffmpeg", "-y", "-loop", "1", "-i", img_temp,
                "-vf", "zoompan=z='zoom+0.0005':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=125:s=720x1280",
                "-c:v", "libx264", "-t", "5", "-pix_fmt", "yuv420p", out_video
            ]
            subprocess.run(cmd, capture_output=True)
            return out_video if os.path.exists(out_video) else None
        except Exception: return None

    async def _apply_audio_and_overlay(self, idx: int, scene: Dict, video_path: str, temp_dir: str) -> str:
        """Applies overlays (logo, product, text) on the video."""
        if not self._ffmpeg_available: return video_path
        from api.services.db_mongo_service import get_file_from_gridfs
        
        output_path = video_path
        try:
            logo_ids = self.assets.get("logo", [])
            product_ids = self.assets.get("product", [])
            scene_name = scene.get("scene", "")
            
            print(f"       [Overlay] Scene {idx} ({scene_name}): Found {len(logo_ids)} logos, {len(product_ids)} products")

            overlay_inputs = []
            filter_complex = ""
            current_v = "[0:v]"
            input_idx = 1
            
            if logo_ids:
                img_bytes, _ = await get_file_from_gridfs(logo_ids[0])
                if img_bytes:
                    logo_p = os.path.join(temp_dir, f"l_{idx}.png")
                    with open(logo_p, "wb") as f: f.write(img_bytes)
                    overlay_inputs += ["-i", logo_p]
                    # Logo in top-right
                    prefix = ";" if filter_complex else ""
                    filter_complex += f"{prefix}[{input_idx}:v]scale=150:-1[logo];{current_v}[logo]overlay=W-w-20:20[v_l]"
                    current_v = "[v_l]"
                    input_idx += 1

            relevant_scenes = ["solution", "proof", "cta", "product", "result", "feature", "reveal", "benefit"]
            if any(s.lower() in scene_name.lower() for s in relevant_scenes) and product_ids:
                img_data, _ = await get_file_from_gridfs(product_ids[0])
                if img_data:
                    prod_p = os.path.join(temp_dir, f"p_{idx}.png")
                    with open(prod_p, "wb") as f: f.write(img_data)
                    overlay_inputs += ["-i", prod_p]
                    # Product boldly centered
                    prefix = ";" if filter_complex else ""
                    filter_complex += f"{prefix}[{input_idx}:v]scale=500:-1[prod];{current_v}[prod]overlay=(W-w)/2:(H-h)/2[v_p]"
                    current_v = "[v_p]"
                    input_idx += 1
            
            text_overlay = scene.get("text_overlay", scene.get("overlay_text", ""))
            if text_overlay:
                # Robust Windows font path for FFmpeg
                font_path = "C\\:/Windows/Fonts/arialbd.ttf"
                
                # CRITICAL: Escape single quotes for FFmpeg filter string!
                # FFmpeg filters use ' as a delimiter, so we must replace ' with '\'' (escaped)
                safe_text = str(text_overlay).replace("'", "'\\''")
                
                prefix = ";" if filter_complex else ""
                filter_complex += f"{prefix}{current_v}drawtext=text='{safe_text}':fontfile='{font_path}':fontsize=48:fontcolor=white:shadowcolor=black@0.6:shadowx=3:shadowy=3:x=(w-text_w)/2:y=H/4[v_out]"
                current_v = "[v_out]"
            
            if filter_complex:
                branded_out = os.path.join(temp_dir, f"branded_{idx}.mp4")
                cmd = ["ffmpeg", "-y", "-i", video_path] + overlay_inputs + ["-filter_complex", filter_complex, "-map", current_v, "-c:v", "libx264", "-pix_fmt", "yuv420p", branded_out]
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode == 0 and os.path.exists(branded_out):
                    output_path = branded_out
                else:
                    print(f"       ⚠️ Overlay failed for scene {idx}: {res.stderr[:200]}")

            return output_path
        except Exception as e:
            print(f"       ⚠️ Overlay exception for scene {idx}: {e}")
            return video_path

    async def render_variant(self, variant: Dict) -> Dict:
        """Full orchestrator with retries and audio pipeline."""
        variant_label = variant.get("variant", "?")
        storyboard = variant.get("storyboard") or variant.get("scenes") or []
        temp_dir = tempfile.mkdtemp()
        scene_videos = [None] * len(storyboard)
        
        async def process(idx, s):
            p = os.path.join(temp_dir, f"s_{idx}.mp4")
            if await self.generate_scene_video(s, p):
                return idx, await self._apply_audio_and_overlay(idx, s, p, temp_dir)
            return idx, None

        render_log(f"   🎬 Rendering Variant {variant_label} with {len(storyboard)} scenes...")
        tasks = [process(i, s) for i, s in enumerate(storyboard)]
        results = await asyncio.gather(*tasks)
        for idx, path in results: scene_videos[idx] = path
        
        # Simple Retry
        for idx, path in enumerate(scene_videos):
            if path is None:
                render_log(f"       ⚠️ Scene {idx} failed. Attempting Retry...")
                p = os.path.join(temp_dir, f"s_{idx}_retry.mp4")
                if await self.generate_scene_video(storyboard[idx], p):
                    scene_videos[idx] = await self._apply_audio_and_overlay(idx, storyboard[idx], p, temp_dir)
                else:
                    render_log(f"       🚨 Retry failed! Falling back to static image animation for scene {idx}.")
                    scene_videos[idx] = await self._generate_fallback_image_video(storyboard[idx], idx, temp_dir)

        valid = [v for v in scene_videos if v]
        if len(valid) < len(storyboard):
            render_log(f"   ⚠️ Warning: Some scenes completely failed. {len(valid)}/{len(storyboard)} valid.")

        if not valid: 
            render_log(f"   ❌ Critical Failure: All scenes invalid.")
            return {"variant": variant_label, "status": "failed"}

        video_id = f"{variant_label}_{int(time.time())}"
        final_path = os.path.join(self.video_dir, f"ad_{video_id}.mp4")
        
        render_log(f"   🎞️ Starting Final Merge Process...")
        self.merge_videos(valid, final_path)

        # ── Audio Pipeline ──
        try:
            audio_planning = self.context.get("audio_planning", {})
            if not audio_planning:
                print("   ⚠️ AUDIO SKIPPED: No audio_planning found in context. Check creative agent output.")
            elif not self._ffmpeg_available:
                print("   ⚠️ AUDIO SKIPPED: FFmpeg not available on this system.")
            if audio_planning and os.path.exists(final_path) and self._ffmpeg_available:
                print(f"   🔊 Applying audio pipeline for {variant_label}...")
                
                # Compute ACTUAL video duration via ffprobe
                probe_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", final_path]
                dur_res = subprocess.run(probe_cmd, capture_output=True, text=True)
                actual_duration = self._safe_float(dur_res.stdout.strip(), 25.0)
                print(f"   📏 Actual video duration: {actual_duration}s")
                
                full_text = " ".join([s.get("voiceover", "") for s in storyboard])
                voiceover_path = None
                if full_text.strip():
                    try:
                        from agents.production.audio_service import audio_service
                        voiceover_path = audio_service.generate_voiceover(full_text, self._get_scene_context()['language'])
                        print(f"   🎙️ Voiceover: {'Generated' if voiceover_path else 'Failed'}")
                    except Exception as vo_err:
                        print(f"   ⚠️ Voiceover failed (non-fatal): {vo_err}")
                
                from agents.production.audio_mixer import AudioMixer
                mixer = AudioMixer(audio_planning, actual_duration)
                mixed_audio = mixer.mix_final_audio(voiceover_path=voiceover_path)
                
                if mixed_audio and os.path.exists(mixed_audio):
                    final_audio_path = final_path.replace(".mp4", "_AUDIO.mp4")
                    # Map 0:v (video from silent movie) and 1:a (audio from mix)
                    cmd = ["ffmpeg", "-y", "-i", final_path, "-i", mixed_audio, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-map", "0:v:0", "-map", "1:a:0", "-shortest", final_audio_path]
                    print(f"   🔊 Merging audio into video...")
                    res = subprocess.run(cmd, capture_output=True, text=True)
                    if res.returncode == 0 and os.path.exists(final_audio_path):
                        final_path = final_audio_path
                        print(f"   ✅ Audio merged successfully!")
                    else:
                        print(f"   ⚠️ Final audio merge failed (rc={res.returncode}): {res.stderr[:300] if res.stderr else 'unknown'}")
                else:
                    print(f"   ⚠️ AudioMixer returned no usable audio (mixed_audio={mixed_audio})")
        except Exception as e:
            import traceback
            print(f"   ⚠️ Audio pipeline error: {e}")
            traceback.print_exc()

        return {
            "variant": variant_label,
            "status": "completed",
            "local_path": final_path,
            "video_id": video_id
        }

    async def generate_output(self, wait_for_render=True) -> Dict:
        variant_list = self.variants.get("variants", [])
        render_results = []
        for variant in variant_list:
            render_results.append(await self.render_variant(variant))
        return {"campaign_id": self.context.get("campaign_id"), "render_results": render_results}
