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
        self.avatar = avatar_config
        self.context = campaign_context
        
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None
            
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.video_dir = os.path.join(self.base_dir, "video")
        os.makedirs(self.video_dir, exist_ok=True)
        
        # Load PUMA assets
        self.assets = self._load_assets()

    def _load_assets(self) -> Dict:
        """Loads product images and logo from Redis based on campaign_id."""
        import asyncio
        from api.services.db_mongo_service import get_user_assets
        
        # Robust campaign_id extraction
        campaign_id = None
        user_id = None
        if isinstance(self.context, dict):
            campaign_id = self.context.get("campaign_id") or self.context.get("_id")
            user_id = self.context.get("user_id")
            if campaign_id:
                campaign_id = str(campaign_id)
            if user_id:
                user_id = str(user_id)
            
        print(f"   Loading assets from Redis for campaign: {campaign_id}")
        
        loaded = {"product": [], "logo": [], "lifestyle": []}
        
        async def fetch_assets():
            if not user_id: return loaded
            items = await get_user_assets(user_id)
            for item in items:
                if item.get("metadata", {}).get("campaign_id") == campaign_id:
                    asset_type = item.get("metadata", {}).get("asset_type")
                    file_id = str(item["_id"])
                    if asset_type in loaded:
                        loaded[asset_type].append(file_id)
            return loaded

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loaded = loop.run_until_complete(fetch_assets())
            loop.close()
        except Exception as e:
            print(f"       Failed to load assets from Redis: {e}")
            
        print(f"   Assets loaded from Redis: {len(loaded['product'])} product, {len(loaded['logo'])} logo")
        return loaded

    def _load_image_for_veo(self, asset_id: str):
        """Loads an image from GridFS and returns a types.Image."""
        from api.services.db_mongo_service import get_file_from_gridfs
        import asyncio
        try:
            async def fetch():
                content, metadata = await get_file_from_gridfs(asset_id)
                return content, metadata
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            image_bytes, metadata = loop.run_until_complete(fetch())
            loop.close()
            
            mime_type = metadata.get("content_type", "image/jpeg")
            return types.Image(image_bytes=image_bytes, mime_type=mime_type)
        except Exception as e:
            print(f"       Failed to load Redis image {asset_id}: {e}")
            return None

    def _get_reference_images_for_scene(self, scene: Dict) -> List:
        """Returns Veo reference images based on D2C story arc.
        
        D2C Marketing Logic:
        - Hook/Problem → NO product assets (show the pain, not the solution)
        - Solution/Proof → Product assets (the big reveal + social proof)
        - Trust/CTA → Logo + product (brand credibility + call to action)
        """
        scene_name = scene.get("scene", "")
        references = []

        # --- Custom Avatar Reference (Priority) ---
        custom_avatar_url = (scene.get("avatar") or {}).get("custom_image_url")
        if custom_avatar_url:
            relative_path = custom_avatar_url.lstrip("/")
            full_path = os.path.join(self.base_dir, relative_path)
            
            if os.path.exists(full_path):
                img = self._load_image_for_veo(full_path)
                if img:
                    ref = types.VideoGenerationReferenceImage(
                        image=img,
                        reference_type="ASSET"
                    )
                    references.append(ref)
        
        # --- D2C STORY ARC: NO product in Hook/Problem ---
        if scene_name in ("Hook", "Problem", "Relatable Moment"):
            return references[:3]
        
        # --- Solution/Proof: Product images (the reveal) ---
        elif scene_name in ("Solution", "Proof"):
            for img_path in self.assets["product"][:2]:
                img = self._load_image_for_veo(img_path)
                if img:
                    ref = types.VideoGenerationReferenceImage(
                        image=img,
                        reference_type="ASSET"
                    )
                    references.append(ref)
        
        # --- Trust/CTA: Logo + product (brand identity) ---
        elif scene_name in ("CTA", "Trust"):
            for img_path in self.assets["logo"][:1]:
                img = self._load_image_for_veo(img_path)
                if img:
                    ref = types.VideoGenerationReferenceImage(
                        image=img,
                        reference_type="ASSET"
                    )
                    references.append(ref)
            if self.assets["product"]:
                img = self._load_image_for_veo(self.assets["product"][0])
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

