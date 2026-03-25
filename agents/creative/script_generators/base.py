import os
import math
import json
import random
from google import genai
from dotenv import load_dotenv

# Load .env
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(dotenv_path)

class BaseScriptGenerator:
    """STEP 3: Converts a Pattern Blueprint into a scene-wise ad script.
    
    This step does NOT change strategy.
    STEP 2 decides 'WHAT kind of ad'.
    STEP 3 decides 'WHAT words express it'.
    """
    
    def __init__(self, pattern_blueprint, campaign_context):
        """
        Args:
            pattern_blueprint: Output from Step 2 (the pattern_blueprint dict)
            campaign_context: Output from Step 1 (the campaign_psychology dict)
        """
        self.pattern = pattern_blueprint
        self.context = campaign_context
        
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if api_key:
            # For standard generate_content, we use default version or v1beta
            self.client = genai.Client(api_key=api_key) 
        else:
            self.client = None
    
    def _language_rules(self):
        """Hard constraints on language based on funnel stage and text density."""
        return {
            "max_lines": 1 if self.pattern.get("text_density") == "short" else 2,
            "allow_urgency": self.context.get("funnel_stage") != "cold",
            "tone": self.pattern.get("tone", "Neutral"),
            "cta": self.pattern.get("cta", "Learn More")
        }
    
    def _get_prompt_vars(self, language="Hindi", platform="Instagram Reels", ad_length=30) -> dict:
        """Helper to extract all building-block variables from contextual triggers across wrappers."""
        strategy_data = self.context.get("strategy", {})
        script_planning = strategy_data.get("script_planning", {})
        ad_template = script_planning.get("template", {})
        template_scenes = ad_template.get("scenes", [])
        
        funnel = self.context.get("funnel_stage", "cold")
        tone = self.pattern.get("tone", "Neutral")
        angle = self.pattern.get("angle", "General")
        
        product_info = self.context.get("product_understanding", {})
        product = product_info.get("product_name") or self.context.get("product_name") or "Product"
        brand = product_info.get("brand_name") or self.context.get("brand_name") or "the brand"
        category = product_info.get("category", "")
        
        problem_struct = self.context.get("strategy", {}).get("target_audience_problem", {})
        user_problem = self.context.get("user_problem_raw", "the problem")
        if isinstance(problem_struct, dict) and problem_struct.get("primary_problem"):
            user_problem = f"{problem_struct.get('primary_problem')} (Emotion: {problem_struct.get('emotional_impact', 'N/A')})"
            
        creative_dna = self.context.get("creative_dna", {})
        needs_avatar = script_planning.get("needs_avatar", True)
        
        # Calculate sum if duration is missing from top level template
        total_duration = ad_template.get("duration")
        if not total_duration and template_scenes:
            total_duration = sum(s.get("duration", 0) for s in template_scenes)
        if not total_duration:
            total_duration = ad_length
            
        duration_range = ad_template.get("duration_range", f"{total_duration-3}-{total_duration+3} seconds")

        template_structure_desc = ""
        if template_scenes:
            template_structure_desc = "\n".join([
                f"- Scene {i+1}: {s['name']} ({s['duration']}s) - Visual: {s['visual']}"
                for i, s in enumerate(template_scenes)
            ])
            
        narrative_style = creative_dna.get("narrative_style", "problem_solution")
        ad_type = script_planning.get("ad_type", "unknown")

        creative_dna_section = f"""CREATIVE DNA:
- Ad Type/Template: {ad_type}
- Targeted Duration: {total_duration}s
- Required Structure: {template_structure_desc if template_structure_desc else 'Standard 7-part flow'}
- Psychological Triggers: {', '.join(creative_dna.get('psychological_triggers', []))}"""

        lang_constraints = ""
        writer_role = f"Expert {language} Copywriter"
        
        price_range = product_info.get("price_range", "Competitive")
        target_user = product_info.get("target_user", "General Audience")
        brand_voice = self.context.get("brand_voice", "Professional")

        return {
            "writer_role": writer_role, "language": language, "product": product, "brand": brand,
            "user_problem": user_problem, "tone": tone, "brand_voice": brand_voice, "funnel": funnel, 
            "category": category, "creative_dna_section": creative_dna_section, "total_duration": total_duration, 
            "duration_range": duration_range, "template_structure_desc": template_structure_desc, 
            "needs_avatar": needs_avatar, "template_scenes": template_scenes, 
            "common_rules": ad_template.get("common_rules", []),
            "humanization": ad_template.get("humanization", {}),
            "target_user": target_user, "lang_constraints": lang_constraints
        }

    def _call_llm(self, prompt: str, language="Hindi") -> list:
        """Helper executing network API requests for modular output sets."""
        try:
            import requests
            openrouter_key = os.getenv("OPENROUTER_API_KEY")
            
            if openrouter_key:
                response = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {openrouter_key}", "Content-Type": "application/json"},
                    json={
                        "model": "openai/gpt-4o-mini",
                        "response_format": {"type": "json_object"},
                        "messages": [
                            {"role": "system", "content": "Return response wrapped in JSON with a single key 'script' containing the array of scenes: {\"script\": [{...}]}"},
                            {"role": "user", "content": prompt}
                        ]
                    },
                    timeout=60
                )
                if response.status_code == 200:
                    return json.loads(response.json()['choices'][0]['message']['content']).get("script", [])
                    
            if self.client:
                response = self.client.models.generate_content(
                    model="gemini-flash-latest", contents=prompt,
                    config={'response_mime_type': 'application/json'}
                )
                return json.loads(response.text).get("script", [])
                
        except Exception as e:
            print(f"   [Exception] Call LLM Failed: {e}")
        return []

    def generate_script_llm(self, language="Hindi", platform="Instagram Reels", ad_length=30):
        """Default template loop. Overridden by subclasses."""
        vars = self._get_prompt_vars(language, platform, ad_length)
        
        # Call LLM
        prompt = self.get_prompt_layout(vars)
        scenes = self._call_llm(prompt, language)
        
        # Scaling variables
        template_scenes = vars.get("template_scenes", [])
        total_duration = vars.get("total_duration", ad_length)
        product = vars.get("product", "Product")
        
        # Calculate scaling factor to match requested ad_length
        template_total = sum(s.get("duration", 5.0) for s in template_scenes) if template_scenes else total_duration
        scaling_factor = ad_length / template_total if template_total > 0 else 1.0
        
        processed_scenes = []
        for idx, scene in enumerate(scenes):
            if isinstance(scene, dict):
                scene_obj = scene.get("scene_objective", scene.get("scene", "Scene"))
                voice = scene.get("voiceover", scene.get("copy", ""))
                vis_desc = scene.get("visual_description", scene.get("visual_continuity", ""))
                cam_style = scene.get("camera_style", "")
                
                combined_visual = f"{vis_desc}. Camera: {cam_style}".strip()
                if combined_visual == ". Camera:": combined_visual = ""
                
                # Clean the copy
                voice = (voice or "").replace("Product", product or "Product")
                voice = voice.replace("product", product or "product")
                voice = voice.replace("प्रोडक्ट", product or "Product")
                voice = voice.replace("उत्पाद", product or "Product")
                
                # Scaled duration
                orig_duration = 5.0
                if idx < len(template_scenes):
                    orig_duration = template_scenes[idx].get("duration", 5.0)
                
                scaled_duration = round(orig_duration * scaling_factor, 1)
                # Clamping for stability (1s to 15s per scene)
                if scaled_duration < 1.0: scaled_duration = 1.0
                if scaled_duration > 15.0: scaled_duration = 15.0
                
                processed_scenes.append({
                    "scene": scene_obj,
                    "intent": scene.get("emotion", scene.get("intent", "Neutral")),
                    "voiceover": voice,
                    "visual_continuity": combined_visual,
                    "duration": scaled_duration
                })
        
        return processed_scenes

    def generate_output(self, language="Hindi", platform="Instagram Reels", ad_length=30):
        """Produces the full STEP 3 output object."""
        script = self.generate_script_llm(language, platform, ad_length)
        
        # ── Force-replace scene names with template names (authoritative) ──
        strategy_data = self.context.get("strategy", {})
        script_planning = strategy_data.get("script_planning", {})
        ad_template = script_planning.get("template", {})
        template_scenes = ad_template.get("scenes", [])
        
        if template_scenes and script:
            for idx, scene in enumerate(script):
                if idx < len(template_scenes) and isinstance(scene, dict):
                    scene["name"] = template_scenes[idx].get("name", scene.get("name", f"Scene {idx+1}"))
        
        # Build character persona for downstream propagation
        product_info = self.context.get("product_understanding", {})
        product = product_info.get("product_name") or self.context.get("product_name") or "Product"
        brand = product_info.get("brand_name") or self.context.get("brand_name") or "the brand"
        user_problem = self.context.get("user_problem_raw", "the problem")
        gender_label = self.context.get("avatar_gender", "")
        if not gender_label or gender_label.lower() in ("any", "unknown", "auto"):
            gender_label = "young person"
        
        avatar_persona = (
            f"A relatable {gender_label} in their late 20s to early 30s who personally experienced {user_problem}. "
            f"They discovered {product} by {brand} and it transformed their daily routine."
        )
        
        return {
            "campaign_id": self.context.get("campaign_id", "unknown"),
            "ad_length": ad_length,
            "platform": platform,
            "script_type": "scene_wise",
            "avatar_persona": avatar_persona,
            "pattern_used": {
                "hook_type": self.pattern.get("hook_type"),
                "opening_style": self.pattern.get("opening_style"),
                "angle": self.pattern.get("angle"),
                "tone": self.pattern.get("tone"),
                "text_density": self.pattern.get("text_density")
            },
            "scenes": script
        }

    def get_prompt_layout(self, vars: dict) -> str:
        """Default fallback prompt layout string. Subclasses override this."""
        writer_role = vars.get("writer_role")
        language = vars.get("language")
        product = vars.get("product")
        brand = vars.get("brand")
        category = vars.get("category")
        target_user = vars.get("target_user")
        user_problem = vars.get("user_problem")
        tone = vars.get("tone")
        brand_voice = vars.get("brand_voice")
        funnel = vars.get("funnel")
        lang_constraints = vars.get("lang_constraints")
        creative_dna_section = vars.get("creative_dna_section")
        total_duration = vars.get("total_duration")
        duration_range = vars.get("duration_range")
        template_structure_desc = vars.get("template_structure_desc")
        template_scenes = vars.get("template_scenes", [])
        needs_avatar = vars.get("needs_avatar")

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
{lang_constraints}
{creative_dna_section}

