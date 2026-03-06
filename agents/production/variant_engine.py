import json
import os
import copy
from typing import List, Dict
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# Load .env from root directory (parent of src)
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)


class VariantEngine:
    """STEP 6: Generates creative variants from the locked storyboard.
    
    What stays SAME:
    - Storyboard structure
    - Avatar configuration
    - Assets / bindings
    - Scene order / durations
    
    What varies:
    - Hook line (1-2 alternate phrasings)
    - CTA line (optional softer/stronger phrasing)
    - Delivery emphasis notes
    
    This avoids re-rendering identical videos and prevents creative fatigue.
    """
    
    def __init__(self, storyboard_output, script_output, campaign_context):
        """
        Args:
            storyboard_output: Output from Step 5
            script_output: Output from Step 3
            campaign_context: Output from Step 1
        """
        self.storyboard = storyboard_output
        self.script = script_output
        self.context = campaign_context
        
        api_key = os.getenv("OPENROUTER_API_KEY")
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.7  # Slightly creative for variant generation
        )
    
    def _generate_hook_variants(self, original_hook: str) -> List[str]:
        """Uses AI to generate alternate hook phrasings."""
        pattern = self.script.get("pattern_used", {})
        tone = pattern.get("tone", "Neutral")
        angle = pattern.get("angle", "General")
        user_problem = self.context.get("user_problem_raw", "")
        
        prompt = f"""Generate exactly 2 alternate hook lines for a short video ad.

ORIGINAL HOOK: "{original_hook}"

CONSTRAINTS:
- Tone: {tone}
- Angle: {angle}
- User Problem: {user_problem}
- Must be scroll-stopping (2-3 seconds spoken)
- Keep same emotional intent as original
- Do NOT change the meaning, just rephrase
- Do NOT use urgency or aggressive language (cold funnel)
- Keep under 20 words each

Return ONLY a JSON array of 2 strings. No explanation.
Example: ["Hook variant 1", "Hook variant 2"]"""

        try:
            response = self.llm.invoke([
                SystemMessage(content="You are an expert ad copywriter. Return ONLY valid JSON."),
                HumanMessage(content=prompt)
            ])
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        except Exception as e:
            print(f"   AI hook generation failed: {e}. Using rule-based fallback.")
            return self._fallback_hook_variants(original_hook)
    
    def _fallback_hook_variants(self, original_hook: str) -> List[str]:
        """Rule-based fallback for hook variants."""
        variants = []
        
        # Variant 1: Question style
        if not original_hook.endswith("?"):
            words = original_hook.rstrip(".!").split()
            variants.append("Ever noticed " + " ".join(words[2:]).lower() + "?")
        else:
            variants.append(original_hook.replace("Have you", "Ever").replace("?", " too?"))
        
        # Variant 2: Statement style
        if original_hook.endswith("?"):
            core = original_hook.rstrip("?").replace("Have you noticed ", "").replace("We get it. ", "")
            variants.append(f"Here's the thing — {core.lower()}.")
        else:
            variants.append(f"Real talk — {original_hook.lower()}")
        
        return variants[:2]
    
    def _generate_cta_variants(self, original_cta: str) -> List[str]:
        """Generates softer/stronger CTA phrasings."""
        cta_variants = {
            "Watch Now and see the difference.": [
                "See what's different — tap below.",
                "Curious? Take a quick look."
            ],
            "Learn More": [
                "Explore Now",
                "See for Yourself"
            ],
            "Buy Now": [
                "Get Yours Today",
                "Start Your Order"
            ]
        }
        
        if original_cta in cta_variants:
            return cta_variants[original_cta]
        
        # Generic fallback
        return [
            f"Tap to {original_cta.lower().replace('learn more', 'explore')}",
            f"Ready? {original_cta}"
        ]
    
    def generate_variants(self) -> List[Dict]:
        """Core STEP 6: Generates 3 variants (A = original, B & C = variations)."""
        storyboard = self.storyboard.get("storyboard", [])
        
        # Find the Hook and CTA scenes
        hook_scene = None
        cta_scene = None
        for scene in storyboard:
            if scene["scene"] == "Hook":
                hook_scene = scene
            if scene["scene"] == "CTA":
                cta_scene = scene
        
        if not hook_scene:
            print("   No Hook scene found. Returning original only.")
            return [{"variant": "A", "label": "Original", "storyboard": storyboard}]
        
        original_hook = hook_scene["voiceover"]
        original_cta = cta_scene["voiceover"] if cta_scene else ""
        
        print("   Generating hook variants...")
        hook_variants = self._generate_hook_variants(original_hook)
        cta_variants = self._generate_cta_variants(original_cta) if cta_scene else []
        
        variants = []
        
        # Variant A: Original (untouched)
        variants.append({
            "variant": "A",
            "label": "Original",
            "changes": "None — base script",
            "storyboard": copy.deepcopy(storyboard)
        })
        
        # NOTE: Variant B and C disabled for speed optimization
        # Users now requested only one variant.
        
        return variants
    
    def generate_output(self) -> Dict:
        """Produces the full STEP 6 output object."""
        variants = self.generate_variants()
        
        return {
            "campaign_id": self.context.get("campaign_id", "unknown"),
            "total_variants": len(variants),
            "variant_strategy": "Hook + CTA variation only. Structure, avatar, assets remain locked.",
            "variants": variants
        }


if __name__ == "__main__":
    storyboard_path = os.path.join("output", "storyboard.json")
    script_path = os.path.join("output", "script_output.json")
    ctx_path = os.path.join("output", "campaign_psychology.json")
    
    if all(os.path.exists(p) for p in [storyboard_path, script_path, ctx_path]):
        with open(storyboard_path, "r") as f:
            storyboard_data = json.load(f)
        with open(script_path, "r") as f:
            script_data = json.load(f)
        with open(ctx_path, "r") as f:
            ctx_data = json.load(f)
        
        engine = VariantEngine(storyboard_data, script_data, ctx_data)
        output = engine.generate_output()
        print(json.dumps(output, indent=2))
    else:
        print("Missing required files in output/")
