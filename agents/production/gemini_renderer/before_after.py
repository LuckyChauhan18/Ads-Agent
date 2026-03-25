from .base import BaseRenderer
from google.genai import types
from typing import Dict, List

class BeforeAfterRenderer(BaseRenderer):
    """Renderer specialized for Comparison/Transformation ads."""

    async def _get_reference_images_for_scene(self, scene: Dict) -> List:
        scene_name = scene.get("name", scene.get("scene", "")).lower()
        references = []

        # 'Before' scene: Focus on pain (maybe user provided a 'before' image in lifestyle?)
        if "before" in scene_name or "struggle" in scene_name:
            # We don't have a specific 'before' category, so we rely on prompts mostly
            # Unless we check metadata of lifestyle assets for 'before' keywords?
            pass

        # 'After' / 'Discovery' / 'Works'
        elif "after" in scene_name or "relief" in scene_name or "discovery" in scene_name:
            if self.assets.get("product"):
                img = await self._load_image_for_veo(self.assets["product"][0])
                if img: references.append(types.VideoGenerationReferenceImage(image=img, reference_type="ASSET"))
            if self.assets.get("lifestyle"):
                # Ideally this is the 'After' result image
                img = await self._load_image_for_veo(self.assets["lifestyle"][0])
                if img: references.append(types.VideoGenerationReferenceImage(image=img, reference_type="ASSET"))

        elif "cta" in scene_name:
            if self.assets.get("logo"):
                img = await self._load_image_for_veo(self.assets["logo"][0])
                if img: references.append(types.VideoGenerationReferenceImage(image=img, reference_type="ASSET"))

        return references[:3]

    def _generate_scene_prompts(self, scene_list: List[Dict]) -> Dict[str, str]:
        """Prompts with high visual contrast (Dull vs Vibrant) + Template specificity."""
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

            if "before" in name.lower() or "struggle" in name.lower():
                base = f"STARK CONTRAST - BEFORE STATE: {name}. Dull lighting, desaturated colors, close-up on the pain of {ctx['user_problem']}."
            else:
                base = f"STARK CONTRAST - AFTER STATE: {name}. Burst of vibrant colors, bright high-key lighting, dynamic motion, joy and relief."

            # Merge with template specifics
            full_prompt = base
            if t_goal: full_prompt += f" Goal: {t_goal}."
            if t_visual: full_prompt += f" Visual Hint: {t_visual}."
            if t_cam: full_prompt += f" Camera: {t_cam}."
            
            prompts[name] = full_prompt + " High cinematic quality."
        return prompts
