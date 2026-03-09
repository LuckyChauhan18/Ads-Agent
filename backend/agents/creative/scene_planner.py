"""
AI Scene Planner — Dynamic Scene Planning Engine

Given a target ad_length (15s-60s), uses LLM to generate:
  - Scene names (Hook, Problem, Solution, etc.)
  - Per-scene durations that sum to ad_length
  - Avatar assignments per scene (customer, friend, presenter)

This output feeds directly into ScriptGenerator and GeminiRenderer.
"""

import os
import json
import math
from google import genai
from dotenv import load_dotenv

# Load .env
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(dotenv_path)

import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from utils.logger import logger


# ── Fallback Templates ────────────────────────────────────────────
# Length-based templates (used if LLM fails)
SCENE_TEMPLATES = {
    15: [
        {"scene": "Hook", "duration": "4s"},
        {"scene": "Solution", "duration": "6s"},
        {"scene": "CTA", "duration": "5s"},
    ],
    30: [
        {"scene": "Hook", "duration": "4s"},
        {"scene": "Problem", "duration": "5s"},
        {"scene": "Solution", "duration": "6s"},
        {"scene": "Proof", "duration": "6s"},
        {"scene": "Trust", "duration": "5s"},
        {"scene": "CTA", "duration": "4s"},
    ],
    45: [
        {"scene": "Hook", "duration": "4s"},
        {"scene": "Problem", "duration": "5s"},
        {"scene": "Relatable Moment", "duration": "5s"},
        {"scene": "Solution", "duration": "6s"},
        {"scene": "Feature Highlight", "duration": "5s"},
        {"scene": "Proof", "duration": "6s"},
        {"scene": "Trust", "duration": "5s"},
        {"scene": "Offer", "duration": "4s"},
        {"scene": "CTA", "duration": "5s"},
    ],
    60: [
        {"scene": "Hook", "duration": "4s"},
        {"scene": "Problem", "duration": "5s"},
        {"scene": "Relatable Moment", "duration": "5s"},
        {"scene": "Solution", "duration": "6s"},
        {"scene": "Feature Highlight", "duration": "5s"},
        {"scene": "Product Demo", "duration": "5s"},
        {"scene": "Proof", "duration": "6s"},
        {"scene": "Testimonial", "duration": "5s"},
        {"scene": "Trust", "duration": "5s"},
        {"scene": "Offer", "duration": "4s"},
        {"scene": "Urgency", "duration": "5s"},
        {"scene": "CTA", "duration": "5s"},
    ]
}

# Avatar role mapping per scene type
DEFAULT_AVATAR_MAP = {
    "Hook": "customer",
    "Problem": "customer",
    "Relatable Moment": "friend",
    "Solution": "presenter",
    "Feature Highlight": "presenter",
    "Product Demo": "presenter",
    "Proof": "customer",
    "Testimonial": "customer",
    "Trust": "presenter",
    "Offer": "presenter",
    "Urgency": "presenter",
    "CTA": "presenter",
}


