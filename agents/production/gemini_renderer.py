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

        # Hook/Problem scenes: product as SUBJECT anchor for visual consistency
        # (not shown as product in scene, but anchors Veo's lighting/color/style)
        if scene_name in ("Hook", "Problem", "Relatable Moment", "Stop scroll", "Agitate pain"):
            if product_ids:
                img = await self._load_image_for_veo(product_ids[0])
                if img:
                    references.append(types.VideoGenerationReferenceImage(
                        image=img, reference_type="ASSET"
                    ))
                    print(f"       Using product image {product_ids[0]} as style anchor for scene '{scene_name}'")

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
            gender = "female"

        language = self.avatar.get("voice_preferences", {}).get("language", "Hindi")

        # Get dynamic person description from LLM based on product category/target audience
        # Cached — same person across all scenes for identity lock
        visual_ctx = self._generate_visual_context()
        person_desc = visual_ctx["person_desc"]

        # Build a visual description of the product from uploaded images context
        # so Veo preserves the EXACT appearance instead of reimagining it
        product_visual = product_info.get("visual_description", "")
        if not product_visual:
            # Compose from available fields: packaging color, shape, label details
            parts = []
            if product_info.get("product_name"):
                parts.append(product_info["product_name"])
            if product_info.get("packaging"):
                parts.append(product_info["packaging"])
            if product_info.get("color"):
                parts.append(f"{product_info['color']} colored packaging")
            if product_info.get("description"):
                parts.append(product_info["description"])
            product_visual = ", ".join(parts) if parts else ""

        return {
            "product_name": product_info.get("product_name") or self.context.get("product_name", "the product"),
            "brand": product_info.get("brand_name") or self.context.get("brand_name", "the brand"),
            "category": product_info.get("category", "consumer product"),
            "features": product_info.get("features", []),
            "description": product_info.get("description", ""),
            "product_visual": product_visual,
            "user_problem": self.context.get("user_problem_raw", "a common problem"),
            "brand_voice": self.context.get("brand_voice", "premium"),
            "language": language,
            "gender": gender,
            "person_desc": person_desc,
            "discount": discount,
            "guarantee": guarantee,
        }

    def _extract_script_scenes(self) -> List[Dict]:
        """Extracts scene scripts from variants storyboard for visual context generation."""
        variants = self.variants.get("variants", [])
        if not variants:
            return []
        storyboard = variants[0].get("storyboard") or variants[0].get("scenes") or []
        scenes = []
        for s in storyboard:
            scenes.append({
                "scene": s.get("scene", ""),
                "voiceover": s.get("voiceover", ""),
                "intent": s.get("intent", ""),
                "visual_continuity": s.get("visual_continuity", ""),
            })
        return scenes

    def _generate_visual_context(self) -> Dict:
        """Generates product-appropriate person, setting, and scene actions via Gemini Flash.

        Uses the ACTUAL script (voiceover, intent, visual_continuity) from each scene
        so that visual actions, setting, and lighting match the narrative flow.
        Called once and cached for identity + environment lock.
        """
        if hasattr(self, '_cached_visual_context'):
            return self._cached_visual_context

        product_info = self.context.get("product_understanding", {})
        category = product_info.get("category", "consumer product")
        product_name = product_info.get("product_name", "the product")
        brand_name = product_info.get("brand_name", "the brand")
        description = product_info.get("description", "")
        target_user = product_info.get("target_user", "")
        features = product_info.get("features", [])
        user_problem = self.context.get("user_problem_raw", "a common problem")
        brand_voice = self.context.get("brand_voice", "premium")

        gender = self.avatar.get("gender") or self.avatar.get("avatar_preferences", {}).get("gender", "")
        if not gender or str(gender).lower() in ("unknown", "auto"):
            gender = "female"

        features_str = ", ".join(features[:5]) if features else "not specified"
        lighting = ("soft diffused overhead LED panels giving even, warm-toned (3200K) "
                     "studio lighting with NO harsh shadows and NO direct sunlight")

        # Extract actual script scenes for context-aware visual generation
        script_scenes = self._extract_script_scenes()
        script_block = ""
        scene_keys_list = []
        if script_scenes:
            lines = []
            for s in script_scenes:
                key = s["scene"]
                scene_keys_list.append(key)
                lines.append(
                    f'- {key}:\n'
                    f'    Voiceover: "{s["voiceover"]}"\n'
                    f'    Intent: {s["intent"]}\n'
                    f'    Visual hint: {s["visual_continuity"]}'
                )
            script_block = "\n".join(lines)
        else:
            script_block = "(No script available — generate generic actions for: Hook, Problem, Solution, Trust, Proof, CTA, Relatable Moment)"
            scene_keys_list = ["Hook", "Problem", "Solution", "Trust", "Proof", "CTA", "Relatable Moment"]

        scene_keys_json = ", ".join(f'"{k}": "..."' for k in scene_keys_list)

        prompt = f"""You are a creative director for video ads. Given a product AND the actual script for each scene, generate the visual context for filming. The visuals MUST match what the presenter is saying in each scene.

PRODUCT: {product_name} by {brand_name}
CATEGORY: {category}
DESCRIPTION: {description}
KEY FEATURES: {features_str}
TARGET USER: {target_user}
USER PROBLEM: {user_problem}
BRAND VOICE: {brand_voice}
PRESENTER GENDER: {gender}

=== ACTUAL SCRIPT (each scene's dialogue, intent, and visual direction) ===
{script_block}

Generate a JSON object with these fields:

1. "person_desc": A hyper-detailed physical description of the presenter for Veo identity lock.
   - Must include: exact age, ethnicity (Indian), hair style/color/length, skin tone, facial features (eye color, face shape), specific clothing with color and fabric.
   - Clothing must be appropriate for the product category and target audience.
   - Example for fitness product: "a 24-year-old Indian woman with long black hair in a high ponytail, warm brown skin, sharp cheekbones, dark brown eyes, wearing a fitted charcoal-grey dry-fit tank top and black leggings"
   - Example for tech product: "a 27-year-old Indian man with short wavy black hair, light brown skin, clean-shaven, rectangular glasses, dark brown eyes, wearing a navy blue henley t-shirt"

2. "setting": A realistic indoor setting where someone would naturally use this product.
   - Must end with: "— lit by {lighting}"
   - Must be a real, specific location (not generic). Include furniture, objects, colors, textures.
   - Match the product category: skincare→bathroom, electronics→desk/office, food→kitchen, fitness→living room with equipment, fashion→bedroom, etc.
   - Example for fitness: "a bright modern Indian apartment living room with a yoga mat on hardwood floor, a small rack of dumbbells, a water bottle on a side table, light grey walls with a motivational frame — lit by {lighting}"

3. "scene_actions": A JSON object with one key per scene from the script above.
   Each value is a short action description (1-2 sentences) that MATCHES the voiceover and intent of that scene.
   - READ the voiceover for each scene and design the physical action to complement what is being said.
   - Actions must involve physical movement (gesturing, picking up, turning, stepping, using).
   - Scenes where the product is introduced/shown MUST include the phrase "the EXACT product from the reference image".
   - Hook-type scenes (curiosity/attention) should NOT show the actual product.
   - The emotion in the action must match the emotion in the voiceover (frustration, excitement, confidence, urgency, etc.)
   - Actions must be realistic for how someone actually uses/interacts with this product category.
   - Do NOT use skincare-specific actions (applying on face, squeezing onto palm) unless the product IS skincare.

4. "per_scene_lighting": A JSON object with ONE consistent lighting setup for ALL scenes.
   - Key "global": one detailed lighting description that works for the setting.
   - Must include: light source type, color temperature, shadow quality, ambient fill.
   - This SAME lighting applies to every scene for visual consistency.
   - Example: "two soft diffused overhead LED panels at 3200K, warm ambient fill from a table lamp, even illumination with soft shadows, no direct sunlight"

Return ONLY valid JSON, no explanation.
{{
  "person_desc": "...",
  "setting": "...",
  "scene_actions": {{ {scene_keys_json} }},
  "per_scene_lighting": {{ "global": "..." }}
}}"""

        try:
            if self.client:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config={'response_mime_type': 'application/json'}
                )
                result = json.loads(response.text)

                # Validate required keys
                if all(k in result for k in ("person_desc", "setting", "scene_actions")):
                    # Ensure lighting is in setting
                    if "3200K" not in result["setting"]:
                        result["setting"] += f" — lit by {lighting}"
                    # Ensure per_scene_lighting exists with global key
                    if "per_scene_lighting" not in result or "global" not in result.get("per_scene_lighting", {}):
                        result["per_scene_lighting"] = {"global": lighting}
                    self._cached_visual_context = result
                    print(f"     Generated script-aware visual context for '{category}' via Gemini Flash")
                    return self._cached_visual_context
        except Exception as e:
            print(f"     Visual context generation failed: {e}. Using category fallback.")

        # Fallback: category-based mapping
        self._cached_visual_context = self._fallback_visual_context(category, gender, product_name, lighting)
        return self._cached_visual_context

    def _fallback_visual_context(self, category: str, gender: str, product_name: str, lighting: str) -> Dict:
        """Category-based fallback when LLM visual context generation fails."""
        cat = category.lower()

        # Category to setting mapping
        if any(w in cat for w in ("skin", "beauty", "cosmetic", "personal care", "grooming")):
            setting = (f"a cozy Indian home bathroom with warm beige walls, a wooden shelf with toiletries, "
                       f"a round mirror above a white ceramic sink — lit by {lighting}")
        elif any(w in cat for w in ("laptop", "phone", "electronic", "tech", "computer", "gadget", "software")):
            setting = (f"a modern Indian home office with a clean wooden desk, a monitor, potted plant, "
                       f"warm grey walls, a cushioned desk chair — lit by {lighting}")
        elif any(w in cat for w in ("food", "beverage", "drink", "snack", "nutrition", "supplement", "vitamin")):
            setting = (f"a bright Indian home kitchen with white marble countertop, wooden cabinets, "
                       f"a fruit bowl, ceramic jars, warm cream walls — lit by {lighting}")
        elif any(w in cat for w in ("fitness", "sport", "gym", "running", "shoe", "athletic", "yoga")):
            setting = (f"a modern Indian apartment living room with a yoga mat on hardwood floor, "
                       f"small rack of dumbbells, water bottle on a side table, light grey walls — lit by {lighting}")
        elif any(w in cat for w in ("fashion", "apparel", "clothing", "wear", "accessory", "jewel")):
            setting = (f"a stylish Indian bedroom with a full-length mirror, wooden wardrobe, "
                       f"a neatly made bed with neutral linen, warm beige walls — lit by {lighting}")
        elif any(w in cat for w in ("auto", "car", "bike", "vehicle", "motor")):
            setting = (f"a clean Indian home garage with concrete floor, tool rack on wall, "
                       f"a workbench with car accessories, warm grey walls — lit by {lighting}")
        else:
            setting = (f"a clean, well-lit modern Indian home living room with minimal furniture, "
                       f"a small side table, potted plant, warm beige walls — lit by {lighting}")

        # Person description — category-appropriate clothing
        if gender.lower() in ("female", "woman", "girl"):
            if any(w in cat for w in ("fitness", "sport", "gym", "running", "yoga", "athletic")):
                clothing = "wearing a fitted charcoal-grey dry-fit tank top and black leggings"
            elif any(w in cat for w in ("fashion", "apparel", "clothing")):
                clothing = "wearing a casual beige linen top and blue jeans"
            elif any(w in cat for w in ("tech", "electronic", "laptop", "software")):
                clothing = "wearing a navy blue crew-neck sweater"
            else:
                clothing = "wearing a casual white crew-neck cotton t-shirt with no print"
            person_desc = (
                "a 26-year-old Indian woman with straight jet-black hair past her shoulders, "
                "warm light-brown skin, soft oval face, dark brown eyes, "
                f"{clothing}"
            )
        else:
            if any(w in cat for w in ("fitness", "sport", "gym", "running", "yoga", "athletic")):
                clothing = "wearing a grey dri-fit crew-neck t-shirt and black joggers"
            elif any(w in cat for w in ("fashion", "apparel", "clothing")):
                clothing = "wearing a fitted olive green henley t-shirt and dark jeans"
            elif any(w in cat for w in ("tech", "electronic", "laptop", "software")):
                clothing = "wearing a plain charcoal crew-neck sweater"
            else:
                clothing = "wearing a casual white crew-neck cotton t-shirt with no print"
            person_desc = (
                "a 28-year-old Indian man with short neatly-trimmed black hair, clean-shaven with no beard, "
                "warm light-brown skin, angular jawline, dark brown eyes, "
                f"{clothing}"
            )

        scene_actions = {
            "Hook": "stands in the space, looks around with a mildly frustrated expression, then turns to camera and gestures with hands while speaking",
            "Problem": "picks up a generic item from nearby, shakes head in disappointment, puts it down and turns to camera speaking emotionally",
            "Solution": f"reaches for the EXACT product from the reference image ({product_name}), picks it up with both hands and holds it toward camera with genuine excitement",
            "Trust": "gestures confidently while speaking about results, nods with conviction",
            "Proof": f"uses the EXACT product from the reference image ({product_name}) naturally while looking at camera with a genuine smile",
            "CTA": f"holds the EXACT product from the reference image ({product_name}) forward toward camera, speaks with energy and urgency",
            "Relatable Moment": "pauses in the space, looks thoughtful, then turns to camera to speak naturally and casually",
        }

        print(f"     Using category fallback visual context for '{category}'")
        return {"person_desc": person_desc, "setting": setting, "scene_actions": scene_actions, "per_scene_lighting": {"global": lighting}}

    def _transliterate_hindi(self, text: str) -> str:
        """Converts Hindi/Devanagari text to phonetic Roman script for Veo audio.

        Veo 3.1 generates better Hindi pronunciation when given romanized text
        (e.g. "aapki skin dull lag rahi hai?" instead of Devanagari).
        Uses Gemini Flash for accurate transliteration.
        """
        if not text or not any('\u0900' <= ch <= '\u097F' for ch in text):
            return text  # Already Roman or no Hindi chars

        try:
            if self.client:
                resp = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=(
                        f"Transliterate this Hindi/Hinglish text to phonetic Roman script "
                        f"(how it sounds when spoken). Keep English words as-is. "
                        f"Output ONLY the transliterated text, nothing else.\n\n{text}"
                    ),
                )
                result = resp.text.strip().strip('"').strip("'")
                if result:
                    return result
        except Exception as e:
            print(f"       Transliteration failed: {e}")

        return text  # Return original if transliteration fails

    def _generate_scene_prompts(self, scene_list: List[Dict]) -> Dict[str, str]:
        """Uses Gemini Flash to generate Veo prompts with CONSISTENT person identity.

        Key principles:
        - SAME detailed person description in EVERY scene (identity lock)
        - SAME setting/environment across scenes (visual continuity)
        - Physical movement in every scene
        - Specific cinematic camera language
        """
        if hasattr(self, '_cached_scene_prompts'):
            return self._cached_scene_prompts

        ctx = self._get_scene_context()
        person = ctx["person_desc"]

        # Dynamic setting, actions, and lighting from script-aware visual context
        visual_ctx = self._generate_visual_context()
        setting = visual_ctx["setting"]
        actions = visual_ctx["scene_actions"]
        lighting = visual_ctx.get("per_scene_lighting", {}).get(
            "global", "soft diffused overhead LED panels, warm 3200K, even illumination, no harsh shadows"
        )

        prompt = f"""You are a cinematographer writing video prompts for Google Veo 3.1.

PRODUCT: {ctx['product_name']} by {ctx['brand']} ({ctx['category']})
PRODUCT VISUAL APPEARANCE: {ctx['product_visual'] if ctx['product_visual'] else ctx['product_name'] + ' — match the reference image EXACTLY, same packaging, same colors, same label'}
PROBLEM IT SOLVES: {ctx['user_problem']}
PRESENTER (SAME person in ALL scenes): {person}
SETTING (SAME in ALL scenes): {setting}
LIGHTING (SAME in ALL scenes): {lighting}

=== ABSOLUTE RULES ===
1. EVERY prompt MUST start with EXACT person description: "{person}"
2. EVERY prompt MUST include EXACT setting: "{setting}"
3. EVERY prompt MUST include EXACT lighting: "{lighting}"
4. Each prompt: 2-3 sentences MAX
5. EVERY scene has physical movement (gesturing, picking up, turning, stepping)
6. ONE camera move per scene (dolly, tracking, push-in, steadicam)
7. The person speaks directly to camera
8. NEVER mention sunlight, window light, or natural light — ONLY soft overhead LED panels
9. NEVER say "same person" — just describe them identically each time
10. When the product appears (Solution, Proof, CTA scenes), describe it EXACTLY as the reference image — same packaging shape, same colors, same label design, same brand logo placement. Do NOT reimagine or alter the product appearance.
11. AVOID: blurry, distorted face, extra fingers, deformed hands, cartoon, anime, CGI, 3D render, text overlay, watermark, caption, subtitle, plastic skin, harsh sunlight

Write prompts for ONLY these scenes:

HOOK: {person} in {setting}. {actions.get('Hook', 'Turns to camera with a concerned expression, gestures with hands while speaking')}. Slow dolly-in, {lighting}.

PROBLEM: {person} in {setting}. {actions.get('Problem', 'Picks up a generic item, shakes head in frustration, turns to camera speaking emotionally')}. Handheld close-up, {lighting}.

SOLUTION: {person} in {setting}. {actions.get('Solution', f'Reaches for the EXACT product from the reference image ({ctx["product_name"]}), picks it up and holds toward camera with excitement')} — the product must match the reference image exactly in shape, color, and branding. Tracking shot, {lighting}.

TRUST: {person} in {setting}. {actions.get('Trust', 'Gestures confidently while speaking about results, nods with conviction')}. Steadicam medium shot, {lighting}.

PROOF: {person} in {setting}. {actions.get('Proof', f'Uses the EXACT product from the reference image ({ctx["product_name"]}), interacts with it naturally while looking at camera with a genuine smile')} — product packaging and label must be identical to the reference image. Close-up tracking shot, {lighting}.

CTA: {person} in {setting}. {actions.get('CTA', f'Holds the EXACT product from the reference image ({ctx["product_name"]}) forward toward camera, speaks with energy and urgency')} — product must visually match the reference image exactly. {"Mentions: " + ctx['discount'] + ". " if ctx['discount'] else ""}Push-in shot, {lighting}.

RELATABLE MOMENT: {person} in {setting}. {actions.get('Relatable Moment', 'Pauses thoughtfully, then turns to camera to speak naturally and casually')}. Handheld shot, {lighting}.

Return ONLY valid JSON:
{{
  "Hook": "prompt starting with person description and setting...",
  "Problem": "prompt starting with person description and setting...",
  "Solution": "prompt starting with person description and setting...",
  "Trust": "prompt starting with person description and setting...",
  "Proof": "prompt starting with person description and setting...",
  "CTA": "prompt starting with person description and setting...",
  "Relatable Moment": "prompt starting with person description and setting..."
}}"""

        try:
            if self.client:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config={'response_mime_type': 'application/json'}
                )
                self._cached_scene_prompts = json.loads(response.text)
                # Verify identity lock: ensure person_desc appears in each prompt
                for key, val in self._cached_scene_prompts.items():
                    if person[:30] not in val:
                        # Prepend if Gemini omitted it
                        self._cached_scene_prompts[key] = f"{person} " + val
                print(f"     Generated {len(self._cached_scene_prompts)} identity-locked scene prompts via Gemini")
                return self._cached_scene_prompts
        except Exception as e:
            print(f"     LLM scene prompt generation failed: {e}. Using fallback.")

        # Fallback: use dynamic visual context (already category-appropriate)
        fb_light = lighting
        pname = ctx["product_name"]
        default_solution = f"Reaches for the EXACT product from the reference image ({pname}), picks it up and holds toward camera with excitement"
        default_proof = f"Uses the EXACT product from the reference image ({pname}), interacts naturally while looking at camera with a genuine smile"
        default_cta = f"Holds the EXACT product from the reference image ({pname}) forward toward camera, speaks with energy"
        discount_mention = f"Mentions: {ctx['discount']}." if ctx["discount"] else ""

        self._cached_scene_prompts = {
            "Hook": f"{person} in {setting}. {actions.get('Hook', 'Turns to camera with a concerned expression, gestures with hands while speaking')}. Slow dolly-in, 50mm lens, {fb_light}.",
            "Problem": f"{person} in {setting}. {actions.get('Problem', 'Picks up a generic item, shakes head in frustration, turns to camera speaking emotionally')}. Handheld close-up, {fb_light}.",
            "Solution": f"{person} in {setting}. {actions.get('Solution', default_solution)} — product must match reference image exactly in packaging, color, and branding. Smooth tracking shot, {fb_light}.",
            "Trust": f"{person} in {setting}. {actions.get('Trust', 'Gestures confidently, nods with conviction')}. Steadicam medium shot, {fb_light}.",
            "Proof": f"{person} in {setting}. {actions.get('Proof', default_proof)} — product packaging must be identical to reference image. Close-up tracking shot, {fb_light}.",
            "CTA": f"{person} in {setting}. {actions.get('CTA', default_cta)} — product must visually match reference image. {discount_mention} Push-in shot, {fb_light}.",
            "Relatable Moment": f"{person} in {setting}. {actions.get('Relatable Moment', 'Pauses thoughtfully, then turns to camera to speak naturally')}. Handheld shot, {fb_light}."
        }
        return self._cached_scene_prompts

    def _build_prompt(self, scene: Dict) -> str:
        """Builds a Veo prompt with identity lock, transliterated dialogue, and realism cues."""
        scene_name = scene.get("scene", "")
        directives = scene.get("realistic_directives", "")
        copy_text = scene.get("voiceover", "")
        language = self.avatar.get("voice_preferences", {}).get("language", "Hindi")

        # Get dynamically generated scene prompts (identity-locked)
        storyboard = []
        variants = self.variants.get("variants", [])
        if variants:
            storyboard = variants[0].get("storyboard", [])
        scene_prompts = self._generate_scene_prompts(storyboard)

        ctx = self._get_scene_context()
        person = ctx["person_desc"]

        visual_ctx = self._generate_visual_context()
        dynamic_setting = visual_ctx["setting"]
        dynamic_lighting = visual_ctx.get("per_scene_lighting", {}).get(
            "global", "soft diffused overhead LED panels, warm 3200K, even illumination, no harsh shadows"
        )

        prompt = scene_prompts.get(scene_name,
            f"{person} in {dynamic_setting}. Presents a product to camera. "
            f"50mm lens, {dynamic_lighting}."
        )

        # Ensure identity lock — prepend person description if missing
        if person[:30] not in prompt:
            prompt = f"{person}. " + prompt

        # Transliterate Hindi dialogue to Roman script for better Veo pronunciation
        if copy_text:
            roman_text = self._transliterate_hindi(copy_text)
            pronoun = "She" if ctx["gender"].lower() in ("female", "woman", "girl") else "He"
            prompt += f' {pronoun} speaks naturally in {language} and says: "{roman_text}"'

        # Quality suffix — consistent lighting from visual context + realism + NO text overlays
        # Negative prompt is embedded in text because Veo config may strip it when reference images are used
        prompt += (
            f" Filmed on 35mm film with Fujifilm X-T5, 56mm f/1.2 lens. "
            f"{dynamic_lighting}. "
            f"Skin texture visible, real indoor environment. "
            f"The product shown must EXACTLY match the reference image — same packaging, colors, label, and branding. "
            f"Do NOT replace, alter, or reimagine the product design. "
            f"AVOID: blurry, low quality, distorted face, extra fingers, deformed hands, cartoon, anime, "
            f"CGI, 3D render, text overlay, watermark, logo overlay, caption, subtitle, plastic skin, "
            f"uncanny valley, bad anatomy, harsh sunlight, direct sunlight, window light, lens flare, "
            f"dark shadows, high contrast lighting, overexposed, underexposed, "
            f"different product, generic product, wrong packaging, altered brand label."
        )

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

            NEGATIVE_PROMPT = (
                "blurry, low quality, distorted face, extra fingers, "
                "deformed hands, cartoon, anime, CGI, 3D render, "
                "text overlay, watermark, logo, caption, subtitle, "
                "plastic skin, uncanny valley, bad anatomy, static image, "
                "harsh sunlight, direct sunlight, window light, lens flare, "
                "dark shadows, high contrast lighting, overexposed, underexposed, "
                "different product, generic product, wrong packaging, altered brand label"
            )

            config = None

            if reference_images:
                # With reference images: NO person_generation (not supported with refs)
                # Negative prompt is already embedded in the text prompt for coverage
                config = types.GenerateVideosConfig(
                    number_of_videos=1,
                    duration_seconds=duration_sec,
                    aspect_ratio="9:16",
                    reference_images=reference_images,
                    negative_prompt=NEGATIVE_PROMPT,
                )
            else:
                config = types.GenerateVideosConfig(
                    number_of_videos=1,
                    duration_seconds=duration_sec,
                    aspect_ratio="9:16",
                    person_generation="allow_all",
                    negative_prompt=NEGATIVE_PROMPT,
                )

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
        FADE = 1.2  # Longer crossfade for smoother scene transitions

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
