from .base import BaseStoryboardBuilder

TESTIMONIAL_ASSET_RULES = {
    "Hook": {
        "shot_type": "b_roll_lifestyle",
        "asset_categories": ["lifestyle"],
        "text_overlay": "USER_QUOTE",
        "environment": (
            "warm domestic dashboard interior with ambient window lighting, soft diffused bounce"
        ),
        "camera_shot": (
            "medium close-up, organic handheld micro-movement, natural focus pull with honest depth"
        ),
        "realistic_directives": (
            "Authentic human micro-expressions and skin textures (documentary feel). "
            "Smiling or relaxed reaction matching accurate lighting temperature baseline. "
            "Soft ambient falloff shadows creating relatability."
        ),
        "rationale": "Introduce review context grounded safely and truthfully connection."
    },
    "User Story": {
        "shot_type": "b_roll_lifestyle",
        "asset_categories": ["lifestyle"],
        "text_overlay": None,
        "environment": (
            "practical domestic counter counter-tops brightened with sunlight direction flare spread"
        ),
        "camera_shot": (
            "slow slider tracking sliders detailing hands setting motion speeds kinetic parameters"
        ),
        "realistic_directives": (
            "Natural ambient daylight highlights and transparent shadows layout setup. "
            "Holding product describing weights and scale truthfully. "
            "No studio cinematic edge edge flares."
        ),
        "rationale": "Payoff descriptive setting truthfully layout grounded frame."
    },
    "Resolution": {
        "shot_type": "b_roll_product_lifestyle",
        "asset_categories": ["product", "lifestyle"],
        "text_overlay": None,
        "environment": (
            "same lighting physics setup layout with soft lens flares"
        ),
        "camera_shot": (
            "macro slider slider pull detailing detail tracking sliders frame reveal"
        ),
        "realistic_directives": (
            "Consistent product alignment Scale boundary anchors framing setup. "
            "Highlight material highlights layout roll-off aesthetics clean framing."
        ),
        "rationale": "Visually showcase product details grounding visual layout."
    },
    "Proof points": {
        "shot_type": "logo_endcard",
        "asset_categories": ["logo"],
        "text_overlay": "STAR_RATING",
        "environment": (
            "clean brand color backdrop maintaining previous grading baseline benchmarks setup"
        ),
        "camera_shot": (
            "smooth centering scale centered scale orbit panel slider frame"
        ),
        "realistic_directives": (
            "Graphic dynamic alignment focusing transparently framing previous backdrop triggers setup."
        ),
        "rationale": "Branded lockup scorecard sets layout."
    },
    "CTA": {
        "shot_type": "logo_endcard",
        "asset_categories": ["logo", "product"],
        "text_overlay": "BUY_NOW",
        "environment": (
            "consistent clean backdrop maintaining accurate grading layout"
        ),
        "camera_shot": (
            "smooth center Scale or slide reveal centering"
        ),
        "realistic_directives": (
            "Consistent engagement maintaining accurate visual context layout setup."
        ),
        "rationale": "Product purchase CTA setups layout."
    }
}

class TestimonialStoryboardBuilder(BaseStoryboardBuilder):
    """Storyboard Builder for Testimonial-style ads with scene mapped rules."""
    
    def get_scene_asset_rules(self):
        return TESTIMONIAL_ASSET_RULES

    def get_global_cinematic_style(self):
        return (
            "Shot on documentary cinema camera (Sony FX6 look), clean prime lens, relatable eye-level composition. "
            "Honest interior lighting setup: soft diffused key window light, gentle bounce card fill, natural rim separación. "
            "Fixed color temperature (4300K-5000K), honest shadow falloff, no artificial studio glare overlay. "
            "Imperfect organic micro-gestures capturing authentic human micro-expressions and skin textures. "
            "Grounded relatable sets with natural ambient dust speckles or surface weathering artifacts. "
            "Subtle reduction in digital sharpness, slightly soft contrast curves, transparent natural tones."
        )
