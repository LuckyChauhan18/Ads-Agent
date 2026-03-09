"""Main GeminiRenderer class — composes all mixins.

This is the primary entry point for Step 7: Video Rendering.
"""
import asyncio
import os
import sys
import time
import tempfile
from typing import Dict, List

from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load .env from root directory
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '..', '.env')
load_dotenv(dotenv_path)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from utils.logger import logger

from .asset_loader import AssetLoaderMixin
from .prompt_builder import PromptBuilderMixin
from .video_merger import VideoMergerMixin
from .overlay import OverlayMixin


class GeminiRenderer(AssetLoaderMixin, PromptBuilderMixin, VideoMergerMixin, OverlayMixin):
    """STEP 7: Renders video ads using Google Gemini (Veo 3.1) API.
    
    Generates videos scene-by-scene in parallel with product/logo assets
    as Veo reference images. Merges scenes via FFmpeg.
    
    Composed from 4 mixins:
    - AssetLoaderMixin:   GridFS asset loading, Veo reference images
    - PromptBuilderMixin: LLM scene prompts, per-scene Veo prompts
    - VideoMergerMixin:   FFmpeg normalize, merge, download
    - OverlayMixin:       Branding overlays, fallback image videos
    """
    
    DEFAULT_MODEL = "veo-3.1-generate-preview"
    MAX_POLL_TIME = 600
    POLL_INTERVAL = 30
    MAX_CONCURRENT_SCENES = 3
    TARGET_WIDTH = 720
    TARGET_HEIGHT = 1280
    TARGET_FPS = 30
    
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
        self.video_dir = os.path.join(os.path.dirname(self.base_dir), "extra", "video")
        os.makedirs(self.video_dir, exist_ok=True)
        
        self.assets = {"product": [], "logo": [], "lifestyle": []}
        self._global_context = None

    def _get_avatar_for_scene(self, scene: Dict) -> dict:
        """Returns the avatar assigned to this scene.
        
        Avatars are pre-assigned sequentially in render_variant() based on
        the order the user selected them. Falls back to self.avatar.
        """
        return scene.get("_assigned_avatar") or self.avatar

    def _assign_avatars_to_scenes(self, storyboard: List[Dict]):
        """Distributes user-selected avatars evenly across scenes in sequence order.
        
        Example: 3 avatars + 6 scenes →
          Scene 0,1 → Avatar A  |  Scene 2,3 → Avatar B  |  Scene 4,5 → Avatar C
        """
        if not self.avatar_list:
            return
        
        n_avatars = len(self.avatar_list)
        n_scenes = len(storyboard)
        
        for i, scene in enumerate(storyboard):
            avatar_idx = (i * n_avatars) // n_scenes
            avatar_idx = min(avatar_idx, n_avatars - 1)
            scene["_assigned_avatar"] = self.avatar_list[avatar_idx]
            avatar_name = self.avatar_list[avatar_idx].get("name", self.avatar_list[avatar_idx].get("style", f"Avatar {avatar_idx+1}"))
            logger.info(f"     Scene {i+1} ({scene.get('scene')}) → {avatar_name}")

    def _build_global_context(self) -> dict:
        """Builds a frozen Global Visual Context for all scenes."""
        if self._global_context:
            return self._global_context
        
        product_info = self.context.get("product_understanding", {})
        category = product_info.get("category", "consumer product")
        brand_voice = self.context.get("brand_voice", "premium and modern")
        
        self._global_context = {
            "category": category,
            "brand_voice": brand_voice,
            "location": f"A visually stunning location relevant to {category}",
            "lighting": "Cinematic golden hour lighting",
            "camera_style": "Handheld cinematic, 9:16 vertical",
            "color_palette": "Warm, premium tones",
            "consistency_prompt": (
                "ABSOLUTE VISUAL IDENTITY RULES (DO NOT DEVIATE): "
                "1. The actor MUST be visually IDENTICAL to the provided reference image "
                "(same face, same hair, same clothes, same body type) in EVERY scene. "
                "2. The location and environment MUST remain the SAME as the previous scene. "
                "If the first scene is in a park, ALL scenes are in that SAME park. "
                "3. Lighting, color grading, and camera style MUST stay consistent throughout. "
                "4. Do NOT introduce ANY new characters not shown in the reference image. "
                "5. The actor's wardrobe, accessories, and hairstyle MUST NOT change between scenes."
            )
        }
        logger.info(f"   🔒 Global context locked: {category}, {brand_voice}")
        return self._global_context

    async def initialize(self):
        """Asynchronous initialization: loads assets and builds global context."""
        self.assets = await self._load_assets()
        self._build_global_context()

    async def generate_scene_video(self, scene: Dict, output_path: str) -> bool:
        """Generates a single scene video using Gemini Veo 3.1 with asset references.
        
        Uses the scene's own duration (from Scene Planner) instead of hardcoded 8s.
        """
        if not self.client:
            logger.error("   Gemini API client not initialized. Missing API key.")
            return False
            
        prompt = self._build_prompt(scene)
        reference_images = await self._get_reference_images_for_scene(scene)
        
        scene_name = scene.get("scene", "?")
        
        duration_str = scene.get("duration", "5s")
        duration_sec = 5
        try:
            duration_sec = int(duration_str.replace("s", "").replace("sec", "").strip())
        except:
            pass
        
        logger.info(f"     🎬 Scene '{scene_name}' ({duration_sec}s) with {len(reference_images)} ref(s)...")
        
        try:
            config_args = {
                "number_of_videos": 1,
                "duration_seconds": duration_sec
            }
            if reference_images:
                config_args["reference_images"] = reference_images
                
            config = types.GenerateVideosConfig(**config_args)
            
            operation = self.client.models.generate_videos(
                model=self.DEFAULT_MODEL,
                prompt=prompt,
                config=config,
            )
            
            logger.info(f"       Operation started: {operation.name}")
            
            start_time = time.time()
            while not operation.done:
                elapsed = int(time.time() - start_time)
                if elapsed > self.MAX_POLL_TIME:
                    logger.error(f"       TIMEOUT after {elapsed}s for scene '{scene_name}'")
                    return False
                
                logger.info(f"       ⏳ Waiting for '{scene_name}'... ({elapsed}s)")
                await asyncio.sleep(self.POLL_INTERVAL)
                operation = self.client.operations.get(operation)
            
            if operation.error:
                logger.error(f"       Veo error for '{scene_name}': {operation.error}")
                return False
            
            result = operation.result
            if result and result.generated_videos:
                gen_video = result.generated_videos[0]
                video_uri = gen_video.video.uri
                logger.info(f"       ✅ Video URI: {video_uri}")
                return self._download_video(video_uri, output_path)
            else:
                logger.warning(f"       No video generated for scene '{scene_name}'.")
                return False
                
        except Exception as e:
            logger.error(f"     Gemini API Error for '{scene_name}': {e}")
            return False

    async def render_variant(self, variant: Dict) -> Dict:
        """Renders all scenes for a variant in parallel, retries failures, then merges."""
        variant_label = variant.get("variant", "?")
        storyboard = variant.get("storyboard") or variant.get("scenes") or []
        logger.info(f"\n   🎬 Processing Variant {variant_label}: {variant.get('label', '')}")
        
        # Tag each scene with variant_id for per-variant prompt cache
        for s in storyboard:
            s["_variant_id"] = variant_label
        
        self._assign_avatars_to_scenes(storyboard)
        
        for i, s in enumerate(storyboard):
            assigned = s.get("_assigned_avatar", {})
            av_name = assigned.get("name", assigned.get("style", "default"))
            logger.info(f"     Scene {i+1}: {s.get('scene')} ({s.get('duration', '?')}) → {av_name}")
        
        scene_videos = [None] * len(storyboard)
        temp_dir = tempfile.mkdtemp()
        
        if not storyboard:
            logger.error("     Empty storyboard. Cannot render.")
            return {
                "variant": variant_label,
                "label": variant.get("label"),
                "status": "failed",
                "error": "Empty storyboard"
            }

        sem = asyncio.Semaphore(self.MAX_CONCURRENT_SCENES)

        async def process_scene(idx, scene):
            async with sem:
                scene_path = os.path.join(temp_dir, f"scene_{idx}.mp4")
                if await self.generate_scene_video(scene, scene_path):
                    final_scene_path = await self._apply_audio_and_overlay(idx, scene, scene_path, temp_dir)
                    return idx, final_scene_path
                return idx, None

        logger.info(f"     ⚡ Parallelizing {len(storyboard)} scenes (max {self.MAX_CONCURRENT_SCENES} concurrent)...")
        tasks = [process_scene(i, scene) for i, scene in enumerate(storyboard)]
        results = await asyncio.gather(*tasks)
        
        for idx, path in results:
            if path:
                scene_videos[idx] = path
            else:
                logger.warning(f"     Scene {idx} ({storyboard[idx].get('scene')}) generation failed.")
        
        # --- Retry failed scenes ---
        failed_indices = [i for i, v in enumerate(scene_videos) if v is None]
        if failed_indices:
            logger.info(f"     🔄 Retrying {len(failed_indices)} failed scene(s)...")
            for attempt in range(1, 3):
                still_failed = [i for i in failed_indices if scene_videos[i] is None]
                if not still_failed: break
                for idx in still_failed:
                    scene = storyboard[idx]
                    scene_path = os.path.join(temp_dir, f"scene_{idx}_retry_{attempt}.mp4")
                    if await self.generate_scene_video(scene, scene_path):
                        final_scene_path = await self._apply_audio_and_overlay(idx, scene, scene_path, temp_dir)
                        scene_videos[idx] = final_scene_path

            # --- Final Fallback: Static Image Animation ---
            still_failed = [i for i in failed_indices if scene_videos[i] is None]
            if still_failed:
                logger.warning(f"     ⚠️ {len(still_failed)} scenes failed Veo. Using static fallback...")
                for idx in still_failed:
                    scene = storyboard[idx]
                    fallback_path = await self._generate_fallback_image_video(scene, idx, temp_dir)
                    if fallback_path:
                        final_scene_path = await self._apply_audio_and_overlay(idx, scene, fallback_path, temp_dir)
                        scene_videos[idx] = final_scene_path
        
        # --- Final Merge ---
        valid_scene_videos = [v for v in scene_videos if v is not None]
        if not valid_scene_videos:
             return {"variant": variant_label, "status": "failed", "error": "All scenes failed"}

        video_id = f"gemini_{variant_label}_{int(time.time())}"
        final_path = os.path.join(self.video_dir, f"ad_variant_{variant_label}_{video_id}.mp4")
        
        self.merge_videos(valid_scene_videos, final_path)
        
        return {
            "variant": variant_label,
            "label": variant.get("label"),
            "video_id": video_id,
            "status": "completed",
            "local_path": final_path,
            "scenes_count": len(valid_scene_videos)
        }

    async def generate_output(self, wait_for_render=True) -> Dict:
        """Main entry point for Step 7."""
        if not self.api_key:
            logger.warning("   GEMINI_API_KEY not found. Running dry run...")
            return self._generate_dry_run_output()
            
        variant_list = self.variants.get("variants", [])
        render_results = []
        
        for variant in variant_list:
            result = await self.render_variant(variant)
            render_results.append(result)
            
        return {
            "campaign_id": self.context.get("campaign_id", "unknown"),
            "renderer": "gemini",
            "model_used": self.DEFAULT_MODEL,
            "total_variants_rendered": len(render_results),
            "render_results": render_results
        }

    def _generate_dry_run_output(self) -> Dict:
        return {
            "campaign_id": self.context.get("campaign_id", "unknown"),
            "renderer": "gemini",
            "mode": "dry_run",
            "reason": "GEMINI_API_KEY not found",
            "render_results": []
        }