EVERY scene MUST include a young Indian person who SPEAKS in {language}.
The person acts as a presenter/narrator — they look at the camera and SPEAK the ad copy.

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

    def generate_scene_video(self, scene: Dict, output_path: str) -> bool:
        """Generates a single scene video using Gemini Veo 3.1 with asset references."""
        if not self.client:
            print("   Gemini API client not initialized. Missing API key.")
            return False
            
        prompt = self._build_prompt(scene)
        reference_images = self._get_reference_images_for_scene(scene)
        
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
            operation = self.client.models.generate_videos(
                model=self.DEFAULT_MODEL,
                prompt=prompt,
                config=config,
            )
            
            print(f"       Operation started: {operation.name}")
            
            # Poll with refresh using client.operations.get()
            start_time = time.time()
            while not operation.done:
                elapsed = int(time.time() - start_time)
                if elapsed > self.MAX_POLL_TIME:
                    print(f"       TIMEOUT after {elapsed}s for scene '{scene_name}'")
                    return False
                
                print(f"       Waiting... ({elapsed}s elapsed)", flush=True)
                time.sleep(self.POLL_INTERVAL)
                operation = self.client.operations.get(operation)
            
            # Check for errors
            if operation.error:
                print(f"       Veo error: {operation.error}")
                return False
            
            result = operation.result
            if result and result.generated_videos:
                gen_video = result.generated_videos[0]
                video_uri = gen_video.video.uri
                print(f"       Video URI: {video_uri}")
                
                # Download using requests + API key
                return self._download_video(video_uri, output_path)
            else:
                print("       No video generated in response.")
                return False
                
        except Exception as e:
            print(f"     Gemini API Error: {e}")
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
    def _generate_fallback_image_video(self, scene: Dict, idx: int, temp_dir: str) -> str:
        """Generates a static image via Imagen (saved to GridFS) and animates it."""
        import asyncio
        from api.services.db_mongo_service import get_file_from_gridfs
        from api.services.ai_assist_service import ai_assist_service
        
        prompt = self._build_prompt(scene)
        print(f"       Fallback: Generating static image via Imagen for scene {idx}...")
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            # Returns a GridFS ID now
            grid_file_id = loop.run_until_complete(ai_assist_service.generate_fallback_image(prompt))
            
            if not grid_file_id:
                return None
                
            # Fetch bytes to animate
            img_data, _ = loop.run_until_complete(get_file_from_gridfs(grid_file_id))
            loop.close()
            
            img_temp = os.path.join(temp_dir, f"fallback_{idx}.jpg")
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

    def _apply_audio_and_overlay(self, idx: int, scene: Dict, video_path: str, temp_dir: str) -> str:
        import asyncio
        from api.services.db_mongo_service import get_file_from_gridfs
        try:
            from api.services.audio_service import audio_service
            import subprocess
            
            output_path = video_path
            scene_name = scene.get("scene", "")
            voiceover = scene.get("voiceover", "")
            language = self.avatar.get("voice_preferences", {}).get("language", "Hindi")
            
            # Step 1: Audio narration is now handled by browser Web Speech API
            # Sarvam TTS disabled — it was out of sync with video frames
            # The frontend VideoStep.jsx uses Web Speech API for timed narration
            
            # Step 2: Overlay Branding (Logo + Product Name + Product Image)
            product_info = self.context.get("product_understanding", {})
            product_name = product_info.get("product_name") or self.context.get("product_name", "")
            brand_name = product_info.get("brand_name") or self.context.get("brand_name", "")
            
            # Prepare overlays
            overlay_inputs = []
            filter_complex = "[0:v]"
            input_idx = 1 # 0 is video
            
            # A. Persistent Logo (Top Right)
            if self.assets.get("logo"):
                logo_asset_id = self.assets["logo"][0]
                async def fetch_logo():
                    content, _ = await get_file_from_gridfs(logo_asset_id)
                    return content
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                logo_data = loop.run_until_complete(fetch_logo())
                loop.close()
                
                if logo_data:
                    logo_path = os.path.join(temp_dir, f"logo_overlay_{idx}.png")
                    with open(logo_path, "wb") as f:
                        f.write(logo_data)
                    overlay_inputs += ["-i", logo_path]
                    curr_logo_idx = input_idx
                    # Scale logo to ~150px width, overlay top right
                    filter_complex += f"[{curr_logo_idx}:v]scale=150:-1[logo];{filter_complex}[logo]overlay=W-w-20:20[v_with_logo]"
                    filter_complex = "[v_with_logo]"
                    input_idx += 1
            
            # B. Product Image Overlay (Bottom Right)
            if scene_name in ["Solution", "Proof", "CTA"] and self.assets.get("product"):
                product_asset_id = self.assets["product"][0]
                async def fetch_prod():
                    content, _ = await get_file_from_gridfs(product_asset_id)
                    return content
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                img_data = loop.run_until_complete(fetch_prod())
                loop.close()
                
                if img_data:
                    img_path = os.path.join(temp_dir, f"overlay_product_{idx}.png")
                    with open(img_path, "wb") as f:
                        f.write(img_data)
                    overlay_inputs += ["-i", img_path]
                    curr_img_idx = input_idx
                    # Scale product image to ~200px width, overlay bottom right
                    filter_complex += f"[{curr_img_idx}:v]scale=200:-1[prod];{filter_complex}[prod]overlay=W-w-20:H-h-20[v_with_prod]"
                    filter_complex = "[v_with_prod]"
                    input_idx += 1
            
            # C. Product Name Text (Bottom Center)
            if scene_name in ["Solution", "CTA"]:
                text_to_show = f"{brand_name} {product_name}".strip().upper()
                if text_to_show:
                    # Use a standard font path for Windows (Arial)
                    font_path = "C\\\\:/Windows/Fonts/arial.ttf"
                    # Draw text with shadow for readability
                    filter_complex += f",drawtext=text='{text_to_show}':fontfile='{font_path}':fontsize=36:fontcolor=white:shadowcolor=black@0.5:shadowx=2:shadowy=2:x=(w-text_w)/2:y=H-th-80"
            
            # D. BUY NOW CTA Banner (CTA scene only)
            if scene_name == "CTA":
                product_url = (
                    product_info.get("product_url", "") 
                    or self.context.get("product_input", {}).get("product_url", "")
                )
                if product_url:
                    # Extract short domain for display (e.g. www.example.com)
                    try:
                        from urllib.parse import urlparse
                        domain = urlparse(product_url).netloc or product_url
                    except Exception:
                        domain = product_url[:40]
                    
                    buy_text = f"BUY NOW  {domain}"
                    # Escape special chars for FFmpeg drawtext
                    buy_text = buy_text.replace("'", "").replace(":", "\\\\:")
                    font_path = "C\\\\:/Windows/Fonts/arialbd.ttf"
                    # Dark semi-transparent banner + white text at bottom
                    filter_complex += (
                        f",drawbox=x=0:y=H-60:w=W:h=60:color=black@0.7:t=fill"
                        f",drawtext=text='{buy_text}'"
                        f":fontfile='{font_path}'"
                        f":fontsize=28"
                        f":fontcolor=white"
                        f":x=(w-text_w)/2"
                        f":y=H-45"
                    )

            # Execute combined FFmpeg command if we have overlays/text
            if input_idx > 1 or "drawtext" in filter_complex:
                overlay_out = os.path.join(temp_dir, f"scene_{idx}_branded.mp4")
                print(f"       Applying branding overlays (Logo/Text/Product) to scene {idx}...")
                
                # If filter_complex still starts with [0:v], it means no overlays were added (just string re-assignment)
                if filter_complex == "[0:v]":
                     return output_path

                cmd = ["ffmpeg", "-y", "-i", output_path] + overlay_inputs + [
                    "-filter_complex", filter_complex,
                    "-c:a", "copy", overlay_out
                ]
                subprocess.run(cmd, capture_output=True)
                if os.path.exists(overlay_out):
                    output_path = overlay_out
                        
            return output_path
        except Exception as e:
            print(f"       Failed to apply audio/overlay: {e}")
            return video_path


    def render_variant(self, variant: Dict) -> Dict:
        """Renders all scenes for a variant in parallel, retries failures, then merges."""
        variant_label = variant.get("variant", "?")
        storyboard = variant.get("storyboard", [])
        print(f"\n   Processing Variant {variant_label}: {variant.get('label', '')}")
        
        scene_videos = [None] * len(storyboard)
        temp_dir = tempfile.mkdtemp()
        
        print(f"     Parallelizing {len(storyboard)} scenes...")
        
        if not storyboard:
            print("     Error: Empty storyboard. Cannot parallelize.")
            return {
                "variant": variant_label,
                "label": variant.get("label"),
                "status": "failed",
                "error": "Empty storyboard"
            }

        def process_scene(idx, scene):
            scene_path = os.path.join(temp_dir, f"scene_{idx}.mp4")
            if self.generate_scene_video(scene, scene_path):
                final_scene_path = self._apply_audio_and_overlay(idx, scene, scene_path, temp_dir)
                return idx, final_scene_path
            return idx, None

        max_workers = max(1, min(len(storyboard), 5)) if storyboard else 1
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_scene = {executor.submit(process_scene, i, scene): i for i, scene in enumerate(storyboard)}
            for future in concurrent.futures.as_completed(future_to_scene):
                idx, path = future.result()
                if path:
                    scene_videos[idx] = path
                else:
                    print(f"     Scene {idx} generation failed (will retry).")
        
        # --- Retry failed scenes sequentially (up to 2 retries each) ---
        failed_indices = [i for i, v in enumerate(scene_videos) if v is None]
        if failed_indices:
            print(f"\n     Retrying {len(failed_indices)} failed scene(s)...")
            for attempt in range(1, 3):  # Max 2 retries
                still_failed = [i for i in failed_indices if scene_videos[i] is None]
                if not still_failed:
                    break
                for idx in still_failed:
                    scene = storyboard[idx]
                    print(f"     Retry {attempt}/2 for scene '{scene.get('scene', idx)}'...")
                    scene_path = os.path.join(temp_dir, f"scene_{idx}.mp4")
                    if self.generate_scene_video(scene, scene_path):
                        final_scene_path = self._apply_audio_and_overlay(idx, scene, scene_path, temp_dir)
                        scene_videos[idx] = final_scene_path
                        print(f"     Scene '{scene.get('scene', idx)}' succeeded on retry {attempt}!")
        
        valid_scene_videos = []
        for i, v in enumerate(scene_videos):
            if v is not None:
                valid_scene_videos.append(v)
            else:
                print(f"     CRITICAL: Scene {i} completely failed after retries. Enacting AI Image Fallback with Ken Burns zoom.")
                fallback_path = self._generate_fallback_image_video(storyboard[i], i, temp_dir)
                if fallback_path:
                    final_fallback_path = self._apply_audio_and_overlay(i, storyboard[i], fallback_path, temp_dir)
                    valid_scene_videos.append(final_fallback_path)
                elif valid_scene_videos:
                    # Absolute worst case fallback if Imagen ALSO fails
                    valid_scene_videos.append(valid_scene_videos[-1])
                else:
                    valid_scene_videos.append(None)

        # In case the first scene failed and Imagen failed too
        if any(v is None for v in valid_scene_videos):
            first_valid = next((x for x in valid_scene_videos if x is not None), None)
            if first_valid:
                valid_scene_videos = [first_valid if x is None else x for x in valid_scene_videos]
            else:
                valid_scene_videos = [] # Massive catastrophic failure
        
        video_id = f"gemini_{variant_label}_{int(time.time())}"
        final_path = os.path.join(self.video_dir, f"ad_variant_{variant_label}_{video_id}.mp4")
        
        if valid_scene_videos:
            self.merge_videos(valid_scene_videos, final_path)
            # The method ABOVE does not return a dict, so we construct and return it here
            return {
                "variant": variant_label,
                "label": variant.get("label"),
                "video_id": video_id,
                "status": "completed",
                "local_path": final_path,
                "scenes_count": len(valid_scene_videos),
                "total_scenes": len(storyboard),
                "assets_used": {
                    "product": len(self.assets["product"]),
                    "logo": len(self.assets["logo"]),
                    "lifestyle": len(self.assets["lifestyle"])
                }
            }
        else:
            return {
                "variant": variant_label,
                "label": variant.get("label"),
                "status": "failed",
                "error": "All scene generations failed"
            }

    def generate_output(self, wait_for_render=True) -> Dict:
        """Main entry point for Step 7."""
        if not self.api_key:
            print("   GEMINI_API_KEY not found. Running dry run...")
            return self._generate_dry_run_output()
            
        variant_list = self.variants.get("variants", [])
        render_results = []
        
        for variant in variant_list:
            result = self.render_variant(variant)
            render_results.append(result)
            
        return {
            "campaign_id": self.context.get("campaign_id", "unknown"),
            "renderer": "gemini",
            "model_used": self.DEFAULT_MODEL,
            "total_variants_rendered": len(render_results),
            "platform_specs": {
                "platform": self.context.get("platform", "meta_reels"),
                "aspect_ratio": "9:16",
                "resolution": "1080x1920",
                "format": "mp4"
            },
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
