"""
STEP 4: Avatar Selection (Upgraded)
Selects the best-matching HeyGen avatar_id + voice_id from the catalog.
Uses user preferences from avatar_input.json as primary overrides,
then falls back to rules-based scoring from campaign context.
"""
import json
import os
import random
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

# Load .env
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path, override=True)

# --- Style Mapping: Campaign Context → HeyGen Avatar Styles ---

AVATAR_TYPE_TO_STYLES = {
    "UGC_human": ["ugc", "casual", "lifestyle"],
    "presenter": ["semi_formal", "formal", "professional"],
    "direct_presenter": ["formal", "professional", "semi_formal"],
}

ENERGY_TO_VOICE_STYLES = {
    "calm_friendly": ["calm", "friendly", "lifelike", "neutral"],
    "warm_upbeat": ["excited", "friendly", "ugc", "neutral"],
    "balanced": ["neutral", "professional", "lifelike"],
    "firm_confident": ["confident", "professional", "neutral"],
}

CAMERA_TO_ANGLE = {
    "talking_head_self_shot": "front",
    "studio_close_up": "front",
    "mixed_shots": "side",
    "split_screen_demo": "front",
}

AVATAR_TYPE_MAP = {
    ("cold", "POV Relatable"): "UGC_human",
    ("cold", "Story-based"): "UGC_human",
    ("cold", "Problem-first"): "presenter",
    ("cold", "Comparison"): "presenter",
    ("warm", "POV Relatable"): "UGC_human",
    ("warm", "Story-based"): "presenter",
    ("warm", "Problem-first"): "presenter",
    ("warm", "Comparison"): "presenter",
    ("hot", "POV Relatable"): "direct_presenter",
    ("hot", "Story-based"): "direct_presenter",
    ("hot", "Problem-first"): "direct_presenter",
    ("hot", "Comparison"): "direct_presenter",
}

ENERGY_MAP = {
    "Empathetic": "calm_friendly",
    "Friendly": "warm_upbeat",
    "Neutral": "balanced",
    "Direct": "firm_confident",
}

CAMERA_MAP = {
    "POV Relatable": "talking_head_self_shot",
    "Story-based": "mixed_shots",
    "Problem-first": "studio_close_up",
    "Comparison": "split_screen_demo",
}

PACE_MAP = {
    "short": "normal_slow",
    "medium": "normal",
    "long": "slightly_fast",
}


