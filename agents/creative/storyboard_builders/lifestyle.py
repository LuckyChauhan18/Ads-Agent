from .base import BaseStoryboardBuilder

LIFESTYLE_ASSET_RULES = {
    "Aesthetic Hook": {
        "shot_type": "b_roll_lifestyle",
        "asset_categories": ["lifestyle"],
        "text_overlay": "ASPIRATIONAL_HOOK",
        "environment": (
            "bright sunlit workspace or modern cafe morning setup, clean layout, "
            "organic depth with lush plants framing the edge"
        ),
        "camera_shot": (
            "cinematic medium shot with slow creeping track, 50mm anamorphic look, "
            "shallow depth of field with organic oval bokeh"
        ),
        "realistic_directives": (
            "Natural golden-hour lens flares with authentic light leaks roll-off. "
            "Candid unposed human posture showing authentic micro-animations of fabric. "
            "Consistent daylight grading threshold baseline setups."
        ),
        "rationale": "Set aspirational aesthetic mood without staged commercial glare."
    },
    "Daily Routine": {
        "shot_type": "b_roll_lifestyle",
        "asset_categories": ["lifestyle"],
        "text_overlay": None,
        "environment": (
            "clean modern kitchen dashboard interior with soft morning sunshine flare spread"
        ),
        "camera_shot": (
            "smooth tracking shot moving alongside subject kinetic pacing speeds"
        ),
        "realistic_directives": (
            "Natural ambient falloff lighting parameters matching window direction baseline. "
            "Grounded material realism holding weight dynamics truthfully. "
            "Subtle handheld drift sliders layout setup."
        ),
        "rationale": "Contextualize lifestyle before product introduction grounded frame."
    },
    "Product Interaction": {
        "shot_type": "b_roll_product_macro",
        "asset_categories": ["product"],
        "text_overlay": None,
        "environment": (
            "same lighting physics setup angle focusing product surface details"
        ),
        "camera_shot": (
            "macro slider slider pull detailing tracking sliders frame reveal"
        ),
        "realistic_directives": (
            "Consistent product alignment Scale boundary anchors framing setup. "
            "Highlight accurate material textures (metal, glass) without over-sharp CGI glare."
        ),
        "rationale": "Introduce functionality details seamlessly without breaking aesthetics grading."
    },
    "The Feeling": {
        "shot_type": "b_roll_lifestyle",
        "asset_categories": ["lifestyle"],
        "text_overlay": None,
        "environment": (
            "bright wide living space facing bright sunshine setup layout"
        ),
        "camera_shot": (
            "smooth handheld tracking shot slow parallax sliders orbit"
        ),
        "realistic_directives": (
            "Bright warm daylight spread highlights exposure balance benchmarks setup. "
            "Authentic smile reaction action layout setups."
        ),
        "rationale": "Mood payoff matching emotional pay rewards layout."
    },
    "Brand/CTA": {
        "shot_type": "logo_endcard",
        "asset_categories": ["logo", "product"],
        "text_overlay": "CTA_TEXT",
        "environment": (
            "clean aesthetic gradient backdrop matching brand theme grading baseline setup"
        ),
        "camera_shot": (
            "smooth scale slider centered position alignment scale orbit"
        ),
        "realistic_directives": (
            "Consistent grading maintaining previous asset setup boundaries. "
            "Non-polished authentic clean lockup reveal layout."
        ),
        "rationale": "Branded lockup endcard setups layout."
    }
}

class LifestyleStoryboardBuilder(BaseStoryboardBuilder):
    """Storyboard Builder for Lifestyle-style ads with scene mapped rules."""
    
    def get_scene_asset_rules(self):
        return LIFESTYLE_ASSET_RULES

    def get_global_cinematic_style(self):
        return (
            "Shot on cinema camera (Red Monstro look), vintage anamorphic lens, organic oval bokeh. "
            "Natural golden-hour or daylight lighting physics, 3200K-5600K temperature transitions. "
            "Soft lens flare elements, high dynamic range exposing rich shadow detail and rolled highlights. "
            "Smooth continuous glide camera motion (Movi/Ronin look), natural kinetic pacing speed. "
            "Grounded material realism with micro-imperfections, authentic fabric/surface textures. "
            "Warm cinematic LUT grading, 35mm fine film grain overlay, no high-gloss commercial finish."
        )
