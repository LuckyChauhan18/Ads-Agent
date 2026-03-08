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

    def critique(self, script_output: dict, campaign_context: dict) -> dict:
        """
        Evaluate a generated script and return a critique with score.

        Returns:
            {
                "score": 1-10,
                "issues": ["issue1", "issue2"],
                "suggestions": ["fix1", "fix2"]
            }
        """
        if not self.client:
            return {"score": 9, "issues": [], "suggestions": []}

        product_name = campaign_context.get("product_understanding", {}).get("product_name", "the product")
        brand_voice = campaign_context.get("brand_voice", "modern")

        scenes_text = ""
        for scene in script_output.get("scenes", []):
            scenes_text += f"\n- {scene.get('scene')}: {scene.get('voiceover', '')}"

        prompt = f"""You are an expert ad critic evaluating a video ad script.

PRODUCT: {product_name}
BRAND VOICE: {brand_voice}

SCRIPT SCENES:
{scenes_text}

Evaluate the script on each of these criteria (1-10):
1. Hook strength — Does the first scene grab attention?
2. Emotional impact — Does the ad evoke the right emotion?
3. Script length — Is the dialogue appropriate for a 15-30 second ad?
4. Story clarity — Does the narrative flow logically?
5. CTA strength — Is the call to action compelling?
6. Tone alignment — Does the tone match the brand voice?

Return ONLY valid JSON:
{{
  "score": overall_score_1_to_10,
  "issues": ["specific issue 1", "specific issue 2"],
  "suggestions": ["specific improvement 1", "specific improvement 2"]
}}

Be strict but fair. Only flag genuine issues."""

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

    def improve(self, script_output: dict, critique: dict, campaign_context: dict) -> dict:
        """
        Use the critique to improve the script.

        Returns an improved version of the script_output.
        """
        if not self.client:
            return script_output

        product_name = campaign_context.get("product_understanding", {}).get("product_name", "the product")

        scenes_json = json.dumps(script_output.get("scenes", []), indent=2)
        issues_text = "\n".join([f"- {i}" for i in critique.get("issues", [])])
        suggestions_text = "\n".join([f"- {s}" for s in critique.get("suggestions", [])])

        prompt = f"""You are improving a video ad script based on expert critique.

PRODUCT: {product_name}

CURRENT SCRIPT (JSON scenes):
{scenes_json}

ISSUES FOUND:
{issues_text}

IMPROVEMENT SUGGESTIONS:
{suggestions_text}

Improve the script to fix the issues. Keep the same JSON structure.
Return ONLY valid JSON — an array of scene objects with the same keys
(scene, voiceover, visual_description, duration_seconds, visual_continuity).

Do NOT add new scenes. Only improve existing ones."""

        try:
            response = self.client.models.generate_content(
                model="gemini-flash-latest",
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )
            improved_scenes = json.loads(response.text)

            # Handle both array and object responses
            if isinstance(improved_scenes, dict):
                improved_scenes = improved_scenes.get("scenes", improved_scenes.get("script", []))

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


def run_reflection_loop(script_output: dict, campaign_context: dict, max_iterations: int = 2) -> dict:
    """
    Main reflection loop entry point.

    Runs critique → improve cycle up to max_iterations times.
    Stops early if score >= 8.

    Returns:
        Tuple of (improved_script, reflection_results)
    """
    agent = ReflectionAgent()
    reflection_results = []
    current_script = script_output

    for i in range(max_iterations):
        print(f"\n   🔄 Reflection iteration {i + 1}/{max_iterations}")

        # Critique
        critique = agent.critique(current_script, campaign_context)
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
        current_script = agent.improve(current_script, critique, campaign_context)

    return current_script, reflection_results
