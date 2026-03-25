from .base import BaseStoryboardBuilder

PRODUCT_DEMO_ASSET_RULES = {
    "Problem Visual": {
        "shot_type": "b_roll_lifestyle",
        "asset_categories": ["lifestyle"],
        "text_overlay": "PROBLEM_TEXT",
        "environment": (
            "realistic indoor workspace, slightly messy desk, natural clutter, "
            "dim ambient lighting with cool tone, screen light reflecting on surroundings"
        ),
        "camera_shot": (
            "handheld close-up shot, slight micro shake, focus shifts naturally, "
            "subtle motion blur during interaction"
        ),
        "realistic_directives": (
            "Imperfect lighting with visible shadows, slight underexposure in corners. "
            "Natural human interaction timing, no staged perfection."
        ),
        "rationale": "Make problem feel real and relatable, not staged."
    },
    "Product Reveal": {
        "shot_type": "b_roll_product_macro",
        "asset_categories": ["product"],
        "text_overlay": "PRODUCT_NAME",
        "environment": (
            "clean studio setup with dark gradient background, controlled highlights, "
            "soft reflections on surface"
        ),
        "camera_shot": (
            "slow cinematic push-in with stabilized motion, slight lens breathing, "
            "macro focus pull from edge to logo"
        ),
        "realistic_directives": (
            "Consistent product orientation and scale. "
            "Softbox lighting with gentle highlight roll-off, no harsh clipping."
        ),
        "rationale": "Premium product introduction with controlled lighting."
    },
    "Feature 1": {
        "shot_type": "b_roll_product_macro",
        "asset_categories": ["product"],
        "text_overlay": "FEATURE_1",
        "environment": (
            "same studio setup, identical background and lighting, different angle only"
        ),
        "camera_shot": (
            "macro tracking shot across product surface, shallow depth of field, "
            "focus transitions across key feature"
        ),
        "realistic_directives": (
            "Maintain identical lighting and product position baseline. "
            "Highlight real material textures (metal, glass) with imperfections."
        ),
        "rationale": "Show feature without breaking visual continuity."
    },
    "Feature 2": {
        "shot_type": "b_roll_product_macro",
        "asset_categories": ["product"],
        "text_overlay": "FEATURE_2",
        "environment": (
            "same lighting setup, slight variation in angle only, no background change"
        ),
        "camera_shot": (
            "side angle slider shot, subtle parallax, controlled motion, no sudden jumps"
        ),
        "realistic_directives": (
            "Ensure reflections match light direction. "
            "No floating or unrealistic product behavior."
        ),
        "rationale": "Reinforce consistency while adding variation."
    },
    "Result": {
        "shot_type": "b_roll_product_lifestyle",
        "asset_categories": ["product", "lifestyle"],
        "text_overlay": "RESULT_TEXT",
        "environment": (
            "bright natural environment, daylight-balanced lighting, clean modern setup"
        ),
        "camera_shot": (
            "smooth handheld tracking shot, slight natural shake, subject interaction"
        ),
        "realistic_directives": (
            "Natural lighting falloff, soft highlights, realistic exposure balance. "
            "No overexposed whites or artificial glow."
        ),
        "rationale": "Show real-life benefit, not studio-only perfection."
    },
    "Logo/CTA": {
        "shot_type": "logo_endcard",
        "asset_categories": ["logo", "product"],
        "text_overlay": "CTA_TEXT",
        "environment": (
            "clean brand-colored background, minimal design, soft gradient"
        ),
        "camera_shot": (
            "static centered shot with subtle scale-in animation"
        ),
        "realistic_directives": (
            "Sharp but not over-processed logo rendering. "
            "Consistent color grading with previous scenes."
        ),
        "rationale": "Strong, clean brand recall."
    }
}

class ProductDemoStoryboardBuilder(BaseStoryboardBuilder):
    """Storyboard Builder for Product Demo-style ads with scene mapped rules."""
    
    def get_scene_asset_rules(self):
        return PRODUCT_DEMO_ASSET_RULES

    def get_global_cinematic_style(self):
        return (
            "Shot on high-end cinema camera (Arri Alexa 65 look), "
            "50mm macro lens, shallow depth of field, natural focus breathing. "
            "Consistent product design, same color, same geometry, no variation across frames. "
            "Studio lighting setup: key light at 45 degrees, soft fill light, subtle rim light for edge separation. "
            "Lighting temperature fixed at 5600K, soft shadows, realistic light falloff. "
            "Slight handheld micro-movements, natural motion blur, no robotic camera motion. "
            "Realistic textures with micro imperfections, subtle dust particles, fingerprints, no plastic look. "
            "Physically accurate reflections and shadows. "
            "Subtle film grain, slightly reduced sharpness, natural color grading. "
            "No over-polished or artificial smoothness."
        )