CRITICAL VISUAL RULES FOR VIDEO GENERATION:
1. Follow the template scene count ({len(template_scenes) if template_scenes else 7} scenes).
2. ONLY IF needs_avatar is true: The Avatar MUST speak to camera in the FIRST and LAST scenes (or according to template).
3. IF needs_avatar is false: NO faces should be shown. Focus on product and environment.
4. B-ROLL SCENES: For scenes labeled as B-roll or demonstration, use action-oriented visual descriptions (e.g., "Macro shot of product texture").
5. PRODUCT INTRODUCTION: Introduce the product {f'visually in Scene {len(template_scenes)//2 + 1}' if template_scenes else 'visually in Scene 4'}.
6. PACING: Aim for a total duration of ~{total_duration}s ({duration_range}). 
7. HUMANIZATION RULES: {vars.get('humanization', {})}
8. FLEXIBILITY: Prioritize clarity and impact over rigid second-by-second adherence.
9. COMMON RULES: {vars.get('common_rules', [])}

CRITICAL SCRIPT RULES:
1. ONE CONTINUOUS STORY: The voiceover must read like a single flowing paragraph, NOT disjointed statements.
2. NO REPETITIVE INTRODUCTIONS: Do not introduce the person multiple times. Start the hook with a strong pattern interrupt.
4. The word "{product}" MUST appear where and when natural to drive high-converting trust.
5. If an Offer is provided, mention it in the CTA.

AD TEMPLATE STRUCTURE (MUST FOLLOW):
Scene list (Do not invent new scenes, use these exact names):
{template_structure_desc if template_structure_desc else 'Standard 7-part flow'}

Generate exactly {len(template_scenes) if template_scenes else 7} scenes.
Each scene must use the exact scene name from the template list above for its 
"scene_objective".

Return ONLY valid JSON. The JSON must be an array of exactly {len(template_scenes) if template_scenes else 7} objects matching this exact format:
[
  {{
    "scene_objective": "Scene Name from Template list",
    "visual_description": "Close-up face, frustrated expression, sighing contextually.",
    "voiceover": "{language} text",
    "camera_style": "50mm lens, handheld, slight push-in",
    "emotion": "Neutral"
  }}
]"""
        return prompt
