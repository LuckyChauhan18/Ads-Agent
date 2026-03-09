"""Prompt building mixin for GeminiRenderer.

Handles LLM-driven scene prompt generation and per-scene Veo prompt construction.
"""
import json
import os
import sys
from typing import Dict, List

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from utils.logger import logger


class PromptBuilderMixin:
    """Mixin: generates D2C cinematic prompts for Veo scene generation."""

    def _generate_scene_prompts(self, scene_list: List[Dict], variant_id: str = "") -> Dict[str, str]:
        """Uses Gemini Flash to generate product-specific cinematic prompts for Veo.
        
        Dynamically generates prompts for ALL scene names (including custom ones).
        Caches per variant to prevent cross-variant pollution.
        """
        cache_key = f"_cached_prompts_{variant_id}"
        if hasattr(self, cache_key):
            return getattr(self, cache_key)
        
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
        
        offer_info = self.context.get("offer_and_risk_reversal", {})
        offers = offer_info.get("offers", [])
        
        discount = offers[0].get("discount", "") if offers else ""
        guarantee = offers[0].get("guarantee", "") if offers else ""
        trust_signals = self.context.get("trust_signals", [])
        reviews_text = trust_signals[0] if trust_signals else ""
        
        discount_msg = f"'{discount}'" if discount else ""
        guarantee_msg = f"'{guarantee}'" if guarantee else ""
        offer_statement = f"announces {discount_msg} {guarantee_msg}" if (discount_msg or guarantee_msg) else "speaks enthusiastically"
        
        gender = self.avatar.get("gender") or self.avatar.get("avatar_preferences", {}).get("gender", "young Indian person")
        style = self.avatar.get("style") or self.avatar.get("avatar_preferences", {}).get("style", "cinematic")
        
        if not gender or str(gender).lower() in ("unknown", "auto"): 
            gender = "young Indian person"
        if str(style).lower() == "manual upload": 
            style = "realistic presenter"

        language = self.avatar.get("voice_preferences", {}).get("language", "Hindi")
        
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

For EACH of the following scenes, write a 3-4 sentence visual+audio description IN ENGLISH.
Include WHAT THE PERSON SAYS (in {language}), camera movements, and mood.
ALWAYS specify 9:16 vertical.

SCENES TO GENERATE (generate a prompt for EVERY scene listed):
{chr(10).join([f'- "{s.get("scene", "Scene")}"' for s in scene_list])}

Return ONLY valid JSON with one key per scene name:
{{
  {', '.join([f'"{s.get("scene", "Scene")}": "description..."' for s in scene_list])}
}}
"""
        
        try:
            if self.client:
                response = self.client.models.generate_content(
                    model="gemini-flash-latest",
                    contents=prompt,
                    config={'response_mime_type': 'application/json'}
                )
                result_prompts = json.loads(response.text)
                setattr(self, cache_key, result_prompts)
                logger.info(f"     Generated {len(result_prompts)} D2C scene prompts via Gemini")
                return result_prompts
        except Exception as e:
            logger.warning(f"     LLM scene prompt generation failed: {e}. Using fallback.")
        
        # Fallback: generate prompts for ALL scene names dynamically
        fallback_prompts = {}
        for s in scene_list:
            name = s.get("scene", "Scene")
            visual_hint = s.get("visual_continuity", "")
            
            if name in ("Hook", "Relatable Moment"):
                fallback_prompts[name] = f"A young Indian person looks at the camera and speaks in {language} about {user_problem}. They look concerned and relatable. Cinematic close-up, warm lighting. No product visible. 9:16 vertical. {visual_hint}"
            elif name == "Problem":
                fallback_prompts[name] = f"The same person speaks emotionally in {language} about the frustration of {user_problem}. Push-in camera, dramatic lighting. No product visible. 9:16 vertical. {visual_hint}"
            elif name in ("Solution", "Feature Highlight", "Product Demo"):
                fallback_prompts[name] = f"The person's expression changes to excitement as they proudly reveal {product_name}! They stand next to the {category} and speak excitedly in {language} about its features. Dynamic showcase. 9:16 vertical. {visual_hint}"
            elif name in ("Trust", "Testimonial"):
                fallback_prompts[name] = f"The person speaks confidently in {language} about {brand}'s reputation. Premium clean environment. 9:16 vertical. {visual_hint}"
            elif name in ("Proof",):
                fallback_prompts[name] = f"Multiple happy people using {product_name} in the real world. The presenter speaks in {language} about amazing results. Dynamic tracking shots. 9:16 vertical. {visual_hint}"
            elif name in ("CTA", "Offer", "Urgency"):
                fallback_prompts[name] = f"Marketing finale: the person {offer_statement} with energy in {language}! Hero shot of {product_name} with {brand} text visible. Urgent buying energy. 9:16 vertical. {visual_hint}"
            else:
                fallback_prompts[name] = f"Cinematic scene titled '{name}': A person speaks in {language} about {product_name} by {brand}. {visual_hint}. Premium {category} setting. 9:16 vertical."
        
        setattr(self, cache_key, fallback_prompts)
        return fallback_prompts

    def _build_prompt(self, scene: Dict) -> str:
        """Builds a product-specific cinematic prompt for Veo with Hindi speaking dialogue.
        
        Injects Global Visual Context for end-to-end continuity.
        """
        scene_name = scene.get("scene", "")
        directives = scene.get("realistic_directives", "")
        copy_text = scene.get("voiceover", "")
        
        language = self.avatar.get("voice_preferences", {}).get("language", "Hindi")
        
        variant_id = scene.get("_variant_id", "default")
        scene_prompts = self._generate_scene_prompts(
            self.variants.get("variants", [])[0].get("storyboard", []),
            variant_id=variant_id
        )
        
        prompt = scene_prompts.get(scene_name, 
            f"Cinematic footage of {self.context.get('product_understanding', {}).get('product_name', 'the product')}. "
            f"Premium lifestyle, 9:16 vertical."
        )
        
        # ── INJECT GLOBAL CONTEXT for continuity ──
        global_ctx = self._build_global_context()
        prompt += f" {global_ctx['consistency_prompt']}"
        
        # ── INJECT AVATAR IDENTITY for this scene ──
        scene_avatar = self._get_avatar_for_scene(scene)
        if scene_avatar:
            avatar_name = scene_avatar.get("name", scene_avatar.get("role", ""))
            avatar_desc = scene_avatar.get("description", "")
            if avatar_name:
                prompt += f" The person in this scene is {avatar_name}. {avatar_desc}. Use the provided reference image for this character."
        
        if copy_text:
            prompt += f' The person in the video speaks in {language} and says: "{copy_text}"'
        
        if directives:
            prompt += f" {directives}"
        
        return prompt
