import asyncio
import json
import os
import time
import subprocess
import tempfile
import requests
import concurrent.futures
from typing import Dict, List
from google import genai
from google.genai import types
from PIL import Image
from dotenv import load_dotenv

# Load .env from root directory (parent of src)
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)

class GeminiRenderer:
    """STEP 7: Renders video ads using Google Gemini (Veo 3.1) API.
    
    Generates videos scene-by-scene in parallel with product/logo assets
    as Veo reference images. Merges scenes via FFmpeg.
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
            # Handle cases where avatar_config might be nested or have plural selection
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

        self.avatar_config_raw = avatar_config # Keep raw for reference
        self.context = campaign_context
        
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None
            
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.video_dir = os.path.join(self.base_dir, "video")
        os.makedirs(self.video_dir, exist_ok=True)

        # Check if ffmpeg/ffprobe are available
        self._ffmpeg_available = self._check_ffmpeg()

        # Assets will be loaded during initialize()
        self.assets = {"product": [], "logo": [], "lifestyle": []}

    @staticmethod
    def _check_ffmpeg() -> bool:
        """Check if ffmpeg and ffprobe are available on PATH."""
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
            subprocess.run(["ffprobe", "-version"], capture_output=True, timeout=5)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print("   [GeminiRenderer] WARNING: ffmpeg/ffprobe not found. Video merging and overlays will use fallback mode.")
            return False

    async def initialize(self):
        """Asynchronous initialization: loads assets from Redis/GridFS."""
        self.assets = await self._load_assets()

    async def _load_assets(self) -> Dict:
        """Loads ONLY this campaign's product images and logo from GridFS.

        Strict filtering: assets MUST match campaign_id. Never loads
        assets from other campaigns to prevent random product images.
        """
        from api.services.db_mongo_service import get_user_assets

        context = self.context if isinstance(self.context, dict) else {}
        campaign_id = context.get("campaign_id") or context.get("_id")
        user_id = context.get("user_id") or context.get("owner_id")

        if campaign_id: campaign_id = str(campaign_id)
        if user_id: user_id = str(user_id)

        print(f"   [GeminiRenderer] Loading assets for campaign: {campaign_id}, user: {user_id}")

        loaded = {"product": [], "logo": [], "lifestyle": []}

        if not user_id:
            print("   [GeminiRenderer] No user_id found in context. Cannot load assets.")
            return loaded

        if not campaign_id:
            print("   [GeminiRenderer] WARNING: No campaign_id — skipping asset load to avoid random images.")
            return loaded

        try:
            items = await get_user_assets(user_id)
            for item in items:
                metadata = item.get("metadata", {})
                item_campaign_id = metadata.get("campaign_id")

                # STRICT: only load assets that belong to THIS campaign
                if not item_campaign_id or str(item_campaign_id) != campaign_id:
                    continue

                asset_type = metadata.get("asset_type")
                file_id = str(item["_id"])
                if asset_type in loaded:
                    loaded[asset_type].append(file_id)
                    print(f"       Loaded {asset_type} asset: {file_id} (campaign: {item_campaign_id})")
        except Exception as e:
            print(f"       Failed to load assets from GridFS: {e}")

        print(f"   Assets loaded: {len(loaded['product'])} product, {len(loaded['logo'])} logo (campaign: {campaign_id})")
        return loaded

    async def _load_image_for_veo(self, asset_id: str):
        """Loads an image from GridFS and returns a types.Image."""
        from api.services.db_mongo_service import get_file_from_gridfs
        try:
            image_bytes, metadata = await get_file_from_gridfs(asset_id)
            mime_type = metadata.get("content_type", "image/jpeg")
            return types.Image(image_bytes=image_bytes, mime_type=mime_type)
        except Exception as e:
            print(f"       Failed to load GridFS image {asset_id}: {e}")
            return None

    async def _get_reference_images_for_scene(self, scene: Dict) -> List:
        """Returns Veo reference images — ONLY from user-uploaded campaign assets.

        Uses uploaded product images and logo only. No avatar URLs, no external
        sources. Strictly limited to what the user uploaded for this campaign.
        """
        scene_name = scene.get("scene", "")
        references = []

        product_ids = self.assets.get("product", [])
        logo_ids = self.assets.get("logo", [])

        # Hook/Problem scenes: NO product references (build curiosity first)
        if scene_name in ("Hook", "Problem", "Relatable Moment", "Stop scroll", "Agitate pain"):
            return []

        # Solution/Proof: Show the product (the reveal)
        elif scene_name in ("Solution", "Proof", "Introduce product", "Show results"):
            for pid in product_ids[:2]:
                img = await self._load_image_for_veo(pid)
                if img:
                    references.append(types.VideoGenerationReferenceImage(
                        image=img, reference_type="ASSET"
                    ))
                    print(f"       Using product image {pid} for scene '{scene_name}'")

        # Trust/CTA: Logo + product
        elif scene_name in ("CTA", "Trust", "Drive action", "Build credibility"):
            for lid in logo_ids[:1]:
                img = await self._load_image_for_veo(lid)
                if img:
                    references.append(types.VideoGenerationReferenceImage(
                        image=img, reference_type="ASSET"
                    ))
                    print(f"       Using logo {lid} for scene '{scene_name}'")
            for pid in product_ids[:1]:
                img = await self._load_image_for_veo(pid)
                if img:
                    references.append(types.VideoGenerationReferenceImage(
                        image=img, reference_type="ASSET"
                    ))
                    print(f"       Using product image {pid} for scene '{scene_name}'")

        else:
            # Default: use first product image if available
            if product_ids:
                img = await self._load_image_for_veo(product_ids[0])
                if img:
                    references.append(types.VideoGenerationReferenceImage(
                        image=img, reference_type="ASSET"
                    ))

        return references[:2]

    def _get_scene_context(self) -> Dict:
        """Extracts all product/brand/avatar context for prompt generation."""
        product_info = self.context.get("product_understanding", {})
        offer_info = self.context.get("offer_and_risk_reversal", {})
        offers = offer_info.get("offers", [])
        discount = offers[0].get("discount", "") if offers else ""
        guarantee = offers[0].get("guarantee", "") if offers else ""

        gender = self.avatar.get("gender") or self.avatar.get("avatar_preferences", {}).get("gender", "")
        if not gender or str(gender).lower() in ("unknown", "auto"):
            gender = "young Indian woman"

        language = self.avatar.get("voice_preferences", {}).get("language", "Hindi")

        return {
            "product_name": product_info.get("product_name") or self.context.get("product_name", "the product"),
            "brand": product_info.get("brand_name") or self.context.get("brand_name", "the brand"),
            "category": product_info.get("category", "consumer product"),
            "features": product_info.get("features", []),
            "description": product_info.get("description", ""),
            "user_problem": self.context.get("user_problem_raw", "a common problem"),
            "brand_voice": self.context.get("brand_voice", "premium"),
            "language": language,
            "gender": gender,
            "discount": discount,
            "guarantee": guarantee,
        }

    def _generate_scene_prompts(self, scene_list: List[Dict]) -> Dict[str, str]:
        """Uses Gemini Flash to generate hyper-specific photorealistic Veo prompts.

        Focus: short, visually precise descriptions with real camera/lighting
        language that Veo understands. Avoids abstract instructions.
        """
        if hasattr(self, '_cached_scene_prompts'):
            return self._cached_scene_prompts

        ctx = self._get_scene_context()
        continuity_hints = "\n".join([
            f"- {s.get('scene')}: {s.get('visual_continuity', 'Maintain consistency')}"
            for s in scene_list
        ])

        prompt = f"""You are a cinematographer writing SHORT video prompts for Google Veo 3.1 AI video generator.

