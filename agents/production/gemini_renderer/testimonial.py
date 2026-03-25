from .base import BaseRenderer
from google.genai import types
from typing import Dict, List

class TestimonialRenderer(BaseRenderer):
    """Renderer specialized for Social Proof/Testimonial ads."""

    async def _get_reference_images_for_scene(self, scene: Dict) -> List:
        scene_name = scene.get("name", scene.get("scene", "")).lower()
        references = []

        # Testimonial maps to 'User Story' and 'Resolution'
        if "story" in scene_name or "resolution" in scene_name or "proof" in scene_name:
            # Use lifestyle images if available to show the 'happy user' context
            if self.assets.get("lifestyle"):
                img = await self._load_image_for_veo(self.assets["lifestyle"][0])
                if img: references.append(types.VideoGenerationReferenceImage(image=img, reference_type="ASSET"))
            # Use product
            if self.assets.get("product"):
                img = await self._load_image_for_veo(self.assets["product"][0])
                if img: references.append(types.VideoGenerationReferenceImage(image=img, reference_type="ASSET"))

        elif "cta" in scene_name:
            if self.assets.get("logo"):
                img = await self._load_image_for_veo(self.assets["logo"][0])
                if img: references.append(types.VideoGenerationReferenceImage(image=img, reference_type="ASSET"))

        return references[:3]

    def _generate_scene_prompts(self, scene_list: List[Dict]) -> Dict[str, str]:
        """Prompts focused on emotional relief and trustworthiness."""
        ctx = self._get_scene_context()
        ad_template = self.context.get("ad_template", {})
        template_scenes = ad_template.get("scenes", [])
        
        prompts = {}
        for s in scene_list:
            name = s.get("name", s.get("scene", ""))
            
            # Find matching template scene for metadata
            t_scene = next((ts for ts in template_scenes if ts.get("name") == name), {})
            t_visual = t_scene.get("visual", "")
            t_goal = t_scene.get("goal", "")
            t_cam = t_scene.get("camera_style", "")

            full_prompt = (
                f"Authentic testimonial video of {name} for {ctx['brand']}. "
                "Relatable environment, natural lighting, focus on sincere facial expressions. "
                "Speaking directly to camera with confidence and relief."
            )
            
            # Merge with template specifics
            if t_goal: full_prompt += f" Goal: {t_goal}."
            if t_visual: full_prompt += f" Visual Hint: {t_visual}."
            if t_cam: full_prompt += f" Camera Style: {t_cam}."
            
            prompts[name] = full_prompt
        return prompts
