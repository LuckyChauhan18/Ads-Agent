from .base import BaseRenderer
from google.genai import types
from typing import Dict, List

class LifestyleRenderer(BaseRenderer):
    """Renderer specialized for Aspirational/Lifestyle ads."""

    async def _get_reference_images_for_scene(self, scene: Dict) -> List:
        scene_name = scene.get("name", scene.get("scene", "")).lower()
        references = []

        # Lifestyle relies on 'Aesthetic Hook' and 'Daily Routine'
        if "hook" in scene_name or "routine" in scene_name:
            if self.assets.get("lifestyle"):
                # Use lifestyle images to set the mood
                for img_id in self.assets["lifestyle"][:2]:
                    img = await self._load_image_for_veo(img_id)
                    if img: references.append(types.VideoGenerationReferenceImage(image=img, reference_type="ASSET"))

        # Interaction/CTA: Product focus
        elif "interaction" in scene_name or "cta" in scene_name or "brand" in scene_name:
            if self.assets.get("product"):
                img = await self._load_image_for_veo(self.assets["product"][0])
                if img: references.append(types.VideoGenerationReferenceImage(image=img, reference_type="ASSET"))
            if "brand" in scene_name and self.assets.get("logo"):
                img = await self._load_image_for_veo(self.assets["logo"][0])
                if img: references.append(types.VideoGenerationReferenceImage(image=img, reference_type="ASSET"))

        return references[:3]

    def _generate_scene_prompts(self, scene_list: List[Dict]) -> Dict[str, str]:
        """Cinematic, rhythm-focused, and mood-heavy prompts."""
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
                f"High-end lifestyle video of {name} for {ctx['brand']}. "
                "Bright, vibrant, aesthetic environment. "
                f"Premium cinematic quality showing {ctx['product_name']} in an aspirational context."
            )
            
            # Merge with template specifics
            if t_goal: full_prompt += f" Goal: {t_goal}."
            if t_visual: full_prompt += f" Visual Hint: {t_visual}."
            if t_cam: full_prompt += f" Camera Style: {t_cam}."
            
            prompts[name] = full_prompt
        return prompts
