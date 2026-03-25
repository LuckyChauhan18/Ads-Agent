"""
Agent Reflection Loop — Self-Critique and Improvement.

Runs after the Creative Agent to evaluate and improve the generated
script/storyboard before it is sent to Production.

Loop logic:
  1. Critique the output (score 1-10)
  2. If score < 8, improve the output
  3. Max 2 iterations
"""

import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()


class ReflectionAgent:
    """
    Self-critique agent that evaluates generated ad scripts.

    Checks: Hook strength, emotional impact, script length,
            clarity, CTA strength, tone alignment.
    """

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = None
            print("   ⚠️ ReflectionAgent: No Gemini API key found.")

    def critique(self, script_output: dict, campaign_context: dict, ad_type: str = "product_demo") -> dict:
        """
        Evaluate a generated script and return a critique with score.
        """
        if not self.client:
            return {"score": 9, "issues": [], "suggestions": []}

        # campaign_context is now strategy_data
        campaign_psychology = campaign_context.get("campaign_psychology", campaign_context)
        product_name = campaign_psychology.get("product_understanding", {}).get("product_name", "the product")
        brand_voice = campaign_psychology.get("brand_voice", "modern")

        # Extract Dynamic Template Rules
        ad_template = campaign_context.get("script_planning", {}).get("template", {})
        common_rules = ad_template.get("common_rules", [])
        needs_avatar = ad_template.get("needs_avatar", True)
        description = ad_template.get("description", "Standard Ad")

        rules_text = "\n".join([f"- {r}" for r in common_rules]) if common_rules else "- Standard ad flow"

        scenes_text = ""
        for i, scene in enumerate(script_output.get("scenes", [])):
            scenes_text += f"\n- Scene {i+1} [{scene.get('scene', 'N/A')}]:"
            scenes_text += f"\n  VOICEOVER: {scene.get('voiceover', scene.get('copy', ''))}"
            scenes_text += f"\n  VISUAL: {scene.get('visual_description', scene.get('visual_continuity', 'N/A'))}\n"

        prompt = f"""You are an expert ad critic evaluating a video ad script.

PRODUCT: {product_name}
BRAND VOICE: {brand_voice}
AD TYPE: {ad_type}
AD DESCRIPTION: {description}

SCRIPT SCENES:
{scenes_text}

CRITICAL AD TYPE DYNAMIC RULES (MUST VERIFY):
- Needs Avatar: {needs_avatar}
{rules_text}

Below is a strict checklist for a {ad_type} ad. Critique this script based on:
1. **Hook Strength (First 3-5s)** — Is the first scene visually striking? Does the `visual_continuity` specify an arresting image? Does the opening line create an immediate curiosity gap or emotional trigger?
2. **Visual Feasibility** — Can the `visual_continuity` be realistically rendered by a standard AI video generator (e.g., Gemini Veo 3.1)? Avoid overly complex physics or impossible camera moves.
3. **Script Pacing** — Is the line length realistic for a 15-30 second ad?
4. **Story Clarity** — Does the narrative flow logically from scene to scene?
5. **CTA Strength (Final Scene)** — Does the LAST scene containing the Call To Action feel compelling and clear?
6. **Tone & Rules Alignment** — Does the pacing match the intended brand voice and obey the ad type guidelines above?

Return ONLY valid JSON:
{{
  "score": overall_score_1_to_10,
  "issues": ["specific issue 1", "specific issue 2"],
  "suggestions": ["specific improvement 1", "specific improvement 2"]
}}

Be strict but fair. Only flag genuine issues. Avoid reviewing scenes out-of-context; for example, do not expect a hook in the middle of the script."""

        try:
            response = self.client.models.generate_content(
                model="gemini-flash-latest",
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )
            result = json.loads(response.text)
            print(f"   🔍 Reflection score: {result.get('score', 'N/A')}/10")
            return result
        except Exception as e:
            print(f"   ⚠️ Reflection failed: {e}. Passing through.")
            return {"score": 9, "issues": [], "suggestions": []}

    def improve(self, script_output: dict, critique: dict, campaign_context: dict, ad_type: str = "product_demo") -> dict:
        """
        Use the critique to improve the script.

        Returns an improved version of the script_output.
        """
        if not self.client:
            return script_output

        # campaign_context is now strategy_data
        campaign_psychology = campaign_context.get("campaign_psychology", campaign_context)
        product_name = campaign_psychology.get("product_understanding", {}).get("product_name", "the product")

        # Extract Dynamic Template Rules for improvement context
        ad_template = campaign_context.get("script_planning", {}).get("template", {})
        common_rules = ad_template.get("common_rules", [])
        rules_text = "\n".join([f"- {r}" for r in common_rules]) if common_rules else "- Standard ad flow"

        scenes_json = json.dumps(script_output.get("scenes", []), indent=2)
        issues_text = "\n".join([f"- {i}" for i in critique.get("issues", [])])
        suggestions_text = "\n".join([f"- {s}" for s in critique.get("suggestions", [])])

        prompt = f"""You are improving a video ad script based on expert critique and template rules.

PRODUCT: {product_name}

CURRENT SCRIPT (JSON scenes):
{scenes_json}

AD TYPE: {ad_type}

AD TYPE RULES TO MAINTAIN:
{rules_text}

ISSUES FOUND:
{issues_text}

IMPROVEMENT SUGGESTIONS:
{suggestions_text}

Improve the script to fix the issues while strictly respecting the ad type rules. Keep the same JSON structure.
Return ONLY valid JSON — an array of scene objects with the exact same keys:
(scene, voiceover, visual_continuity, duration).

Do NOT add new scenes. Only improve existing ones."""

        try:
            response = self.client.models.generate_content(
                model="gemini-flash-latest",
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )
            
            # Robust JSON parsing
            try:
                raw_text = response.text.strip()
                improved_data = json.loads(raw_text)
            except json.JSONDecodeError:
                # Attempt to extract JSON if LLM added markdown blockers
                import re
                match = re.search(r'\[.*\]', raw_text, re.DOTALL)
                if match:
                    improved_data = json.loads(match.group(0))
                else:
                    raise

            # Handle both array and object responses (look for 'scenes')
            if isinstance(improved_data, dict):
                improved_scenes = improved_data.get("scenes", improved_data.get("script", []))
            else:
                improved_scenes = improved_data

            if isinstance(improved_scenes, list) and len(improved_scenes) > 0:
                improved_output = script_output.copy()
                improved_output["scenes"] = improved_scenes
                improved_output["reflection_improved"] = True
                print(f"   ✨ Script improved by reflection agent")
                return improved_output

            return script_output
        except Exception as e:
            print(f"   ⚠️ Improvement failed: {e}. Returning original.")
            return script_output


def run_reflection_loop(script_output: dict, campaign_context: dict, ad_type: str = "product_demo", max_iterations: int = 2) -> tuple:
    """
    Main reflection loop entry point.
    """
    agent = ReflectionAgent()
    reflection_results = []
    current_script = script_output

    for i in range(max_iterations):
        print(f"\n   🔄 Reflection iteration {i + 1}/{max_iterations}")

        # Critique
        critique = agent.critique(current_script, campaign_context, ad_type=ad_type)
        score = critique.get("score", 10)
        reflection_results.append({
            "iteration": i + 1,
            "score": score,
            "issues": critique.get("issues", []),
        })

        # If score is good enough, stop
        if score >= 8:
            print(f"   ✅ Score {score}/10 — passing through.")
            break

        # Improve
        print(f"   ⚡ Score {score}/10 — improving...")
        current_script = agent.improve(current_script, critique, campaign_context, ad_type=ad_type)

    return current_script, reflection_results
