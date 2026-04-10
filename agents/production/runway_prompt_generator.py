"""
Runway ML / Kling Prompt Generator

Replaces GeminiRenderer for video generation.
Instead of calling an API, generates 2 optimized cinematic prompts
(each ~15 seconds) that the user pastes into RunwayML website.

Merges 6 scenes into 2 continuous prompts:
  - Prompt 1 (Part A): Hook + Problem + Relatable Moment  (~15s)
  - Prompt 2 (Part B): Solution + Trust/Proof + CTA       (~15s)
"""

import json
import os
from typing import Dict, List
from google import genai
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)


class RunwayPromptGenerator:
    """STEP 7: Generates 2 Runway ML / Kling prompts from 6-scene storyboard.

    No video API calls. Outputs 2 copy-paste-ready prompts for manual
    generation on runwayml.com (15 sec each = 30 sec total ad).
    """

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

        self.context = campaign_context

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = None

    async def initialize(self):
        """No async asset loading needed — prompts are text-only output."""
        pass

    # ── Context extraction (reused from GeminiRenderer logic) ──────────

    def _get_scene_context(self) -> Dict:
        product_info = self.context.get("product_understanding", {})
        offer_info = self.context.get("offer_and_risk_reversal", {})
        offers = offer_info.get("offers", [])
        discount = offers[0].get("discount", "") if offers else ""

        gender = self.avatar.get("gender") or self.avatar.get("avatar_preferences", {}).get("gender", "")
        if not gender or str(gender).lower() in ("unknown", "auto"):
            gender = "female"

        language = self.avatar.get("voice_preferences", {}).get("language", "Hindi")
        visual_ctx = self._generate_visual_context()
        person_desc = visual_ctx["person_desc"]

        product_visual = product_info.get("visual_description", "")
        if not product_visual:
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
        }

    def _extract_script_scenes(self) -> List[Dict]:
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

    # ── Visual context generation ──────────────────────────────────────

    def _generate_visual_context(self) -> Dict:
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
            script_block = "(No script available — generate generic actions for: Hook, Problem, Solution, Trust, Proof, CTA)"
            scene_keys_list = ["Hook", "Problem", "Solution", "Trust", "Proof", "CTA"]

        scene_keys_json = ", ".join(f'"{k}": "..."' for k in scene_keys_list)

        prompt = f"""You are a creative director for video ads. Given a product AND the actual script for each scene, generate the visual context for filming.

PRODUCT: {product_name} by {brand_name}
CATEGORY: {category}
DESCRIPTION: {description}
KEY FEATURES: {features_str}
TARGET USER: {target_user}
USER PROBLEM: {user_problem}
BRAND VOICE: {brand_voice}
PRESENTER GENDER: {gender}

=== ACTUAL SCRIPT ===
{script_block}

Generate a JSON object with these fields:

1. "person_desc": A hyper-detailed physical description of the presenter.
   - Must include: exact age, ethnicity (Indian), hair style/color/length, skin tone, facial features, specific clothing with color and fabric.
   - Clothing must be appropriate for the product category and target audience.

2. "setting": A realistic indoor setting where someone would naturally use this product.
   - Must end with: "— lit by {lighting}"
   - Must be a real, specific location with furniture, objects, colors, textures.

3. "scene_actions": A JSON object with one key per scene from the script above.
   Each value is a short action description (1-2 sentences) that MATCHES the voiceover and intent.
   - Actions must involve physical movement.
   - Scenes where product is introduced MUST include "the EXACT product from the reference image".
   - Hook scenes should NOT show the actual product.

4. "per_scene_lighting": A JSON object with ONE consistent lighting setup for ALL scenes.
   - Key "global": one detailed lighting description.

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
                if all(k in result for k in ("person_desc", "setting", "scene_actions")):
                    if "3200K" not in result["setting"]:
                        result["setting"] += f" — lit by {lighting}"
                    if "per_scene_lighting" not in result or "global" not in result.get("per_scene_lighting", {}):
                        result["per_scene_lighting"] = {"global": lighting}
                    self._cached_visual_context = result
                    print(f"     Generated visual context for '{category}' via Gemini Flash")
                    return self._cached_visual_context
        except Exception as e:
            print(f"     Visual context generation failed: {e}. Using fallback.")

        self._cached_visual_context = self._fallback_visual_context(category, gender, product_name, lighting)
        return self._cached_visual_context

    def _fallback_visual_context(self, category: str, gender: str, product_name: str, lighting: str) -> Dict:
        cat = category.lower()

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
        else:
            setting = (f"a clean, well-lit modern Indian home living room with minimal furniture, "
                       f"a small side table, potted plant, warm beige walls — lit by {lighting}")

        if gender.lower() in ("female", "woman", "girl"):
            if any(w in cat for w in ("fitness", "sport", "gym", "yoga")):
                clothing = "wearing a fitted charcoal-grey dry-fit tank top and black leggings"
            elif any(w in cat for w in ("fashion", "apparel", "clothing")):
                clothing = "wearing a casual beige linen top and blue jeans"
            elif any(w in cat for w in ("tech", "electronic", "laptop")):
                clothing = "wearing a navy blue crew-neck sweater"
            else:
                clothing = "wearing a casual white crew-neck cotton t-shirt with no print"
            person_desc = (
                "a 26-year-old Indian woman with straight jet-black hair past her shoulders, "
                "warm light-brown skin, soft oval face, dark brown eyes, "
                f"{clothing}"
            )
        else:
            if any(w in cat for w in ("fitness", "sport", "gym", "yoga")):
                clothing = "wearing a grey dri-fit crew-neck t-shirt and black joggers"
            elif any(w in cat for w in ("fashion", "apparel", "clothing")):
                clothing = "wearing a fitted olive green henley t-shirt and dark jeans"
            elif any(w in cat for w in ("tech", "electronic", "laptop")):
                clothing = "wearing a plain charcoal crew-neck sweater"
            else:
                clothing = "wearing a casual white crew-neck cotton t-shirt with no print"
            person_desc = (
                "a 28-year-old Indian man with short neatly-trimmed black hair, clean-shaven, "
                "warm light-brown skin, angular jawline, dark brown eyes, "
                f"{clothing}"
            )

        scene_actions = {
            "Hook": "stands facing camera with both hands at sides, looks frustrated, raises right hand to gesture while speaking",
            "Problem": "stands near a shelf, picks up an item, shakes head in disappointment, turns to camera",
            "Relatable Moment": "stands with both hands relaxed, pauses thoughtfully, turns to camera and speaks naturally",
            "Solution": f"reaches for {product_name} on the counter, picks it up and holds toward camera with excitement",
            "Trust": "stands facing camera, gestures confidently with right hand while speaking, nods with conviction",
            "Proof": f"holds {product_name} in left hand, demonstrates using it naturally while smiling at camera",
            "CTA": f"holds {product_name} forward toward camera with both hands, speaks with energy and urgency",
        }

        return {"person_desc": person_desc, "setting": setting, "scene_actions": scene_actions, "per_scene_lighting": {"global": lighting}}

    # ── Scene grouping: 6 scenes -> 2 merged groups ───────────────────

    def _group_scenes(self, storyboard: List[Dict]) -> tuple:
        """Splits storyboard into 2 groups for 2x 15-sec Runway prompts.

        Group A (emotional setup): Hook, Problem, Relatable Moment
        Group B (product payoff):  Solution, Trust/Proof, CTA

        If scene names don't match exactly (LLM generates creative names),
        splits by index: first half → Group A, second half → Group B.
        """
        emotional_names = {"hook", "problem", "relatable moment", "relatable", "agitate pain", "stop scroll"}
        payoff_names = {"solution", "trust", "proof", "cta", "introduce product", "show results", "drive action", "build credibility"}

        group_a = []
        group_b = []

        for scene in storyboard:
            name = scene.get("scene", "").lower().strip()
            if name in emotional_names:
                group_a.append(scene)
            elif name in payoff_names:
                group_b.append(scene)
            else:
                # Unknown scene name — assign by position
                if len(group_a) <= len(group_b):
                    group_a.append(scene)
                else:
                    group_b.append(scene)

        # Fallback: if grouping failed, split by index
        if not group_a or not group_b:
            mid = len(storyboard) // 2
            group_a = storyboard[:mid]
            group_b = storyboard[mid:]

        return group_a, group_b

    # ── Runway ML prompt building ─────────────────────────────────────

    def _build_runway_prompt(self, scenes: List[Dict], part_label: str, ctx: Dict, visual_ctx: Dict) -> str:
        """Builds a single Runway ML / Kling prompt from merged scenes.

        Runway works best with:
        - Continuous cinematic description (not scene-by-scene cuts)
        - Detailed character + setting description upfront
        - Natural action flow with camera movement
        - 15 seconds of coherent, filmable action
        """
        person = visual_ctx["person_desc"]
        setting = visual_ctx["setting"]
        actions = visual_ctx.get("scene_actions", {})
        lighting = visual_ctx.get("per_scene_lighting", {}).get(
            "global", "soft diffused overhead LED panels, warm 3200K, even illumination"
        )

        # Collect voiceovers and actions for all scenes in this group
        action_parts = []
        voiceover_parts = []
        for scene in scenes:
            scene_name = scene.get("scene", "")
            vo = scene.get("voiceover", "")
            action = actions.get(scene_name, "")
            if vo:
                voiceover_parts.append(vo)
            if action:
                action_parts.append(action)

        # Build the merged action narrative
        if action_parts:
            merged_actions = ". Then, ".join(action_parts)
        else:
            merged_actions = "interacts naturally with the environment, speaking directly to camera"

        # Determine camera movement flow based on part
        if part_label == "A":
            camera = "Slow dolly-in transitioning to handheld close-up, then settling into a steady medium shot"
        else:
            camera = "Smooth tracking shot transitioning to steadicam medium, ending with a confident push-in"

        # Build the Runway-optimized prompt
        prompt_lines = [
            f"Cinematic 15-second vertical video (9:16 aspect ratio). ",
            f"{person} in {setting}. ",
            f"{merged_actions}. ",
            f"Camera: {camera}. ",
            f"Lighting: {lighting}. ",
            f"Shot on 35mm film, shallow depth of field, skin texture visible, photorealistic. ",
            f"The person speaks directly to camera with natural expressions and gestures throughout. ",
        ]

        # Add product reference for Part B
        if part_label == "B":
            product_name = ctx["product_name"]
            prompt_lines.append(
                f"The product ({product_name}) appears naturally — same packaging, colors, and branding as the reference image. "
            )
            if ctx.get("discount"):
                prompt_lines.append(f"Urgency moment mentioning: {ctx['discount']}. ")

        # Negative guidance
        prompt_lines.append(
            "AVOID: blurry, distorted face, extra fingers, deformed hands, cartoon, anime, CGI, "
            "text overlay, watermark, caption, subtitle, plastic skin, harsh sunlight, jump cuts."
        )

        return "".join(prompt_lines)

    def _build_runway_prompt_llm(self, scenes: List[Dict], part_label: str, ctx: Dict, visual_ctx: Dict) -> str:
        """Uses Gemini Flash to craft a polished Runway ML prompt from merged scenes."""
        person = visual_ctx["person_desc"]
        setting = visual_ctx["setting"]
        actions = visual_ctx.get("scene_actions", {})
        lighting = visual_ctx.get("per_scene_lighting", {}).get(
            "global", "soft diffused overhead LED panels, warm 3200K"
        )

        # Build scene details block
        scene_details = []
        for scene in scenes:
            name = scene.get("scene", "")
            vo = scene.get("voiceover", "")
            intent = scene.get("intent", "")
            action = actions.get(name, "natural gesture while speaking")
            scene_details.append(f"- {name}: Action: {action} | Voiceover: \"{vo}\" | Intent: {intent}")

        scenes_block = "\n".join(scene_details)

        if part_label == "A":
            part_desc = "EMOTIONAL SETUP — Hook the viewer, show the problem, build relatability. NO product shown yet."
            camera_guide = "Start with a slow dolly-in, transition to handheld close-up for emotional intensity, settle into a steady medium shot."
        else:
            part_desc = f"PRODUCT PAYOFF — Reveal {ctx['product_name']}, build trust, and close with a strong CTA."
            camera_guide = "Start with a smooth tracking shot for the product reveal, transition to steadicam medium for trust, end with a confident push-in for CTA."

        llm_prompt = f"""You are an expert prompt engineer for Runway ML and Kling AI video generation platforms.