PRODUCT: {ctx['product_name']} by {ctx['brand']} ({ctx['category']})
FEATURES: {', '.join(ctx['features'][:4]) if ctx['features'] else 'premium quality'}
PROBLEM IT SOLVES: {ctx['user_problem']}
PRESENTER: {ctx['gender']}, speaking in {ctx['language']}

SCENE CONTINUITY:
{continuity_hints}

=== CRITICAL RULES ===
1. Each prompt: 2-3 sentences ONLY. Keep it simple.
2. EVERY scene MUST have PHYSICAL MOVEMENT: walking, turning, picking up, gesturing with hands, leaning forward, stepping toward camera, pointing, demonstrating.
3. Include ONE camera movement per scene: slow dolly in, tracking shot, pan, crane up, steadicam follow, push-in.
4. Describe SPECIFIC setting: "sunlit kitchen with marble countertop" not "a room".
5. Describe what the person DOES with their body, not just facial expressions.
6. The person speaks directly to camera in {ctx['language']}.
7. NEVER write a static scene. The person must be DOING something physical in every frame.

Write prompts for these scenes:

HOOK: Presenter walks into frame in a {ctx['category']}-related location, makes eye contact with camera, and starts speaking about {ctx['user_problem']} with hand gestures. Slow dolly in.