class ScenePlanner:
    """LLM-driven scene planning engine for variable-length ads."""

    def __init__(self, campaign_context: dict, avatar_list: list = None):
        """
        Args:
            campaign_context: Campaign psychology dict with product info
            avatar_list: List of avatar dicts with {name, role, image/url}
        """
        self.context = campaign_context
        self.avatar_list = avatar_list or []
        
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=api_key) if api_key else None

    def _get_avatar_for_role(self, role: str) -> dict:
        """Returns the avatar dict matching a role (customer/friend/presenter)."""
        for av in self.avatar_list:
            if av.get("role", "").lower() == role.lower():
                return av
        # Fallback: return first avatar or empty
        return self.avatar_list[0] if self.avatar_list else {}

    def plan_scenes_llm(self, ad_length: int, platform: str = "Instagram Reels") -> list:
        """Uses LLM to generate a smart scene plan with durations."""
        if not self.client:
            logger.warning("   No Gemini client for Scene Planner. Using fallback templates.")
            return self._plan_scenes_fallback(ad_length)

        product_info = self.context.get("product_understanding", {})
        product_name = product_info.get("product_name", "the product")
        category = product_info.get("category", "consumer product")
        brand_voice = self.context.get("brand_voice", "premium")
        
        # Build avatar context
        avatar_roles = ", ".join([f"{a.get('name','?')} ({a.get('role','?')})" for a in self.avatar_list])
        if not avatar_roles:
            avatar_roles = "Single presenter avatar"

        prompt = f"""You are an expert video ad planner for {platform}.

TARGET AD LENGTH: {ad_length} seconds
PRODUCT: {product_name}
CATEGORY: {category}
BRAND VOICE: {brand_voice}
AVAILABLE AVATARS: {avatar_roles}

Create a scene-by-scene plan where durations sum to EXACTLY {ad_length} seconds.

RULES:
1. First scene MUST be "Hook" (3-4s, punchy)
2. Last scene MUST be "CTA" (4-5s, urgent)
3. Middle scenes should follow D2C story arc: Problem → Solution → Proof → Trust
4. For longer ads (45s+), add Feature Highlight, Testimonial, Offer, Urgency scenes
5. Each scene duration: minimum 3s, maximum 8s
6. Assign the most appropriate avatar role to each scene
7. The total of all durations MUST equal {ad_length}

AVATAR ASSIGNMENT RULES:
- "customer" avatar: Hook, Problem, Relatable, Testimonial scenes
- "friend" avatar: Relatable Moment scenes (if available)
- "presenter" avatar: Solution, Demo, Trust, CTA scenes

Return ONLY valid JSON array:
[
  {{"scene": "Hook", "duration": "4s", "avatar_role": "customer"}},
  ...
  {{"scene": "CTA", "duration": "5s", "avatar_role": "presenter"}}
]"""

        try:
            logger.info(f"   🧠 Planning {ad_length}s ad with LLM ({platform})...")
            response = self.client.models.generate_content(
                model="gemini-flash-latest",
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            scenes = json.loads(response.text)
            
            if isinstance(scenes, dict) and "scenes" in scenes:
                scenes = scenes["scenes"]
            
            # Validate total duration
            total = sum(int(s.get("duration", "5s").replace("s", "")) for s in scenes)
            if abs(total - ad_length) > 2:
                logger.warning(f"   ⚠️ LLM planned {total}s but target is {ad_length}s. Adjusting...")
                scenes = self._adjust_durations(scenes, ad_length)
            
            # Attach avatar objects
            for scene in scenes:
                role = scene.get("avatar_role", DEFAULT_AVATAR_MAP.get(scene["scene"], "presenter"))
                scene["avatar"] = self._get_avatar_for_role(role)
                scene["avatar_role"] = role
            
            logger.info(f"   ✅ Scene plan: {len(scenes)} scenes, total ≈{ad_length}s")
            return scenes
            
        except Exception as e:
            logger.warning(f"   ⚠️ LLM scene planning failed: {e}. Using fallback.")
            return self._plan_scenes_fallback(ad_length)

    def _plan_scenes_fallback(self, ad_length: int) -> list:
        """Template-based fallback scene planner."""
        # Find closest template
        template_key = min(SCENE_TEMPLATES.keys(), key=lambda k: abs(k - ad_length))
        template = [dict(s) for s in SCENE_TEMPLATES[template_key]]  # Deep copy
        
        # Adjust durations to match target
        template = self._adjust_durations(template, ad_length)
        
        # Assign avatars
        for scene in template:
            role = DEFAULT_AVATAR_MAP.get(scene["scene"], "presenter")
            scene["avatar_role"] = role
            scene["avatar"] = self._get_avatar_for_role(role)
        
        logger.info(f"   📋 Fallback scene plan: {len(template)} scenes for {ad_length}s")
        return template

    def _adjust_durations(self, scenes: list, target_total: int) -> list:
        """Adjusts scene durations so they sum to exactly target_total."""
        current_total = sum(int(s.get("duration", "5s").replace("s", "")) for s in scenes)
        diff = target_total - current_total
        
        if diff == 0:
            return scenes
        
        # Distribute the difference across middle scenes (not Hook or CTA)
        adjustable = [i for i in range(1, len(scenes) - 1)] if len(scenes) > 2 else list(range(len(scenes)))
        
        while diff != 0 and adjustable:
            for idx in adjustable:
                if diff == 0:
                    break
                current_dur = int(scenes[idx]["duration"].replace("s", ""))
                if diff > 0 and current_dur < 8:
                    scenes[idx]["duration"] = f"{current_dur + 1}s"
                    diff -= 1
                elif diff < 0 and current_dur > 3:
                    scenes[idx]["duration"] = f"{current_dur - 1}s"
                    diff += 1
            
            # Safety: if we can't adjust anymore, break
            if diff != 0:
                new_total = sum(int(s["duration"].replace("s", "")) for s in scenes)
                if new_total == current_total:
                    break
                current_total = new_total
        
        return scenes
