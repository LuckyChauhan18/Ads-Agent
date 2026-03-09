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

# Load .env from root directory (parent of backend)
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '..', '.env')
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
            
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # Points to backend
        self.video_dir = os.path.join(os.path.dirname(self.base_dir), "extra", "video")
        os.makedirs(self.video_dir, exist_ok=True)
        
        # Assets will be loaded during initialize()
        self.assets = {"product": [], "logo": [], "lifestyle": []}

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

    def _generate_scene_prompts(self, scene_list: List[Dict]) -> Dict[str, str]:
        """Uses Gemini Flash to generate product-specific cinematic prompts for Veo.
        
        Uses the 'visual_continuity' hints from the script to ensure a smooth flow.
        """
        if hasattr(self, '_cached_scene_prompts'):
            return self._cached_scene_prompts
        
        # Build continuity map from scene_list
        continuity_hints = "\n".join([
            f"- {s.get('scene')}: {s.get('visual_continuity', 'Maintain consistency')}"
            for s in scene_list
        ])
        
        product_info = self.context.get("product_understanding", {})
        product_name = product_info.get("product_name") or self.context.get("product_name", "the product")
        brand = product_info.get("brand_name") or self.context.get("brand_name", "the brand")
        category = product_info.get("category", "consumer product")

        features = product_info.get("features", [])
        description = product_info.get("description", "")
        user_problem = self.context.get("user_problem_raw", "a common user problem")
        brand_voice = self.context.get("brand_voice", "premium and modern")
        
        # Get offer/discount data for CTA
        # We need to handle cases where the user provided NO offer.
        offer_info = self.context.get("offer_and_risk_reversal", {})
        offers = offer_info.get("offers", [])
        
        discount = offers[0].get("discount", "") if offers else ""
        guarantee = offers[0].get("guarantee", "") if offers else ""
        trust_signals = self.context.get("trust_signals", [])
        reviews_text = trust_signals[0] if trust_signals else ""
        
        discount_msg = f"'{discount}'" if discount else ""
        guarantee_msg = f"'{guarantee}'" if guarantee else ""
        offer_statement = f"announces {discount_msg} {guarantee_msg}" if (discount_msg or guarantee_msg) else "speaks enthusiastically"
        
        # Get avatar info for prompt customization
        gender = self.avatar.get("gender") or self.avatar.get("avatar_preferences", {}).get("gender", "young Indian person")
        style = self.avatar.get("style") or self.avatar.get("avatar_preferences", {}).get("style", "cinematic")
        
        if not gender or str(gender).lower() in ("unknown", "auto"): 
            gender = "young Indian person"
        if str(style).lower() == "manual upload": 
            style = "realistic presenter"

        # Get language
        language = self.avatar.get("voice_preferences", {}).get("language", "Hindi")
        
        # Extract competitor DNA
        market_ctx = self.context.get("market_context", {})
        competitor_hooks = market_ctx.get("top_punch_lines", [])
        competitor_hooks_str = "\n".join([f"  - {h}" for h in competitor_hooks[:5]]) if competitor_hooks else "N/A"
        
        prompt = f"""You are a D2C brand video ad director creating a cinematic 9:16 vertical ad.

PRODUCT: {product_name}
BRAND: {brand}
CATEGORY: {category}
FEATURES: {', '.join(features[:5]) if features else 'N/A'}
DESCRIPTION: {description}
USER PROBLEM: {user_problem}
BRAND VOICE: {brand_voice}
LANGUAGE: {language}

DISCOUNT OFFER: {discount if discount else 'N/A'}
GUARANTEE: {guarantee if guarantee else 'N/A'}
REVIEWS: {reviews_text if reviews_text else 'N/A'}

COMPETITOR AD HOOKS (for inspiration):
{competitor_hooks_str}

=== STRICT D2C STORY ARC WITH SPEAKING AVATAR ===

EVERY scene MUST include the person defined by the provided reference image.
The person SPEAKS in {language}.
If a reference image of a person is provided, the person in the video MUST be an EXACT visual match to that person (identity, clothes, hair, facial features).
DO NOT use a random person or a generic avatar if a reference image exists.

VISUAL CONTINUITY PLAN (ADHERE STRICTLY):
{continuity_hints}

ENVIRONMENTAL CONSISTENCY RULES:
1. Locations MUST persist across scenes (e.g. if Hook is in a Park, Solution is also in a Park).
2. The actor (presenter) MUST maintain identical appearance (clothes, hair) in all scenes.
3. Use lighting and camera flow that builds on the previous scene's hint.

CRITICAL: All visuals MUST be relevant to the {category} category.
For example: if {category} is Motorcycles, show bikes/riders/roads. If Shoes, show running/feet/tracks. etc.

1. HOOK: A relatable {category} scene. A person SPEAKS to camera.
   - Show a {category}-relevant situation (e.g., for Motorcycles: a rider on a boring road, for Shoes: a runner warming up).
   - The person speaks in {language} about a relatable {category} situation. NO product visible.
   
2. PROBLEM: Person SPEAKS emotionally about the {category}-specific pain point.
   - Show {category}-specific frustration visually (e.g., for Motorcycles: old bike struggling in traffic, for Shoes: worn out shoes on painful feet).
   - Close-up, frustrated expression. NO product visible. The viewer must FEEL the problem.

3. SOLUTION: Person excitedly REVEALS {product_name} — FIRST TIME product appears!
   - They MUST say the name "{product_name}" while presenting it.
   - IMPORTANT: If the product is a large physical item (like a motorcycle, car, or furniture), they MUST NOT hold it (stand next to it or sit on it). Describe the EXACT type of product (e.g. a Royal Enfield motorcycle, NOT a generic scooter).
   - They speak about "{product_name}" features excitedly in {language}.

4. TRUST: Person SPEAKS confidently about {brand}'s credibility.
   - Professional setting with {brand} logo visible.
   - Person mentions "{brand}" by name, speaks about reviews and trust in {language}.

5. PROOF: Multiple happy people using {product_name} in {category}-relevant situations.
   - Presenter speaks about results in {language}, mentions "{product_name}" by name.
   - Dynamic scenes of satisfied {category} users.

6. CTA: MARKETING FINALE — Person speaks with URGENCY about {product_name}.
   - Show {product_name} hero shot + {brand} logo prominently on screen.
   - Person {offer_statement} and says "{product_name}" by name.
   - Urgent, exciting energy. "Buy {product_name} now!" vibe.

7. RELATABLE MOMENT: Alternative opening — candid {category}-related everyday moment.

For each scene, write a 3-4 sentence visual+audio description IN ENGLISH.
Include WHAT THE PERSON SAYS (in {language}), camera movements, and mood.
ALWAYS specify 9:16 vertical.

Return ONLY valid JSON:
{{
  "Hook": "description with dialogue...",
  "Problem": "description with dialogue...",
  "Solution": "description with dialogue...",
  "Trust": "description with dialogue...",
  "Proof": "description with dialogue...",
  "CTA": "description with marketing...",
  "Relatable Moment": "description..."
}}
"""
        
        try:
            if self.client:
                response = self.client.models.generate_content(
                    model="gemini-flash-latest",
                    contents=prompt,
                    config={'response_mime_type': 'application/json'}
                )
                self._cached_scene_prompts = json.loads(response.text)
                print(f"     Generated {len(self._cached_scene_prompts)} D2C scene prompts with voice via Gemini")
                return self._cached_scene_prompts
        except Exception as e:
            print(f"     LLM scene prompt generation failed: {e}. Using fallback.")
        
        # Fallback: D2C-aware prompts with speaking avatar
        self._cached_scene_prompts = {
            "Hook": f"A young Indian person looks at the camera and speaks in {language} about {user_problem}. They look concerned and relatable. Cinematic close-up, warm lighting. No product visible. 9:16 vertical.",
            "Problem": f"The same person speaks emotionally in {language} about the frustration of {user_problem}. Push-in camera, dramatic lighting. No product visible. 9:16 vertical.",
            "Solution": f"The person's expression changes to excitement as they proudly reveal the {product_name}! They stand next to the {category} and speak excitedly in {language} about its features. 360-degree dynamic showcase. 9:16 vertical.",
            "Trust": f"The person speaks confidently in {language} about {brand}'s reputation. Premium clean environment with floating review stars. 9:16 vertical.",
            "Proof": f"Multiple happy people using {product_name} in the real world. The presenter speaks in {language} about amazing results. Dynamic tracking shots. 9:16 vertical.",
            "CTA": f"Marketing finale: the person {offer_statement} with energy in {language}! Hero shot of {product_name} with {brand} text visible. Urgent buying energy. 9:16 vertical.",
            "Relatable Moment": f"A young person in a candid everyday moment dealing with {user_problem}. No product visible. Natural lighting. 9:16 vertical."
        }
        return self._cached_scene_prompts

    def _build_prompt(self, scene: Dict) -> str:
        """Builds a product-specific cinematic prompt for Veo with Hindi speaking dialogue."""
        scene_name = scene.get("scene", "")
        directives = scene.get("realistic_directives", "")
        copy_text = scene.get("voiceover", "")  # Hindi spoken dialogue
        
        # Get language for voice direction
        language = self.avatar.get("voice_preferences", {}).get("language", "Hindi")
        
        # Get dynamically generated scene prompts
        scene_prompts = self._generate_scene_prompts(self.variants.get("variants", [])[0].get("storyboard", []))
        
        prompt = scene_prompts.get(scene_name, 
            f"Cinematic footage of {self.context.get('product_understanding', {}).get('product_name', 'the product')}. "
            f"Premium lifestyle, 9:16 vertical."
        )
        
        # Add Hindi spoken dialogue as voice-over instruction for Veo
        if copy_text:
            prompt += f' The person in the video speaks in {language} and says: "{copy_text}"'
        
        # Add stylistic directives from storyboard
        if directives:
            prompt += f" {directives}"
        
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

            # Build config with reference images if available
            config_args = {
                "number_of_videos": 1,
                "duration_seconds": duration_sec
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
                return self._download_video(video_uri, output_path)
            else:
                print(f"       No video generated in response for scene '{scene_name}'.")
                return False
                
        except Exception as e:
            print(f"     Gemini API Error for scene '{scene_name}': {e}")
            return False

    def merge_videos(self, video_paths: List[str], final_output_path: str):
        """Merges multiple video files using FFmpeg with smooth cross-fade transitions."""
        print(f"   Merging {len(video_paths)} scenes into {final_output_path}...")
        
        if len(video_paths) == 1:
            import shutil
            shutil.copy2(video_paths[0], final_output_path)
            print(f"     Single scene  copied directly.")
            return
        
        FADE_DURATION = 0.5  # seconds of cross-fade between scenes
        
        # --- Pre-process: Stretch Veo 5s videos to 8.5s natively ---
        print("     Normalizing scenes to 8.5s via cinematic slow-motion stretching...")
        import tempfile
        import time
        import os
        
        stretched_paths = []
        for i, vp in enumerate(video_paths):
            probe_cmd = [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", vp
            ]
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
            original_dur = float(probe_result.stdout.strip()) if probe_result.stdout.strip() else 5.0
            
            target_dur = 8.5
            ratio = target_dur / original_dur
            
            if ratio > 1.1:
                stretched_vp = os.path.join(tempfile.gettempdir(), f"stretch_{int(time.time()*100)}_{i}.mp4")
                # Check for audio stream
                audio_probe = subprocess.run(["ffprobe", "-i", vp, "-show_streams", "-select_streams", "a", "-loglevel", "error"], capture_output=True, text=True)
                
                if audio_probe.stdout.strip():
                    filter_str = f"[0:v]setpts={ratio}*PTS[v];[0:a]atempo={1.0/ratio}[a]"
                    stretch_cmd = [
                        "ffmpeg", "-y", "-i", vp,
                        "-filter_complex", filter_str,
                        "-map", "[v]", "-map", "[a]",
                        "-c:v", "libx264", "-preset", "ultrafast",
                        "-c:a", "aac",
                        stretched_vp
                    ]
                else:
                    filter_str = f"[0:v]setpts={ratio}*PTS[v]"
                    stretch_cmd = [
                        "ffmpeg", "-y", "-i", vp,
                        "-filter_complex", filter_str,
                        "-map", "[v]",
                        "-c:v", "libx264", "-preset", "ultrafast",
                        stretched_vp
                    ]
                
                subprocess.run(stretch_cmd, capture_output=True)
                if os.path.exists(stretched_vp):
                    stretched_paths.append(stretched_vp)
                else:
                    stretched_paths.append(vp)
            else:
                stretched_paths.append(vp)
                
        video_paths = stretched_paths
        
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
            
            filter_complex = ";".join(video_filters + audio_filters)
            
            cmd = ["ffmpeg", "-y"] + inputs + [
                "-filter_complex", filter_complex,
                "-map", "[outv]", "-map", "[outa]",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium",
                "-c:a", "aac", "-b:a", "128k",
                final_output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"     Final video merged with smooth cross-fade transitions!")
                return
            else:
                print(f"     Cross-fade failed, falling back to simple concat...")
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
