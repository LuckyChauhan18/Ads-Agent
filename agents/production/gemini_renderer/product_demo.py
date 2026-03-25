from .base import BaseRenderer
from google.genai import types
from typing import Dict, List

class ProductDemoRenderer(BaseRenderer):
    """Renderer specialized for Product Demo ads. 
    Maps Reveal/Feature scenes back to product assets."""

    async def _get_reference_images_for_scene(self, scene: Dict) -> List:
        scene_name = scene.get("scene", "").lower()
        references = []

        # Reveal/Solution scenes get product images
        product_keywords = ["reveal", "solution", "feature", "introduce", "result", "benefit"]
        if any(kw in scene_name for kw in product_keywords):
            for img_id in self.assets.get("product", [])[:2]:
                img = await self._load_image_for_veo(img_id)
                if img:
                    references.append(types.VideoGenerationReferenceImage(
                        image=img, reference_type="ASSET"
                    ))
        
        # CTA gets logo + product
        elif "cta" in scene_name or "drive action" in scene_name:
            if self.assets.get("logo"):
                img = await self._load_image_for_veo(self.assets["logo"][0])
                if img: references.append(types.VideoGenerationReferenceImage(image=img, reference_type="ASSET"))
            if self.assets.get("product"):
                img = await self._load_image_for_veo(self.assets["product"][0])
                if img: references.append(types.VideoGenerationReferenceImage(image=img, reference_type="ASSET"))

        return references[:3]

    def _generate_scene_prompts(self, scene_list: List[Dict]) -> Dict[str, str]:
        """Custom prompts for product demos (macro, high-end commercial style)."""
        ctx = self._get_scene_context()
        ad_template = self.context.get("ad_template", {})
        template_scenes = ad_template.get("scenes", [])
        
        prompts = {}
        for s in scene_list:
            name = s.get("scene", "")
            vis_cont = s.get("visual_continuity", "")
            
            is_problem = any(kw in name.lower() for kw in ["problem", "pain", "situation", "hook", "struggle", "intro"])
            
            if is_problem:
                full_prompt = (
                    f"Cinematic 8k video. {vis_cont} "
                    "Ultra-photorealistic, high-end commercial style, cinematic lighting."
                )
            else:
                full_prompt = (
                    f"Cinematic 8k environmental B-roll video for {ctx['brand']}. "
                    f"Atmosphere should reflect {ctx['product_name']}. {vis_cont} "
                    "DO NOT generate the product itself, only generate the beautiful background environment and atmospheric effects. "
                    "Ultra-photorealistic, high-end commercial studio lighting, macro detail, stunning cinematic lighting."
                )
            
            # Find matching template scene for metadata
            t_scene = next((ts for ts in template_scenes if ts.get("name") == name), {})
            t_cam = t_scene.get("camera_style", "")
            if t_cam: full_prompt += f" Camera Style: {t_cam}."
            
            prompts[name] = full_prompt
        return prompts