Write ONE single cinematic prompt that merges these scenes into a continuous 15-second vertical video (9:16).

=== CHARACTER (must appear IDENTICALLY throughout) ===
{person}

=== SETTING (SAME throughout) ===
{setting}

=== LIGHTING ===
{lighting}

=== PART {part_label}: {part_desc} ===
SCENES TO MERGE:
{scenes_block}

=== CAMERA FLOW ===
{camera_guide}

=== RUNWAY ML PROMPT RULES ===
1. Write as ONE continuous cinematic paragraph — NO scene labels, NO timestamps, NO numbered steps.
2. Start with the full character description and setting, then flow into the action naturally.
3. Describe a SINGLE continuous 15-second take — the action flows from one beat to the next without cuts.
4. Include specific camera movements that transition smoothly.
5. Include lighting description.
6. The character speaks directly to camera throughout with natural expressions.
7. End with film quality cues: "Shot on 35mm film, shallow depth of field, photorealistic, skin texture visible."
8. {"The product must NOT appear in this part — it is the emotional setup before the reveal." if part_label == "A" else f"The product ({ctx['product_name']}) must appear naturally with EXACT packaging from the reference image."}
9. Add AVOID line at the end: "AVOID: blurry, distorted face, extra fingers, deformed hands, cartoon, anime, CGI, text overlay, watermark, subtitle, plastic skin, harsh sunlight, jump cuts."
10. Keep it under 200 words — Runway works best with concise, dense prompts.
{f'11. Include urgency mentioning: {ctx["discount"]}.' if part_label == "B" and ctx.get("discount") else ""}

