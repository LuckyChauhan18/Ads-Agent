from typing import Dict, Any, List

class AudioPlannerEngine:
    def __init__(self, ad_type: str):
        self.ad_type = ad_type.lower().replace(" ", "_")

    def plan_audio(self) -> Dict[str, Any]:
        """
        Decides on audio elements based on the ad type.
        """
        if self.ad_type == "influencer":
            return {
                "voice_type": "avatar_speech",
                "lip_sync": True,
                "music_style": "light_social_media_music",
                "sfx_list": ["transition_whoosh", "subtle_pop"],
                "pacing": "energetic_and_natural"
            }
        elif self.ad_type == "testimonial":
            return {
                "voice_type": "voiceover",
                "lip_sync": False,
                "music_style": "emotional_soft_music",
                "sfx_list": [],
                "pacing": "calm_and_trustworthy"
            }
        elif self.ad_type == "product_demo":
            return {
                "voice_type": "minimal_voiceover",
                "lip_sync": False,
                "music_style": "modern_product_music",
                "sfx_list": ["click", "swipe", "pop", "whoosh"],
                "pacing": "fast_and_feature_focused"
            }
        elif self.ad_type == "before_after":
            return {
                "voice_type": "none",
                "lip_sync": False,
                "music_style": "dramatic_transformation_music",
                "sfx_list": ["transition_whoosh", "sparkle", "impact"],
                "pacing": "dynamic_contrast"
            }
        elif self.ad_type == "lifestyle":
            return {
                "voice_type": "soft_voiceover",
                "lip_sync": False,
                "music_style": "cinematic_lifestyle_music",
                "sfx_list": ["ambient_environment"],
                "pacing": "rhythmic_and_aesthetic"
            }
        else:
            # Default fallback
            return {
                "voice_type": "voiceover",
                "lip_sync": False,
                "music_style": "generic_background_music",
                "sfx_list": ["whoosh"],
                "pacing": "standard"
            }
