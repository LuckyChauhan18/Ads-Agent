from .base import BaseStoryboardBuilder

INFLUENCER_ASSET_RULES = {
    "Hook": {
        "shot_type": "avatar_talking_head",
        "asset_categories": ["product", "logo"],
        "text_overlay": "HOOK_TEXT",
        "environment": (
            "modern home interior dashboard workspace with clean ambient layout, "
            "soft natural daylight spilling from large window, warm bounce layout"
        ),
        "camera_shot": (
            "vlog style front-facing medium close-up, organic handheld micro-movement, "
            "50mm prime look with natural focus falloff framing the subject"
        ),
        "realistic_directives": (
            "Creator speaking directly to camera eye contact. "
            "High energy engagement with soft rim lighting highlight roll-off. "
            "Holding product close to lens causing natural depth defocus in background."
        ),
        "rationale": "Aspirational connection with high relatable grounding parameters."
    },
    "Story/Pain": {
        "shot_type": "b_roll_lifestyle",
        "asset_categories": ["lifestyle"],
        "text_overlay": None,
        "environment": (
            "practical room setup, slightly unorganized setting with natural human clutter, "
            "dim top-down mood lighting mixed with blue screen light cast"
        ),
        "camera_shot": (
            "close-up handheld slider with organic micro camera shake, "
            "slight motion blur during reaching actions or interactions"
        ),
        "realistic_directives": (
            "Moody underexposure profile in corners highlighting authentic struggle action. "
            "Grounded textures with micro-imperfections creating non-staged realism appearance."
        ),
        "rationale": "Contrast struggle setup highlighting accurate relatable friction."
    },
    "Discovery": {
        "shot_type": "avatar_talking_head",
        "asset_categories": ["product"],
        "text_overlay": "DISCOVERY_REACTION",
        "environment": (
            "same home setup workspace dashboard, same ambient window daylight baseline"
        ),
        "camera_shot": (
            "stabilized handheld push, fast lens breathing focus pull on product frame"
        ),
        "realistic_directives": (
            "Authentic smile high energy eyes reaction matching baseline lighting temperature. "
            "Product surface reflections matching window placement layout setup."
        ),
        "rationale": "Introduce relief payoff with brightened positive setup parameters."
    },
    "Solution": {
        "shot_type": "b_roll_product_lifestyle",
        "asset_categories": ["product", "lifestyle"],
        "text_overlay": None,
        "environment": (
            "same lighting physics setup layout with soft lens flares"
        ),
        "camera_shot": (
            "macro slider slider pull detailing detail tracking slider frame reveal"
        ),
        "realistic_directives": (
            "Consistent product alignment orientation bounding scales layout setup. "
            "Highlight material highlights layout roll-off aesthetics clean framing."
        ),
        "rationale": "Visually showcase product details grounding visual layout."
    },
    "Proof": {
        "shot_type": "b_roll_lifestyle",
        "asset_categories": ["lifestyle"],
        "text_overlay": "RESULTS_OVERLAY",
        "environment": (
            "natural outdoor location bright daylight with warm sunshine flares setup sunlit backdrop"
        ),
        "camera_shot": (
            "handheld tracking orbit sliders side panel frame panning slider setup"
        ),
        "realistic_directives": (
            "Vibrant color correction warm grading with natural highlights exposure balance setup."
        ),
        "rationale": "Lifestyle framing payoff layout."
    },
    "CTA": {
        "shot_type": "avatar_talking_head",
        "asset_categories": ["logo", "product"],
        "text_overlay": "CTA_TEXT",
        "environment": (
            "initial creator setup baseline backdrop with soft lighting bounce"
        ),
        "camera_shot": (
            "smooth scale slider tracking pan scale orbit centering"
        ),
        "realistic_directives": (
            "Energetic final interaction engagement maintaining consistent grading baseline setups."
        ),
        "rationale": "Call to action endcard setups layout."
    }
}

class InfluencerStoryboardBuilder(BaseStoryboardBuilder):
    """Storyboard Builder for Influencer-style ads with scene mapped rules."""
    
    def get_scene_asset_rules(self):
        return INFLUENCER_ASSET_RULES

    def get_global_cinematic_style(self):
        return (
            "Shot on high-end smartphone camera (iPhone 15 Pro look) or mirrorless vlogging setup. "
            "Natural lighting blend: soft ring light setup mixed with ambient window daylight, 5600K temperature. "
            "Organic handheld micro-vibrations, slight camera bump for realism, natural focus breathing. "
            "Crisp 4K sensor readout, HDR highlight roll-off without digital sharpening artifacts. "
            "Aesthetic depth of field framing subject clearly while maintaining slight background recognizability. "
            "Vibrant true-to-life skin tones, warm color grade layout, no over-polished beauty filter smoothing look."
        )