PROBLEM: Same presenter picks up / examines a bad alternative, shakes head in frustration, turns to camera and speaks emotionally. Handheld close-up.

SOLUTION: Presenter reaches for {ctx['product_name']}, holds it up excitedly, turns it to show different angles. Steps closer to camera while speaking. Tracking shot.

TRUST: Presenter walks through a clean modern space, gestures confidently while speaking about {ctx['brand']}. Steadicam follow shot.

PROOF: Presenter actively uses/demonstrates {ctx['product_name']}. Show hands interacting with the product. Smooth tracking shot.

CTA: Presenter steps forward to camera holding {ctx['product_name']}, speaks with urgency and energy. {"Says: " + ctx['discount'] + ". " if ctx['discount'] else ""}Dramatic push-in shot.

RELATABLE MOMENT: Presenter in a candid everyday moment related to {ctx['category']}, doing a real activity. Natural handheld documentary style.

Return ONLY valid JSON:
{{
  "Hook": "prompt...",
  "Problem": "prompt...",
  "Solution": "prompt...",
  "Trust": "prompt...",
  "Proof": "prompt...",
  "CTA": "prompt...",
  "Relatable Moment": "prompt..."
}}"""

        try:
            if self.client:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config={'response_mime_type': 'application/json'}
                )
                self._cached_scene_prompts = json.loads(response.text)
                print(f"     Generated {len(self._cached_scene_prompts)} photorealistic scene prompts via Gemini")
                return self._cached_scene_prompts
        except Exception as e:
            print(f"     LLM scene prompt generation failed: {e}. Using fallback.")

        # Fallback: motion-rich photorealistic prompts
        ctx = self._get_scene_context()
        self._cached_scene_prompts = {
            "Hook": f"A {ctx['gender']} walks into a sunlit {ctx['category']}-related space, stops and turns to camera with a concerned look, gestures with hands while speaking in {ctx['language']} about {ctx['user_problem']}. Slow dolly-in, 50mm lens, warm natural light.",
            "Problem": f"Close-up of the same {ctx['gender']} picking up and examining a bad alternative, shaking head in frustration. They turn to camera and speak emotionally in {ctx['language']} about {ctx['user_problem']}. Handheld camera with subtle push-in.",
            "Solution": f"The same {ctx['gender']} reaches for {ctx['product_name']}, picks it up with both hands and holds it toward camera with genuine excitement. They turn the product to show different angles while speaking in {ctx['language']}. Smooth tracking shot, bright soft lighting.",
            "Trust": f"The same {ctx['gender']} walks through a clean modern space with white walls, gesturing confidently while speaking in {ctx['language']} about {ctx['brand']}. Steadicam follow shot, soft overhead lighting, 35mm lens.",
            "Proof": f"The same {ctx['gender']} actively demonstrates {ctx['product_name']} — hands interacting with the product in a real setting. Smooth tracking shot following the action, natural daylight. Speaking in {ctx['language']} about the results with a genuine smile.",
            "CTA": f"The same {ctx['gender']} steps forward toward the camera holding {ctx['product_name']}, speaks with urgency and energy in {ctx['language']}. {'Says: ' + ctx['discount'] + '.' if ctx['discount'] else ''} Dramatic push-in shot, bright punchy lighting.",
            "Relatable Moment": f"A {ctx['gender']} in an everyday {ctx['category']}-related moment — doing a real physical activity. Natural handheld documentary style, 35mm lens, available light. No product visible."
        }
        return self._cached_scene_prompts

    def _build_prompt(self, scene: Dict) -> str:
        """Builds a photorealistic Veo prompt with dialogue and cinematic quality cues."""
        scene_name = scene.get("scene", "")
        directives = scene.get("realistic_directives", "")
        copy_text = scene.get("voiceover", "")
        language = self.avatar.get("voice_preferences", {}).get("language", "Hindi")

        # Get dynamically generated scene prompts
        storyboard = []
        variants = self.variants.get("variants", [])
        if variants:
            storyboard = variants[0].get("storyboard", [])
        scene_prompts = self._generate_scene_prompts(storyboard)

        prompt = scene_prompts.get(scene_name,
            f"A person presenting a product to camera. 50mm lens, soft natural lighting, "
            f"shallow depth of field. Clean modern background. Photorealistic."
        )

        # Add spoken dialogue for Veo's native audio generation
        if copy_text:
            prompt += f' The person speaks in {language} and says: "{copy_text}"'

        # Add scene-specific directives from the storyboard
        if directives:
            prompt += f" {directives}"

        # Quality suffix — photorealism + motion emphasis + NO text
        prompt += " Photorealistic, cinematic, natural skin texture, real-world lighting, smooth continuous motion. No CGI, no animation, no text, no captions, no subtitles, no watermark, no static frames."

        return prompt

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
                print(f"       Downloaded: {os.path.basename(output_path)}")
                return True
            else:
                print(f"       Download failed: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"       Download error: {e}")
            return False

    async def generate_scene_video(self, scene: Dict, output_path: str) -> bool:
        """Generates a single scene video using Gemini Veo 3.1 with asset references."""
        if not self.client:
            print("   Gemini API client not initialized. Missing API key.")
            return False
            
        prompt = self._build_prompt(scene)
        reference_images = await self._get_reference_images_for_scene(scene)
        
        scene_name = scene.get("scene", "?")
        print(f"     Generating scene '{scene_name}' with {len(reference_images)} asset reference(s)...")
        
        try:
            # Parse duration from scene dict (e.g. "8s" -> 8)
            duration_str = scene.get("duration", "8s")
            duration_sec = 8
            try:
                duration_sec = int(duration_str.replace("s", "").replace("sec", "").strip())
            except:
                pass

            # Veo 3.1 with reference images is VERY restrictive:
            #   - No enhancePrompt, no generateAudio, no negativePrompt, no allow_all
            # Without reference images: negativePrompt and allow_all work fine
            # With reference images: Veo 3.1 only allows minimal config
            #   (aspectRatio, durationSeconds, referenceImages, numberOfVideos)
            # Without reference images: full config works
            if reference_images:
                config_args = {
                    "number_of_videos": 1,
                    "duration_seconds": duration_sec,
                    "aspect_ratio": "9:16",
                    "reference_images": reference_images,
                }
            else:
                config_args = {
                    "number_of_videos": 1,
                    "duration_seconds": duration_sec,
                    "aspect_ratio": "9:16",
                    "person_generation": "allow_all",
                    "negative_prompt": (
                        "blurry, low quality, distorted face, extra fingers, "
                        "deformed hands, cartoon, anime, CGI, 3D render, "
                        "text overlay, watermark, logo, caption, subtitle, "
                        "plastic skin, uncanny valley, bad anatomy, static image"
                    ),
                }

            config = types.GenerateVideosConfig(**config_args)
            
            # Call Veo 3.1
            # Note: client.models.generate_videos is sync in the currently used SDK version
            # or it returns an operation that we can poll.
            operation = self.client.models.generate_videos(
                model=self.DEFAULT_MODEL,
                prompt=prompt,
                config=config,
            )
            
            print(f"       Operation started: {operation.name}")
            
            # Poll asynchronously
            start_time = time.time()
            import asyncio
            while not operation.done:
                elapsed = int(time.time() - start_time)
                if elapsed > self.MAX_POLL_TIME:
                    print(f"       TIMEOUT after {elapsed}s for scene '{scene_name}'")
                    return False
                
                print(f"       Waiting for scene '{scene_name}'... ({elapsed}s elapsed)", flush=True)
                await asyncio.sleep(self.POLL_INTERVAL)
                operation = self.client.operations.get(operation)
            
            # Check for errors
            if operation.error:
                print(f"       Veo error for scene '{scene_name}': {operation.error}")
                return False
            
            result = operation.result
            if result and result.generated_videos:
                gen_video = result.generated_videos[0]
                video_uri = gen_video.video.uri
                print(f"       Video URI: {video_uri}")
                
                # Download using requests + API key
                return self._download_video(video_uri, output_path)
            else:
                print(f"       No video generated in response for scene '{scene_name}'.")
                return False
                
        except Exception as e:
            print(f"     Gemini API Error for scene '{scene_name}': {e}")
            return False

    def _probe_video(self, path: str) -> Dict:
        """Probes a video file for duration and audio presence."""
        info = {"duration": 8.0, "has_audio": False}
        try:
            dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                       "-of", "default=noprint_wrappers=1:nokey=1", path]
            dur_result = subprocess.run(dur_cmd, capture_output=True, text=True, timeout=10)
            if dur_result.stdout.strip():
                info["duration"] = float(dur_result.stdout.strip())

            audio_cmd = ["ffprobe", "-v", "error", "-select_streams", "a",
                         "-show_entries", "stream=codec_type",
                         "-of", "default=noprint_wrappers=1:nokey=1", path]
            audio_result = subprocess.run(audio_cmd, capture_output=True, text=True, timeout=10)
            info["has_audio"] = bool(audio_result.stdout.strip())
        except Exception as e:
            print(f"     Probe error for {path}: {e}")
        return info

    def _normalize_scene(self, path: str, idx: int, target_w: int, target_h: int, temp_dir: str) -> str:
        """Normalizes a scene to consistent resolution/fps and adds silent audio if missing."""
        info = self._probe_video(path)
        norm_path = os.path.join(temp_dir, f"norm_{idx}_{int(time.time())}.mp4")

        # Build filter: scale + pad to target resolution, set fps to 30
        vf = f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2,fps=30"

        cmd = ["ffmpeg", "-y", "-i", path]

        if not info["has_audio"]:
            # Add silent audio track so all scenes have audio for merging
            cmd += ["-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo",
                    "-shortest"]

        cmd += ["-vf", vf, "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
                "-ac", "2", "-ar", "44100", norm_path]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0 and os.path.exists(norm_path):
            print(f"       Normalized scene {idx}: {info['duration']:.1f}s, audio={'yes' if info['has_audio'] else 'added silent'}")
            return norm_path

        print(f"       Normalize failed for scene {idx}: {result.stderr[:200] if result.stderr else 'unknown'}")
        return path

    def merge_videos(self, video_paths: List[str], final_output_path: str):
        """Merges scene videos with cross-fade transitions.

        No stretching — preserves original Veo frame rate and motion.
        Normalizes resolution/fps/audio before merging for compatibility.
        """
        import shutil
        print(f"   Merging {len(video_paths)} scenes into {final_output_path}...")

        if len(video_paths) == 1:
            shutil.copy2(video_paths[0], final_output_path)
            print(f"     Single scene copied directly.")
            return

        if not self._ffmpeg_available:
            print("     ffmpeg not available — copying first scene as final output.")
            shutil.copy2(video_paths[0], final_output_path)
            return

        norm_dir = tempfile.mkdtemp(prefix="merge_")
        FADE = 0.4

        # Step 1: Normalize all scenes (consistent resolution, fps, audio)
        print("     Normalizing scenes for merge compatibility...")
        normalized = []
        for i, vp in enumerate(video_paths):
            norm = self._normalize_scene(vp, i, 720, 1280, norm_dir)
            normalized.append(norm)

        # Step 2: Probe normalized durations
        durations = []
        for vp in normalized:
            info = self._probe_video(vp)
            durations.append(info["duration"])
        print(f"     Scene durations: {[f'{d:.1f}s' for d in durations]}")

        # Step 3: Try xfade merge (video + audio cross-fade)
        try:
            n = len(normalized)
            inputs = []
            for vp in normalized:
                inputs += ["-i", vp]

            # Calculate xfade offsets
            offsets = []
            cumulative = 0
            for i in range(n - 1):
                cumulative += durations[i] - FADE
                offsets.append(round(cumulative, 2))

            # Build video xfade chain
            vf = []
            af = []
            if n == 2:
                vf.append(f"[0:v][1:v]xfade=transition=fade:duration={FADE}:offset={offsets[0]}[outv]")
                af.append(f"[0:a][1:a]acrossfade=d={FADE}[outa]")
            else:
                vf.append(f"[0:v][1:v]xfade=transition=fade:duration={FADE}:offset={offsets[0]}[v1]")
                af.append(f"[0:a][1:a]acrossfade=d={FADE}[a1]")
                for i in range(2, n - 1):
                    vf.append(f"[v{i-1}][{i}:v]xfade=transition=fade:duration={FADE}:offset={offsets[i-1]}[v{i}]")
                    af.append(f"[a{i-1}][{i}:a]acrossfade=d={FADE}[a{i}]")
                vf.append(f"[v{n-2}][{n-1}:v]xfade=transition=fade:duration={FADE}:offset={offsets[n-2]}[outv]")
                af.append(f"[a{n-2}][{n-1}:a]acrossfade=d={FADE}[outa]")

            fc = ";".join(vf + af)
            cmd = ["ffmpeg", "-y"] + inputs + [
                "-filter_complex", fc,
                "-map", "[outv]", "-map", "[outa]",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "18",
                "-c:a", "aac", "-b:a", "128k",
                final_output_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0 and os.path.exists(final_output_path):
                size_mb = os.path.getsize(final_output_path) / (1024 * 1024)
                print(f"     Merged with cross-fade transitions! ({size_mb:.1f} MB)")
                return
            else:
                print(f"     Cross-fade failed: {result.stderr[:300] if result.stderr else 'unknown'}")
                print(f"     Falling back to simple concat...")
        except Exception as e:
            print(f"     Cross-fade error: {e}. Falling back to concat...")

        # Step 4: Fallback — simple concat (still uses normalized files)
        concat_file = os.path.join(norm_dir, "concat.txt")
        with open(concat_file, "w") as f:
            for path in normalized:
                safe_path = path.replace("'", "'\\''")
                f.write(f"file '{safe_path}'\n")

        try:
            cmd = [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", concat_file,
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "18",
                "-c:a", "aac", "-b:a", "128k",
                final_output_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                print(f"     Merged via concat fallback.")
            else:
                print(f"     Concat also failed: {result.stderr[:200] if result.stderr else 'unknown'}")
        except Exception as e:
            print(f"     FFmpeg merge error: {e}")
    async def _generate_fallback_image_video(self, scene: Dict, idx: int, temp_dir: str) -> str:
        """Generates a static image via Imagen (saved to GridFS) and animates it."""
        if not self._ffmpeg_available:
            print(f"       Fallback skipped: ffmpeg not available for image-to-video conversion.")
            return None

        from api.services.db_mongo_service import get_file_from_gridfs
        from api.services.ai_assist_service import ai_assist_service

        prompt = self._build_prompt(scene)
        print(f"       Fallback: Generating static image via Imagen for scene {idx}...")
        try:
            # Returns a GridFS ID now
            grid_file_id = await ai_assist_service.generate_fallback_image(prompt)
            
            if not grid_file_id:
                return None
                
            # Fetch bytes to animate
            img_data, _ = await get_file_from_gridfs(grid_file_id)
            
            img_temp = os.path.join(temp_dir, f"fallback_{idx}_{int(time.time())}.jpg")
            with open(img_temp, "wb") as f:
                f.write(img_data)
                
            out_video = os.path.join(temp_dir, f"scene_fallback_{idx}_{int(time.time())}.mp4")
            cmd = [
                "ffmpeg", "-y", "-loop", "1", "-i", img_temp,
                "-vf", "zoompan=z='zoom+0.0005':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=212:s=720x1280",
                "-c:v", "libx264", "-t", "8.5", "-pix_fmt", "yuv420p", "-preset", "medium",
                out_video
            ]
            subprocess.run(cmd, capture_output=True)
            return out_video if os.path.exists(out_video) else None
        except Exception as e:
            print(f"       Fallback Error: {e}")
            return None

    async def _apply_audio_and_overlay(self, idx: int, scene: Dict, video_path: str, temp_dir: str) -> str:
        """No-op: Veo 3.1 generates complete scenes with audio. No overlays needed.

        Text overlays (drawtext) were causing the "images with caption" look.
        Product image overlays were covering the AI-generated video.
        Veo already incorporates product context via reference images and prompts.
        """
        return video_path


    async def render_variant(self, variant: Dict) -> Dict:
        """Renders all scenes for a variant in parallel using asyncio.gather, retries failures, then merges."""
        variant_label = variant.get("variant", "?")
        # Robust handle storyboard / scenes
        storyboard = variant.get("storyboard") or variant.get("scenes") or []
        print(f"\n   Processing Variant {variant_label}: {variant.get('label', '')}")
        
        scene_videos = [None] * len(storyboard)
        temp_dir = tempfile.mkdtemp()
        
        if not storyboard:
            print("     Error: Empty storyboard. Cannot parallelize.")
            return {
                "variant": variant_label,
                "label": variant.get("label"),
                "status": "failed",
                "error": "Empty storyboard"
            }

        async def process_scene(idx, scene):
            scene_path = os.path.join(temp_dir, f"scene_{idx}.mp4")
            if await self.generate_scene_video(scene, scene_path):
                final_scene_path = await self._apply_audio_and_overlay(idx, scene, scene_path, temp_dir)
                return idx, final_scene_path
            return idx, None

        print(f"     Parallelizing {len(storyboard)} scenes via asyncio...")
        tasks = [process_scene(i, scene) for i, scene in enumerate(storyboard)]
        results = await asyncio.gather(*tasks)
        
        for idx, path in results:
            if path:
                scene_videos[idx] = path
            else:
                print(f"     Scene {idx} ({storyboard[idx].get('scene')}) generation failed.")
        
        # --- Retry failed scenes sequentially (up to 2 retries each) ---
        failed_indices = [i for i, v in enumerate(scene_videos) if v is None]
        if failed_indices:
            print(f"\n     Retrying {len(failed_indices)} failed scene(s)...")
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
                print(f"\n     ⚠️ {len(still_failed)} scenes failed Veo. Using static fallback...")
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

        # If merge didn't produce a file (e.g. ffmpeg error), copy the first scene
        if not os.path.exists(final_path) and valid_scene_videos:
            import shutil
            shutil.copy2(valid_scene_videos[0], final_path)
            print(f"     Merge output missing — copied first scene as final video.")

        return {
            "variant": variant_label,
            "label": variant.get("label"),
            "video_id": video_id,
            "status": "completed",
            "local_path": final_path if os.path.exists(final_path) else None,
            "scenes_count": len(valid_scene_videos)
        }

    async def generate_output(self, wait_for_render=True) -> Dict:
        """Main entry point for Step 7."""
        if not self.api_key:
            print("   GEMINI_API_KEY not found. Running dry run...")
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

if __name__ == "__main__":
    print("Testing GeminiRenderer standalone...")