Return ONLY the prompt text. No JSON, no explanation, no quotes around it."""

        try:
            if self.client:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=llm_prompt,
                )
                result = response.text.strip().strip('"').strip("'")
                if len(result) > 50:
                    print(f"     Generated Runway prompt Part {part_label} via Gemini Flash ({len(result)} chars)")
                    return result
        except Exception as e:
            print(f"     LLM prompt generation failed for Part {part_label}: {e}. Using fallback.")

        # Fallback to template-based prompt
        return self._build_runway_prompt(scenes, part_label, ctx, visual_ctx)

    # ── Main output ───────────────────────────────────────────────────

    async def generate_variant_prompts(self, variant: Dict) -> Dict:
        """Generates 2 Runway ML prompts for a single variant."""
        variant_label = variant.get("variant", "A")
        storyboard = variant.get("storyboard") or variant.get("scenes") or []
        print(f"\n   Processing Variant {variant_label} for Runway ML prompts...")

        if not storyboard:
            return {
                "variant": variant_label,
                "status": "failed",
                "error": "Empty storyboard",
            }

        ctx = self._get_scene_context()
        visual_ctx = self._generate_visual_context()
        group_a, group_b = self._group_scenes(storyboard)

        print(f"     Part A scenes ({len(group_a)}): {[s.get('scene') for s in group_a]}")
        print(f"     Part B scenes ({len(group_b)}): {[s.get('scene') for s in group_b]}")

        # Generate prompts (try LLM first, fallback to template)
        prompt_a = self._build_runway_prompt_llm(group_a, "A", ctx, visual_ctx)
        prompt_b = self._build_runway_prompt_llm(group_b, "B", ctx, visual_ctx)

        return {
            "variant": variant_label,
            "label": variant.get("label", ""),
            "status": "completed",
            "platform": "runway_ml",
            "instructions": "Copy each prompt into RunwayML website. Generate 2 videos (15 sec each), then join them for a 30-sec ad.",
            "prompts": {
                "part_a": {
                    "label": "Part A — Emotional Setup (15 sec)",
                    "scenes_merged": [s.get("scene") for s in group_a],
                    "prompt": prompt_a,
                },
                "part_b": {
                    "label": "Part B — Product Payoff (15 sec)",
                    "scenes_merged": [s.get("scene") for s in group_b],
                    "prompt": prompt_b,
                },
            },
            "visual_context": {
                "person_description": visual_ctx["person_desc"],
                "setting": visual_ctx["setting"],
                "lighting": visual_ctx.get("per_scene_lighting", {}).get("global", ""),
            },
        }

    async def generate_output(self, wait_for_render=True) -> Dict:
        """Main entry point — replaces GeminiRenderer.generate_output()."""
        variant_list = self.variants.get("variants", [])
        render_results = []

        for variant in variant_list:
            result = await self.generate_variant_prompts(variant)
            render_results.append(result)

        return {
            "campaign_id": self.context.get("campaign_id", "unknown"),
            "renderer": "runway_ml",
            "total_variants": len(render_results),
            "render_results": render_results,
        }
