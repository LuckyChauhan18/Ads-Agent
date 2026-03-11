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
        """Loads product images and logo from GridFS based on campaign_id."""
        from api.services.db_mongo_service import get_user_assets
        
        # Robust campaign_id and user_id extraction
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

        try:
            items = await get_user_assets(user_id)
            for item in items:
                metadata = item.get("metadata", {})
                item_campaign_id = metadata.get("campaign_id")
                
                # Check for campaign_id match (if provided)
                if campaign_id and item_campaign_id and str(item_campaign_id) != str(campaign_id):
                    continue
                
                asset_type = metadata.get("asset_type")
                file_id = str(item["_id"])
                if asset_type in loaded:
                    loaded[asset_type].append(file_id)
        except Exception as e:
            print(f"       Failed to load assets from GridFS: {e}")
            
        print(f"   Assets loaded: {len(loaded['product'])} product, {len(loaded['logo'])} logo")
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
        """Returns Veo reference images based on D2C story arc."""
        scene_name = scene.get("scene", "")
        references = []

        # --- Custom Avatar Reference (Priority) ---
        avatar_obj = scene.get("avatar") or {}
        # Prioritize scene-specific avatar first, then top-level self.avatar
        custom_avatar_url = avatar_obj.get("custom_image_url") or avatar_obj.get("url")
        if not custom_avatar_url:
            custom_avatar_url = self.avatar.get("custom_image_url") or self.avatar.get("url")
        
        if custom_avatar_url:
            file_id = None
            if "/files/" in str(custom_avatar_url):
                file_id = str(custom_avatar_url).split("/files/")[-1]
            elif len(str(custom_avatar_url)) >= 24: # Likely a MongoDB ObjectId string
                file_id = str(custom_avatar_url)
            
            if file_id:
                img = await self._load_image_for_veo(file_id)
                if img:
                    ref = types.VideoGenerationReferenceImage(
                        image=img,
                        reference_type="ASSET"
                    )
                    references.append(ref)
                    print(f"       ✅ Using custom avatar reference for scene: {file_id}")
        
        # --- D2C STORY ARC: NO product in Hook/Problem ---
        if scene_name in ("Hook", "Problem", "Relatable Moment", "Stop scroll", "Agitate pain"):
            return references[:3]
        
        # --- Solution/Proof: Product images (the reveal) ---
        elif scene_name in ("Solution", "Proof", "Introduce product", "Show results"):
            for img_path in self.assets["product"][:2]:
                img = await self._load_image_for_veo(img_path)
                if img:
                    ref = types.VideoGenerationReferenceImage(
                        image=img,
                        reference_type="ASSET"
                    )
                    references.append(ref)
        
        # --- Trust/CTA: Logo + product (brand identity) ---
        elif scene_name in ("CTA", "Trust", "Drive action", "Build credibility"):
            for img_path in self.assets["logo"][:1]:
                img = await self._load_image_for_veo(img_path)
                if img:
                    ref = types.VideoGenerationReferenceImage(
                        image=img,
                        reference_type="ASSET"
                    )
                    references.append(ref)
            if self.assets["product"]:
                img = await self._load_image_for_veo(self.assets["product"][0])
                if img:
                    ref = types.VideoGenerationReferenceImage(
                        image=img,
                        reference_type="ASSET"
                    )
                    references.append(ref)
        
        return references[:3]

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

        prompt = f"""You are a cinematographer writing SHORT, PRECISE video prompts for Google Veo 3.1 AI video generator.

PRODUCT: {ctx['product_name']} by {ctx['brand']} ({ctx['category']})
FEATURES: {', '.join(ctx['features'][:4]) if ctx['features'] else 'premium quality'}
PROBLEM IT SOLVES: {ctx['user_problem']}
PRESENTER: {ctx['gender']}, speaking in {ctx['language']}

SCENE CONTINUITY NOTES:
{continuity_hints}

=== RULES FOR WRITING VEO PROMPTS ===
1. Each prompt must be 2-3 sentences MAX. Veo works best with concise, specific descriptions.
2. ALWAYS specify: camera gear, lens type, lighting, exact setting, and what the person is doing.
3. Use REAL filmmaking terms: "Shot on Arri Alexa 65", "85mm lens", "shallow depth of field", "golden hour", "tracking shot", "rack focus", "handheld", "steadicam", "close-up", "medium close-up".
4. Describe the person's EXACT appearance, clothing, and expression. Action should be grounded and subtle.
5. Specify the EXACT location (e.g. "modern minimalist apartment with white walls and warm practical lights").
6. BANNED WORDS: "cinematic", "premium", "dynamic", "high quality", "4k". Instead, describe what makes it look that way.
7. GROUNDED REALISM: Specify "natural skin texture", "subtle skin imperfection", "real-world mixed lighting".
8. The person speaks directly to camera in {ctx['language']}.
9. For product scenes: describe the product's REAL physical appearance (color, shape, size).

Write prompts for these scenes:

HOOK: The presenter in a real {ctx['category']}-related setting, speaking to camera about {ctx['user_problem']}. No product visible. Show genuine emotion.

PROBLEM: Same presenter, same setting. Frustrated expression, speaking emotionally about the pain of {ctx['user_problem']}. Tight framing on face.

SOLUTION: Presenter's face lights up with excitement. They present {ctx['product_name']} to camera. First time product appears. Describe the product physically.

TRUST: Presenter in a clean, well-lit setting. Speaking confidently about {ctx['brand']}. Professional and trustworthy energy.

PROOF: Presenter demonstrating {ctx['product_name']} in use. Show the product being used naturally. Happy, satisfied expression.

CTA: Presenter holds/shows {ctx['product_name']} close to camera with energy. {"Mentions " + ctx['discount'] + ". " if ctx['discount'] else ""}Urgent, excited call to action.

RELATABLE MOMENT: Candid slice-of-life moment. The presenter in an everyday {ctx['category']}-related situation before discovering the product.

Return ONLY valid JSON with scene names as keys and prompt strings as values.
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
                    model="gemini-2.5-flash-preview-05-20",
                    contents=prompt,
                    config={'response_mime_type': 'application/json'}
                )
                self._cached_scene_prompts = json.loads(response.text)
                print(f"     Generated {len(self._cached_scene_prompts)} photorealistic scene prompts via Gemini")
                return self._cached_scene_prompts
        except Exception as e:
            print(f"     LLM scene prompt generation failed: {e}. Using fallback.")

        # Fallback: highly specific photorealistic prompts
        ctx = self._get_scene_context()
        self._cached_scene_prompts = {
            "Hook": f"Medium close-up of a {ctx['gender']} standing in a naturally lit {ctx['category']}-related environment, looking directly into camera with a concerned expression. Shot on Arri Alexa 65, 50mm lens, f/2.8, shallow depth of field, warm natural window light. Natural skin texture. The person speaks in {ctx['language']} about {ctx['user_problem']}.",
            "Problem": f"Tight close-up on the same {ctx['gender']}'s face, 85mm lens with creamy bokeh. Soft directional practical light from the left. Frustrated expression, subtle micro-expressions. They speak emotionally in {ctx['language']} about the struggle with {ctx['user_problem']}. Subtle handheld camera drift.",
            "Solution": f"Medium shot of the same {ctx['gender']} holding {ctx['product_name']} up to camera with both hands, face lit up with genuine excitement. Clean bright background with soft diffused overhead lighting. 35mm lens. True-to-life color grading. They speak enthusiastically in {ctx['language']} about {ctx['product_name']}.",
            "Trust": f"The same {ctx['gender']} in a modern, clean white environment with soft practical lighting. Medium close-up, 50mm lens. Confident posture, direct eye contact with camera. Speaking in {ctx['language']} about {ctx['brand']}'s quality and reputation.",
            "Proof": f"Extreme close-up macro tracking shot of {ctx['product_name']} being used naturally in a real-life setting. Shot on 35mm lens, natural daylight. Authentic interaction. The person speaks in {ctx['language']} about the results.",
            "CTA": f"Close-up of the same {ctx['gender']} energetically presenting {ctx['product_name']} to camera. Bright, punchy lighting but with natural shadow roll-off. 50mm lens. Excited expression, urgent tone, speaking in {ctx['language']}. {'Mentions ' + ctx['discount'] + '.' if ctx['discount'] else ''}",
            "Relatable Moment": f"Medium close-up of a {ctx['gender']} in an everyday {ctx['category']}-related situation. Natural ambient lighting, 35mm lens. Candid, documentary style, slight grain. No product visible. Slight handheld camera movement."
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

        # Combine with Global Style if available
        global_style = self.variants.get("variants", [])[0].get("storyboard_output", {}).get("global_style", "")
        if global_style:
            prompt += f" Overall Style Setup: {global_style}"

        # Photorealism quality suffix — keeps Veo grounded in realistic output
        prompt += " Photorealistic, highly detailed natural skin texture, skin pores, shot on Arri Alexa 65, f/2.8, physical world lighting. NO CGI, NO animation, NO text overlays, NO plastic skin, NO AI smoothing, authentic imperfect reality."

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
            target_duration_sec = 8
            try:
                target_duration_sec = int(duration_str.replace("s", "").replace("sec", "").strip())
            except:
                pass
                
            veo_duration_sec = max(5, min(target_duration_sec, 8))

            # Build config with quality-optimized parameters
            config_args = {
                "number_of_videos": 1,
                "duration_seconds": veo_duration_sec,
                "aspect_ratio": "9:16"
            }
            if reference_images:
                config_args["reference_images"] = reference_images

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
                success = self._download_video(video_uri, output_path)
                
                if success and target_duration_sec != veo_duration_sec and self._ffmpeg_available:
                    print(f"       Adjusting video duration from {veo_duration_sec}s to {target_duration_sec}s...")
                    self._adjust_video_duration(output_path, veo_duration_sec, target_duration_sec)
                    
                return success
            else:
                print(f"       No video generated in response for scene '{scene_name}'.")
                return False
                
        except Exception as e:
            print(f"     Gemini API Error for scene '{scene_name}': {e}")
            return False

    def _adjust_video_duration(self, video_path: str, current_sec: int, target_sec: int):
        """Stretches or trims the generated video to match the target duration using FFmpeg."""
        temp_path = video_path + ".tmp.mp4"
        try:
            if target_sec < current_sec:
                # Trim
                cmd = [
                    "ffmpeg", "-y", "-i", video_path,
                    "-t", str(target_sec),
                    "-c:v", "libx264", "-preset", "fast",
                    "-c:a", "aac",
                    temp_path
                ]
            else:
                # Stretch
                ratio = target_sec / float(current_sec)
                cmd = [
                    "ffmpeg", "-y", "-i", video_path,
                    "-filter:v", f"setpts={ratio}*PTS",
                    "-c:v", "libx264", "-preset", "fast",
                    temp_path
                ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and os.path.exists(temp_path):
                import shutil
                shutil.move(temp_path, video_path)
            else:
                print(f"       FFmpeg duration adjustment failed: {result.stderr}")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        except Exception as e:
            print(f"       Exception during duration adjustment: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def merge_videos(self, video_paths: List[str], final_output_path: str):
        """Merges multiple video files using FFmpeg with smooth cross-fade transitions.
        Falls back to copying the first scene if ffmpeg is not available."""
        import shutil
        print(f"   Merging {len(video_paths)} scenes into {final_output_path}...")

        if len(video_paths) == 1:
            shutil.copy2(video_paths[0], final_output_path)
            print(f"     Single scene copied directly.")
            return

        # If ffmpeg is not installed, just copy the first scene as the final video
        if not self._ffmpeg_available:
            print("     ffmpeg not available — copying first scene as final output.")
            shutil.copy2(video_paths[0], final_output_path)
            return

        FADE_DURATION = 0.5  # seconds of cross-fade between scenes

        try:
            # Build FFmpeg xfade filter chain for smooth transitions
            # First, probe each video duration
            durations = []
            for vp in video_paths:
                probe_cmd = [
                    "ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1", vp
                ]
                probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
                dur = float(probe_result.stdout.strip()) if probe_result.stdout.strip() else 8.0
                durations.append(dur)

            # Build input arguments
            inputs = []
            for vp in video_paths:
                inputs += ["-i", vp]

            # Build xfade filter chain
            n = len(video_paths)
            video_filters = []
            audio_filters = []

            # Calculate offsets for each xfade transition
            offsets = []
            cumulative = 0
            for i in range(n - 1):
                cumulative += durations[i] - FADE_DURATION
                offsets.append(cumulative)

            # Chain xfade filters: [0][1] -> tmp1, [tmp1][2] -> tmp2, etc.
            if n == 2:
                video_filters.append(f"[0:v][1:v]xfade=transition=fade:duration={FADE_DURATION}:offset={offsets[0]}[outv]")
                audio_filters.append(f"[0:a][1:a]acrossfade=d={FADE_DURATION}[outa]")
            else:
                # First pair
                video_filters.append(f"[0:v][1:v]xfade=transition=fade:duration={FADE_DURATION}:offset={offsets[0]}[v1]")
                audio_filters.append(f"[0:a][1:a]acrossfade=d={FADE_DURATION}[a1]")

                # Middle pairs
                for i in range(2, n - 1):
                    prev_v = f"v{i-1}"
                    prev_a = f"a{i-1}"
                    curr_v = f"v{i}"
                    curr_a = f"a{i}"
                    video_filters.append(f"[{prev_v}][{i}:v]xfade=transition=fade:duration={FADE_DURATION}:offset={offsets[i-1]}[{curr_v}]")
                    audio_filters.append(f"[{prev_a}][{i}:a]acrossfade=d={FADE_DURATION}[{curr_a}]")

                # Last pair
                last_v = f"v{n-2}"
                last_a = f"a{n-2}"
                video_filters.append(f"[{last_v}][{n-1}:v]xfade=transition=fade:duration={FADE_DURATION}:offset={offsets[n-2]}[outv]")
                audio_filters.append(f"[{last_a}][{n-1}:a]acrossfade=d={FADE_DURATION}[outa]")

            # Add a film grain + contrast curve filter for extra photorealism to the post-xfade result
            # We first transition, then apply subtle noise (luma grain) and a mild contrast eq
            post_filter = "[outv]eq=contrast=1.05:saturation=1.05,noise=alls=2:allf=t+u[finalv]"
            filter_complex = ";".join(video_filters + audio_filters) + ";" + post_filter

            cmd = ["ffmpeg", "-y"] + inputs + [
                "-filter_complex", filter_complex,
                "-map", "[finalv]", "-map", "[outa]",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium",
                "-c:a", "aac", "-b:a", "128k",
                final_output_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                print(f"     Final video merged with smooth cross-fade, film grain, and contrast grading!")
                return
            else:
                print(f"     Cross-fade/Post-processing failed, falling back to simple concat...")
                print(f"       FFmpeg Error: {result.stderr}")
        except Exception as e:
            print(f"     Cross-fade error: {e}. Falling back to concat...")

        # Fallback: simple concat
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for path in video_paths:
                safe_path = path.replace("'", "'\\''")
                f.write(f"file '{safe_path}'\n")
            concat_file = f.name

        try:
            cmd = [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", concat_file,
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium",
                "-c:a", "aac", "-b:a", "128k",
                final_output_path
            ]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"     Final video merged (simple concat fallback).")
        except Exception as e:
            print(f"     FFmpeg merge error: {e}")
        finally:
            if os.path.exists(concat_file):
                os.remove(concat_file)
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
        """Applies overlays BRAND logo/product images on the video."""
        if not self._ffmpeg_available:
            return video_path  # Skip overlays without ffmpeg

        from api.services.db_mongo_service import get_file_from_gridfs
        output_path = video_path

        try:
            # Note: SARVAM TTS is currently handled by frontend or disabled to avoid sync issues.
            # We focus on visual overlays here.

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
                    # Scale logo, overlay top right
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
                    # Scale product image, overlay bottom right
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
            print(f"       Failed to apply branding overlay: {e}")
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
