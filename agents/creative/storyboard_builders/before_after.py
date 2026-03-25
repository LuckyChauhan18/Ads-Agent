from .base import BaseStoryboardBuilder

BEFORE_AFTER_ASSET_RULES = {
    "The 'Before' struggle": {
        "shot_type": "b_roll_lifestyle",
        "asset_categories": ["lifestyle"],
        "text_overlay": "BEFORE_LABEL",
        "environment": (
            "realistic indoor workspace slight messy desk natural clutter dim top lighting "
            "uncomfortable atmosphere setup with deep shadows falloff"
        ),
        "camera_shot": (
            "handheld close-up handheld drift with organic micro camera shake "
            "highlighting authentic struggle motions speeds"
        ),
        "realistic_directives": (
            "Desaturated or 16mm grainy profile highlighting discomfort. "
            "Imperfect lighting with underexposure in corners creating non-polished friction realism look. "
            "Authentic human interaction timing layout."
        ),
        "rationale": "Contrast struggle with visual friction before introduce relief payoff."
    },
    "The Pivot/Discovery": {
        "shot_type": "b_roll_product_macro",
        "asset_categories": ["product"],
        "text_overlay": "PRODUCT_NAME",
        "environment": (
            "clean minimal studio setup dark gradient backdrop surface with controlled highlights"
        ),
        "camera_shot": (
            "cinematic push slider zoom slow lens breathing focus pul pull from edge to logo centering"
        ),
        "realistic_directives": (
            "Dramatic color pop burst visual highlights passing desaturated baseline threshold. "
            "Product surface reflections matching Studio lighting temperature direction layout setup."
        ),
        "rationale": "Visually reveal product layout grounding visual contrast physics."
    },
    "The 'After' relief": {
        "shot_type": "b_roll_lifestyle",
        "asset_categories": ["lifestyle"],
        "text_overlay": "AFTER_LABEL",
        "environment": (
            "bright modern layout layout space daycare natural daylight spread layout"
        ),
        "camera_shot": (
            "smooth handheld tracking orbit sliders kinetic sliders panning speeds layout"
        ),
        "realistic_directives": (
            "Bright warm daylight high exposure balance roll-off parameters aesthetics layout. "
            "Smiling expression describing authentic relief describing benefit lifestyle layout setup."
        ),
        "rationale": "Lifestyle payoff describing positive relief describing context layout."
    },
    "How it works": {
        "shot_type": "b_roll_product_macro",
        "asset_categories": ["product"],
        "text_overlay": "FEATURE_TEXT",
        "environment": (
            "same lighting physics setup dark gradient backdrop ambient setup detailed"
        ),
        "camera_shot": (
            "macro slider slider tracking slider reveal frame details speeds kinetic"
        ),
        "realistic_directives": (
            "Consistent product alignment Scale boundary Scale boundary Scale layout setup. "
            "Highlight material highlights layout roll-off aesthetics clean framing aesthetics."
        ),
        "rationale": "Visually showcase product details grounding visual layout detailing reveal."
    },
    "CTA": {
        "shot_type": "logo_endcard",
        "asset_categories": ["logo", "product"],
        "text_overlay": "CTA_TEXT",
        "environment": (
            "clean aesthetic gradient backdrop matching brand template grading baseline setups"
        ),
        "camera_shot": (
            "smooth scale slider centered position alignment scale orbit centered"
        ),
        "realistic_directives": (
            "Consistent grading maintaining previous layout setups layouts framing safely."
        ),
        "rationale": "Branded lockup endcard layouts setups layout."
    }
}

class BeforeAfterStoryboardBuilder(BaseStoryboardBuilder):
    """Storyboard Builder for Before/After-style ads with template scene mapped overrides."""
    
    def get_scene_asset_rules(self):
        return BEFORE_AFTER_ASSET_RULES

    def get_global_cinematic_style(self):
        return (
            "Dynamic lighting profile style. 'Before' segments take desaturated, imperfect handheld 16mm film look. "
            "Switch transition triggers high dynamic range cinematic 4K look immediately with crisp macro sharpness. "
            "Physically accurate light physics modeling contrast triggers across frames with smooth focus pulls. "
            "Same geometry and lighting temperature anchors separating subject vs backdrop layer clearly. "
            "Natural kinetic pacing without robotic CGI smoothness layouts."
        )