class AvatarSelector:
    """STEP 4: Selects the best HeyGen avatar and voice for the campaign.
    
    Priority: avatar_input.json overrides > campaign auto-detection > defaults
    
    Input: Script (Step 3) + Campaign Context (Step 1) + 
           HeyGen Catalog (Step 3.5) + Avatar Input (from input/)
    Output: selected_avatar_id, selected_voice_id, delivery profile
    """
    
    def __init__(self, script_output: Dict, campaign_context: Dict, 
                 heygen_catalog: Dict, avatar_input: Dict = None):
        self.script = script_output
        self.context = campaign_context
        self.catalog = heygen_catalog
        self.avatars = heygen_catalog.get("avatars", [])
        self.voices = heygen_catalog.get("voices", [])
        self.user_prefs = avatar_input or {}
    
    def _determine_requirements(self) -> Dict:
        """Determines avatar/voice requirements.
        User preferences (avatar_input.json) override auto-detection."""
        pattern = self.script.get("pattern_used", {})
        funnel = self.context.get("funnel_stage", "cold")
        opening_style = pattern.get("opening_style", "POV Relatable")
        tone = pattern.get("tone", "Neutral")
        angle = pattern.get("angle", "General")
        text_density = pattern.get("text_density", "short")
        
        # --- Auto-detect from campaign context ---
        avatar_type = AVATAR_TYPE_MAP.get((funnel, opening_style), "presenter")
        if angle == "Trust" and avatar_type not in ["UGC_human", "direct_presenter"]:
            avatar_type = "UGC_human"
        
        auto_gender = self.context.get("avatar_gender", "any")
        auto_energy = ENERGY_MAP.get(tone, "balanced")
        auto_camera = CAMERA_MAP.get(opening_style, "studio_close_up")
        auto_pace = PACE_MAP.get(text_density, "normal")
        
        # --- Override with user preferences from avatar_input.json ---
        avatar_prefs = self.user_prefs.get("avatar_preferences", {})
        voice_prefs = self.user_prefs.get("voice_preferences", {})
        delivery_prefs = self.user_prefs.get("delivery_style", {})
        
        gender = avatar_prefs.get("gender") or auto_gender
        style = avatar_prefs.get("style", "")
        age_range = avatar_prefs.get("age_range", "25-35")
        ethnicity_hint = avatar_prefs.get("ethnicity_hint", "")
        
        voice_gender = voice_prefs.get("gender") or gender
        voice_tone = voice_prefs.get("tone", "")
        voice_pace = voice_prefs.get("pace") or auto_pace
        
        energy = delivery_prefs.get("energy") or auto_energy
        camera_angle = delivery_prefs.get("camera_angle", "front")
        expression = delivery_prefs.get("expression", "sincere")
        
        # Map user style to avatar style keywords
        style_map = {
            "casual": ["ugc", "casual", "lifestyle"],
            "business": ["formal", "professional", "semi_formal"],
            "formal": ["formal", "professional"],
            "ugc": ["ugc", "casual"],
            "lifestyle": ["lifestyle", "casual"],
            "professional": ["professional", "semi_formal", "formal"],
        }
        preferred_styles = style_map.get(style, AVATAR_TYPE_TO_STYLES.get(avatar_type, ["general"]))
        
        # Map user voice tone to voice style keywords
        voice_tone_map = {
            "friendly": ["friendly", "ugc", "excited", "neutral"],
            "calm": ["calm", "lifelike", "neutral"],
            "excited": ["excited", "friendly", "ugc"],
            "professional": ["professional", "neutral", "lifelike"],
            "confident": ["confident", "professional", "neutral"],
            "neutral": ["neutral", "lifelike"],
        }
        preferred_voice_styles = voice_tone_map.get(
            voice_tone, 
            ENERGY_TO_VOICE_STYLES.get(energy, ["neutral"])
        )
        
        return {
            "avatar_type": avatar_type,
            "gender": gender,
            "voice_gender": voice_gender,
            "energy": energy,
            "camera_style": auto_camera,
            "preferred_angle": camera_angle,
            "speaking_pace": voice_pace,
            "expression": expression,
            "age_range": age_range,
            "ethnicity_hint": ethnicity_hint,
            "preferred_avatar_styles": preferred_styles,
            "preferred_voice_styles": preferred_voice_styles,
        }
    
    def _score_avatar(self, avatar: Dict, requirements: Dict) -> float:
        """Scores an avatar against requirements."""
        score = 0.0
        
        # Gender match (strong signal)
        req_gender = requirements["gender"]
        if req_gender and req_gender != "any":
            if avatar.get("gender", "").lower() == req_gender.lower():
                score += 30
            elif avatar.get("gender") == "unknown":
                score += 5
            else:
                score -= 20
        
        # Style match (strongest signal)
        for style in avatar.get("styles", []):
            if style in requirements["preferred_avatar_styles"]:
                score += 25
            elif style == "general":
                score += 5
        
        # Camera angle match
        if avatar.get("camera_angle") == requirements["preferred_angle"]:
            score += 10
        
        # Ethnicity hint match (if provided)
        ethnicity = requirements.get("ethnicity_hint", "")
        if ethnicity:
            name_lower = avatar.get("name", "").lower()
            ethnicity_keywords = {
                "south_asian": ["aditya", "priya", "raj", "kumar", "singh", "ananya", "arjun"],
                "east_asian": ["mei", "chen", "yuki", "kim", "li", "wang"],
                "european": ["anna", "james", "sarah", "michael", "emma"],
                "african": ["amara", "kwame", "zuri", "kofi"],
            }
            keywords = ethnicity_keywords.get(ethnicity, [])
            for kw in keywords:
                if kw in name_lower:
                    score += 15
                    break
        
        # Prefer proper named avatars
        name = avatar.get("name", "")
        if len(name) > 3 and not name.startswith("avatar_"):
            score += 5
        
        return score
    
    def _score_voice(self, voice: Dict, requirements: Dict) -> float:
        """Scores a voice against requirements."""
        score = 0.0
        
        # Gender match
        req_gender = requirements.get("voice_gender", requirements["gender"])
        if req_gender and req_gender != "any":
            if voice.get("gender", "").lower() == req_gender.lower():
                score += 30
            elif voice.get("gender") == "unknown":
                score += 5
            else:
                score -= 20
        
        # Style match
        for style in voice.get("styles", []):
            if style in requirements["preferred_voice_styles"]:
                score += 25
        
        # Pause support
        if voice.get("support_pause"):
            score += 10
        
        # Clean name
        name = voice.get("name", "")
        if ".mp4" not in name and ".m4a" not in name:
            score += 5
        
        return score
    
    def _select_best(self, items: List[Dict], score_fn, requirements: Dict, 
                     id_key: str, name_key: str) -> Tuple[str, str, float]:
        """Generic scorer — returns (id, name, score) for best match."""
        if not items:
            return None, "none", 0
        
        scored = [(score_fn(item, requirements), item) for item in items]
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Pick the top-scored item (deterministic)
        selected_score, selected = scored[0]
        return selected.get(id_key, ""), selected.get(name_key, ""), selected_score
    
    def generate_output(self) -> Dict:
        """Produces the full STEP 4 output with real HeyGen IDs."""
        
        # Check for force overrides from avatar_input.json
        overrides = self.user_prefs.get("overrides", {})
        force_avatar = overrides.get("force_avatar_id")
        force_voice = overrides.get("force_voice_id")
        
        requirements = self._determine_requirements()
        
        # Select avatar (force or score)
        if force_avatar:
            avatar_id = force_avatar
            avatar_name = f"forced:{force_avatar[:20]}"
            avatar_score = 999
            print(f"   Using forced avatar_id: {force_avatar}")
        else:
            avatar_id, avatar_name, avatar_score = self._select_best(
                self.avatars, self._score_avatar, requirements, 
                "avatar_id", "name"
            )
        
        # Select voice (force or score)
        if force_voice:
            voice_id = force_voice
            voice_name = f"forced:{force_voice[:20]}"
            voice_score = 999
            print(f"   Using forced voice_id: {force_voice}")
        else:
            voice_id, voice_name, voice_score = self._select_best(
                self.voices, self._score_voice, requirements,
                "voice_id", "name"
            )
        
        pattern = self.script.get("pattern_used", {})
        platform_specs = self.user_prefs.get("platform_specs", {})
        
        return {
            "campaign_id": self.context.get("campaign_id", "unknown"),
            
            # Real HeyGen IDs
            "selected_avatar_id": avatar_id,
            "selected_avatar_name": avatar_name,
            "selected_voice_id": voice_id,
            "selected_voice_name": voice_name,
            
            # Delivery profile
            "avatar_profile": {
                "avatar_type": requirements["avatar_type"],
                "gender": requirements["gender"],
                "delivery_energy": requirements["energy"],
                "camera_style": requirements["camera_style"],
                "speaking_pace": requirements["speaking_pace"],
                "expression": requirements.get("expression", "sincere"),
            },
            
            # Platform specs (from input)
            "platform_specs": {
                "aspect_ratio": platform_specs.get("aspect_ratio", "9:16"),
                "resolution": platform_specs.get("resolution", "1080x1920"),
                "format": platform_specs.get("format", "mp4"),
                "max_duration_seconds": platform_specs.get("max_duration_seconds", 30),
            },
            
            # Match quality
            "selection_scores": {
                "avatar_score": avatar_score,
                "voice_score": voice_score,
            },
            
            # Derivation trace
            "derived_from": {
                "script_tone": pattern.get("tone"),
                "opening_style": pattern.get("opening_style"),
                "angle": pattern.get("angle"),
                "text_density": pattern.get("text_density"),
                "funnel_stage": self.context.get("funnel_stage"),
                "brand_voice": self.context.get("brand_voice"),
                "platform": self.context.get("platform"),
            },
            
            # User preferences applied
            "user_preferences_applied": {
                "avatar_gender": requirements["gender"],
                "avatar_style": requirements["preferred_avatar_styles"],
                "voice_tone": requirements["preferred_voice_styles"],
                "camera_angle": requirements["preferred_angle"],
                "ethnicity_hint": requirements.get("ethnicity_hint", ""),
            },
            
            "requirements": requirements,
        }


if __name__ == "__main__":
    script_path = os.path.join("output", "script_output.json")
    ctx_path = os.path.join("output", "campaign_psychology.json")
    catalog_path = os.path.join("output", "heygen_catalog.json")
    avatar_input_path = os.path.join("input", "avatar_input.json")
    
    required = [script_path, ctx_path, catalog_path]
    if all(os.path.exists(p) for p in required):
        with open(script_path) as f: script_data = json.load(f)
        with open(ctx_path) as f: ctx_data = json.load(f)
        with open(catalog_path) as f: catalog_data = json.load(f)
        
        avatar_input = {}
        if os.path.exists(avatar_input_path):
            with open(avatar_input_path) as f:
                avatar_input = json.load(f)
        
        selector = AvatarSelector(script_data, ctx_data, catalog_data, avatar_input)
        result = selector.generate_output()
        print(json.dumps(result, indent=2))
    else:
        print("Missing required files in output/")
