from .base import BaseScriptGenerator

class LifestyleScriptGenerator(BaseScriptGenerator):
    """Script Generator for Lifestyle-style ads."""
    
    @property
    def default_needs_avatar(self) -> bool:
        return False

    def generate_script_llm(self, language="Hindi", platform="Instagram Reels", ad_length=30):
        """Custom story type script generator for Lifestyle-style."""
        vars = self._get_prompt_vars(language, platform, ad_length)
        
        writer_role = vars.get("writer_role")
        product = vars.get("product")
        brand = vars.get("brand")
        category = vars.get("category")
        target_user = vars.get("target_user")
        user_problem = vars.get("user_problem")
        tone = vars.get("tone")
        brand_voice = vars.get("brand_voice")
        funnel = vars.get("funnel")
        competitor_insight_section = vars.get("competitor_insight_section")
        lang_constraints = vars.get("lang_constraints")
        total_duration = vars.get("total_duration")
        duration_range = vars.get("duration_range")
        template_structure_desc = vars.get("template_structure_desc")
        template_scenes = vars.get("template_scenes", [])
        common_rules = vars.get("common_rules", [])

        rules_str = "\n".join([f"- {rule}" for rule in common_rules]) if common_rules else "- Focus on aesthetic B-roll and product utility."

        # No persona strings for product-only styles
        prompt = f"""You are a {writer_role}.
Create a high-converting, psychologically persuasive {language} video ad script for {product} by {brand}.

We are moving AWAY from generic product explanations and static talking-heads.
The ad MUST follow the dynamic AD TEMPLATE structure defined below based on competitor insights and audience psychology.

CAMPAIGN DETAILS & PSYCHOLOGY:
- Product: {product}
- Category: {category}
- Target Audience: {target_user}
- User Problem: {user_problem}
- Tone: {tone} (Style: {brand_voice})
- Funnel Stage: {funnel}
- Narrative Anchor: Relief and Transformation
{competitor_insight_section}
{lang_constraints}

CRITICAL VISUAL RULES FOR VIDEO GENERATION:
1. No narrator avatar is used. Focus on high-quality B-roll, close-ups, and smooth transitions.
2. Follow the template scene count ({len(template_scenes) if template_scenes else 6} scenes).
3. NO faces should be shown. Focus on environments, textures, and product interaction.
4. PACING: Aim for a total duration of ~{total_duration}s ({duration_range}). 

AD TYPE COMMON RULES (MUST FOLLOW):
{rules_str}

AD TEMPLATE STRUCTURE (MUST FOLLOW EXACTLY):
Scene list (Do not invent new scenes, use these EXACT names):
{template_structure_desc if template_structure_desc else 'Standard Lifestyle structural flow'}

Generate exactly {len(template_scenes) if template_scenes else 6} scenes.
Each scene must use the exact scene name from the template list above for its "name".

CRITICAL GUIDELINES FOR HIGH-CONVERTING ADS:
1. **Avoid Generic Phrases**: Do NOT use terms like 'best performance', 'ultimate experience', 'high quality'. Use specific, visual, in-action scenario language describing emotions or lifestyles.
2. **Visual Voiceovers**: Each voiceover MUST describe what is happening on screen, or frame the benefit within a visual scenario lifestyle payoff.
3. **Pacing**: The total script duration must be EXACTLY {total_duration} seconds.
4. **Visual Consistency**: Consistent grading and environments across all scenes. No sudden background climate changes unless dictated strictly by pacing layouts.
5. **Realism Guideline**: Avoid perfect CGI look. Add slight imperfections, natural motion, realistic lighting behavior, and physical accuracy.

Return ONLY valid JSON. The JSON must be an array of exactly {len(template_scenes) if template_scenes else 6} objects matching this exact format:
[
  {{
    "name": "Scene Name from Template list",
    "visual": "Cinematic B-roll description matching rule specs.",
    "voiceover": "{language} text",
    "camera_style": "Camera angle or movement specs",
    "emotion": "Neutral"
  }}
]"""
        return self._call_llm(prompt, language)
