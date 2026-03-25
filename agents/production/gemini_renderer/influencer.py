from .base import BaseRenderer
from google.genai import types
from typing import Dict, List

class InfluencerRenderer(BaseRenderer):
    """Renderer specialized for Influencer/UGC ads.
    Focuses on the avatar as the relatable 'friend' recommending the product."""

    async def _get_reference_images_for_scene(self, scene: Dict) -> List:
        scene_name = scene.get("name", scene.get("scene", "")).lower()
        references = []

        # Influencer ads rely heavily on the Avatar Reference for Hook/CTA/Discovery
        # Handled in BaseRenderer via _get_character_description but we can add ASSET refs here too
        
        # Discovery/Solution/Proof: Show product
        product_scenes = ["discovery", "solution", "proof", "showing product"]
        if any(kw in scene_name for kw in product_scenes):
            for img_id in self.assets.get("product", [])[:2]:
                img = await self._load_image_for_veo(img_id)
                if img: references.append(types.VideoGenerationReferenceImage(image=img, reference_type="ASSET"))

        # CTA: Logo + Product
        elif "cta" in scene_name:
            # Add logo
            if self.assets.get("logo"):
                img = await self._load_image_for_veo(self.assets["logo"][0])
                if img: references.append(types.VideoGenerationReferenceImage(image=img, reference_type="ASSET"))
            # Add product
            if self.assets.get("product"):
                img = await self._load_image_for_veo(self.assets["product"][0])
                if img: references.append(types.VideoGenerationReferenceImage(image=img, reference_type="ASSET"))

        return references[:3]

    def _generate_scene_prompts(self, scene_list: List[Dict]) -> Dict[str, str]:
        """Prompts tailored for UGC style: slightly more handheld, authentic lighting, domestic settings."""
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
                f"UGC style video of {name} for {ctx['brand']}. "
                "Authentic setting, natural lighting, relatable vibe. "
                "Speaking directly to viewer like a friend."
            )
            
            # Merge with template specifics
            if t_goal: full_prompt += f" Goal: {t_goal}."
            if t_visual: full_prompt += f" Visual Hint: {t_visual}."
            if t_cam: full_prompt += f" Camera Style: {t_cam}."
            
            prompts[name] = full_prompt + " High quality."
        return prompts
