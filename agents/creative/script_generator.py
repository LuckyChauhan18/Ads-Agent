import os
import math
import json
import random
from google import genai
from dotenv import load_dotenv

# Load .env
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)

# --- Step 3: Scene Intent Map (WHY each scene exists) ---
SCENE_INTENT = {
    "Hook": "Stop scroll with relatable pain",
    "Problem": "Deepen frustration and self-identification",
    "Relatable Moment": "Mirror user experience to build connection",
    "Solution": "Introduce product as relief (no hype)",
    "Trust": "Remove fear and objections",
    "Proof": "Concrete evidence that it works",
    "CTA": "Low-pressure next step"
}

# --- Sentence Templates (Upgraded for Depth and Realism) ---
TEMPLATES = {
    "Hook": [
        "Ever felt like you're doing everything right but still not getting the results you expected?",
        "Most people don't realize this mistake until it's already costing them time, money, or energy.",
        "What if the real reason things aren't working isn't your effort… but the system you're using?",
        "You start with excitement… but somewhere along the way frustration takes over."
    ],

    "Problem": [
        "At first it feels manageable. But slowly the small problems start stacking up until the experience becomes exhausting.",
        "You try different options hoping something will finally work, but the result is always the same disappointment.",
        "The worst part isn't the difficulty — it's the feeling that something should be easier than this.",
        "And over time, that frustration slowly kills motivation and confidence."
    ],

    "Relatable Moment": [
        "If you've experienced this before, you're definitely not alone.",
        "Almost everyone goes through this phase before discovering a better way.",
        "It's that moment where you start wondering if there's a smarter solution."
    ],

    "Solution": [
        "That's where {product} changes the experience completely.",
        "{product} was designed to remove the friction and make the process simple again.",
        "Instead of struggling through the same problems, {product} helps you move forward with confidence.",
        "The difference isn't just small improvements — it's a completely smoother experience."
    ],

    "Trust": [
        "Thousands of people have already made the switch and shared their positive experiences.",
        "Built with reliability and long-term usability in mind.",
        "Designed based on real user feedback and real-world challenges."
    ],

    "Proof": [
        "Users consistently report noticeable improvements after switching.",
        "Rated highly by people who previously struggled with the same problems.",
        "Trusted by a growing community of satisfied users."
    ],

    "CTA": [
        "{cta} and experience the difference for yourself.",
        "{cta} to see why more people are switching.",
        "{cta} and start improving your experience today."
    ]
}



class ScriptGenerator:
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
    
    def _inject_tone(self, line, scene):
        """Applies tone modifiers based on the blueprint's tone setting."""
        tone = self.pattern.get("tone", "Neutral")
        
        if tone == "Empathetic" and scene in ["Hook", "Problem"]:
            line = "We get it. " + line
        elif tone == "Friendly" and scene == "Hook":
            line = "Hey, " + line[0].lower() + line[1:]
        
        return line
    
    def _inject_trust_signals(self, line):
        """Replaces generic trust copy with actual trust signals from Step 1."""
        signals = self.context.get("trust_signals", [])
        if not signals:
            return line
        
        # Map trust signals to human-readable phrases
        signal_phrases = {
            "customer_reviews": "real customer reviews",
            "7_day_return": "a 7-day easy return",
            "easy_return": "a hassle-free return policy",
            "reviews": "verified reviews",
            "guarantee": "a money-back guarantee",
            "free_shipping": "free shipping"
        }
        
        readable = [signal_phrases.get(s, s) for s in signals]
        if len(readable) >= 2:
            return f"Backed by {readable[0]} and {readable[1]}."
        elif len(readable) == 1:
            return f"Backed by {readable[0]}."
        
        return line
    
    def generate_script_llm(self, language="Hindi", platform="Instagram Reels", ad_length=30):
        """Uses Gemini AI to generate a high-quality ad script in the target language."""
        if not self.client:
            print("   Gemini client not initialized for Script. Falling back to templates.")
            return self.generate_script(fallback=True)
            
        # Calculate required scenes based on user request:
        if ad_length >= 60:
            scene_count = 9
        elif ad_length >= 45:
            scene_count = 6
        elif ad_length >= 30:
            scene_count = 4
        else:
            scene_count = math.ceil(ad_length / 6)
            
        scene_count = max(2, scene_count) # Minimum Hook + CTA
        
        print(f"   Generating {language} script for {platform} ({ad_length}s, {scene_count} scenes) with Gemini AI...")
        
        funnel = self.context.get("funnel_stage", "cold")
        tone = self.pattern.get("tone", "Neutral")
        angle = self.pattern.get("angle", "General")
        
        # Robust name extraction from context
        product_info = self.context.get("product_understanding", {})
        product = product_info.get("product_name") or self.context.get("product_name") or "Product"
        brand = product_info.get("brand_name") or self.context.get("brand_name") or "the brand"
        
        features = product_info.get("features", [])
        user_problem = self.context.get("user_problem_raw", "the problem")
        category = product_info.get("category", "")
        
        # Detect available visual assets for better visual_continuity suggestions
        product_images = product_info.get("product_images", [])
        logo_images = product_info.get("logos", [])
        image_count = len(product_images)
        logo_count = len(logo_images)
        
        if language.lower() == "hindi":
            lang_constraints = """STRICT HINDI CONSTRAINTS:
1. All ad copy MUST be in pure, high-impact Hindi (Devanagari script).
2. Use relatable, emotional language (not formal translation).
3. Do NOT use English words or Latin script.
4. Keep each scene copy around 20-25 words (about 2 full lines) to properly explain the concept."""
            writer_role = f"Native Hindi Advertising Copywriter for {category}"
        elif language.lower() == "english":
            lang_constraints = """STRICT ENGLISH CONSTRAINTS:
1. All ad copy MUST be in short, punchy English.
2. Use conversational, emotionally resonant language.
3. Keep each scene copy around 20-25 words (about 2 full lines) to properly explain the concept.
4. Be bold, direct, and action-oriented."""
            writer_role = f"Expert English Advertising Copywriter for {category}"
        else:
            lang_constraints = f"""STRICT {language.upper()} CONSTRAINTS:
1. All ad copy MUST be in native {language} script.
2. Use emotionally resonant, relatable language.
3. Keep each scene copy around 20-25 words (about 2 full lines) to properly explain the concept."""
            writer_role = f"Native {language} Advertising Copywriter for {category}"
        
        # Extract Founder insights: offer and audience
        offer_info = self.context.get("offer_and_risk_reversal", {})
        # Flatten offers if it's a list
        offers = offer_info.get("offers", [])
        offer_str = ", ".join([f"{o.get('discount', '')} ({o.get('guarantee', '')})" for o in offers if o.get('discount')])
        
        brand_voice = self.context.get("brand_voice", "Professional")
        
        # ── Extract Creative DNA for differentiation ──
        creative_dna = self.context.get("creative_dna", {})
        narrative_style = creative_dna.get("narrative_style", "problem_solution")
        psych_triggers = creative_dna.get("psychological_triggers", [])
        pattern_break = creative_dna.get("pattern_break", {})
        hook_break = pattern_break.get("hook_pattern_break", "")
        tone_break = pattern_break.get("tone_pattern_break", "")
        market_gaps = creative_dna.get("market_gaps", [])
        
        # Build creative DNA section for prompt
        creative_dna_section = ""
        if creative_dna:
            creative_dna_section = f"""
CREATIVE DNA (MUST USE — this makes the ad UNIQUE):
- Narrative Style: {narrative_style} — structure the ad as a {narrative_style.replace('_', ' ')}
- Psychological Triggers: {', '.join(psych_triggers)} — weave these into the copy naturally
- Pattern Break Hook: {hook_break}
- Pattern Break Tone: {tone_break}
- Market Gaps to exploit: {', '.join(market_gaps)}

DO NOT write a generic ad. Use the narrative style and triggers above.

PLATFORM STYLE GUIDELINES:
- TikTok/Reels/Shorts: UGC style, high energy, fast cuts, trending audio vibe.
- YouTube: Informative, steady pacing, clear value proposition.
- LinkedIn: Professional, results-driven, industry-specific vocabulary.
- Meta Feed: Relatable, family/lifestyle focus, clear headlines.
- Current Platform: {platform}
"""
        
        prompt = f"""You are a {writer_role}.
Create a high-converting {language} video ad script for {product} by {brand}.

The ad must feel AUTHENTIC, HUMAN, and UNIQUE — not like a corporate script.

CAMPAIGN DETAILS:
- Product: {product}
- Brand: {self.context.get('product_understanding', {}).get('brand_name', '')}
- Category: {category}
- Features: {', '.join(features[:5]) if features else 'N/A'}
- Funnel Stage: {funnel}
- Tone: {tone} (Style: {brand_voice})
- Angle: {angle}
- User Problem: {user_problem}
- SPECIFIC OFFERS (MUST USE THESE NUMBERS/DETAILS): {offer_str if offer_str else "NONE PROVIDED - DO NOT MENTION ANY DISCOUNTS OR OFFERS"}
- Flow: Hook, Problem, Solution, Trust, Proof, CTA
{lang_constraints}
{creative_dna_section}

VISUAL ASSETS AVAILABLE:
- Product Images: {image_count} different shots of the product.
- Logos: {logo_count} brand logo variants.

CRITICAL VISUAL RULES (B-ROLL OVER TALKING HEADS):
1. The Hook and CTA scenes MUST feature the Avatar (person talking).
2. The INTERMEDIATE scenes (Problem, Solutions, Proof, etc.) MUST BE B-ROLL (No Faces). 
3. Describe DIFFERENT visual scenarios across the intermediate scenes (e.g., 'Close up of the heel detail', 'Wide shot of product in use', 'Top-down flat lay'). Do NOT describe 'person talking' or 'influencer looking at camera' for the middle scenes. Provide action-oriented B-roll.

CRITICAL RULES (DO NOT IGNORE):
1. The word "{product}" MUST appear literally in Solution and CTA copy.
2. SPECIFIC OFFER DETAILS: If an offer is provided in the DETAILS above, you MUST mention those exact numbers/terms in the CTA or Solution scene. IF NONE PROVIDED, DO NOT INVENT A FAKE DISCOUNT. 
3. AUDIENCE FIT: Write the dialogue to sound natural for {platform} users experiencing {user_problem}.
4. Problem scene MUST show {category}-specific pain.
5. Hook should feel authentic to {category} users.
6. USE THE CREATIVE DNA to make this script DIFFERENT from typical {category} ads.
7. DURATION CONSTRAINT: You MUST generate exactly {scene_count} scenes to fit the {ad_length}s target duration.

WARNING: If Solution or CTA copy does NOT contain "{product}" by name, or ignores the SPECIFIC OFFER rules, the output is INVALID.

Return ONLY valid JSON with exactly {scene_count} scenes. 

STRICT SCENE STRUCTURE:
1. The FIRST scene (index 0) MUST be named "Hook".
2. Subsequent scenes can have creative names relevant to the ad content (e.g., "Problem Breakdown", "Visual Metaphor", "The Transformation", "Feature Spotlight", "Rapid Fire Benefits").
3. The FINAL scene MUST be the "CTA".

FORMAT:
[
  {{"scene": "Hook", "intent": "Stop scroll", "copy": "{language} text about {category} world", "visual_continuity": "Establish environment"}},
  ... ({scene_count - 2} intermediate scenes with creative, descriptive names relevant to the script flow)
  {{"scene": "CTA", "intent": "Drive action", "copy": "{language} text WITH {product} name + BUY NOW", "visual_continuity": "Final payoff"}}
]
"""
        try:
            import requests
            openrouter_key = os.getenv("OPENROUTER_API_KEY")
            
            if openrouter_key:
                print(f"   Generating {language} script with OpenRouter (GPT-4o-mini)...")
                response = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {openrouter_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "openai/gpt-4o-mini",
                        "response_format": {"type": "json_object"},
                        "messages": [
                            {"role": "system", "content": "You are a professional ad scriptwriter. Always return your response wrapped in a JSON object with a single key 'script' containing the array of scenes, like: {\"script\": [{...}, {...}]}"},
                            {"role": "user", "content": prompt}
                        ]
                    },
                    timeout=60
                )
                if response.status_code == 200:
                    resp_json = response.json()
                    script_text = resp_json['choices'][0]['message']['content']
                    script = json.loads(script_text)
                else:
                    raise Exception(f"OpenRouter API returned {response.status_code}: {response.text}")
            elif self.client:
                print(f"   Generating {language} script with Gemini AI...")
                response = self.client.models.generate_content(
                    model="gemini-flash-latest",
                    contents=prompt,
                    config={'response_mime_type': 'application/json'}
                )
                script = json.loads(response.text)
            else:
                raise Exception("No AI clients available.")

            
            # Handle if LLM returns a dict with 'script' key instead of a list
            if isinstance(script, dict) and "script" in script:
                scenes = script["script"]
            elif isinstance(script, list):
                scenes = script
            else:
                scenes = script
            
            # Post-process: replace generic 'Product' with actual product name
            processed_scenes = []
            for scene in scenes:
                if isinstance(scene, dict):
                    # Standardize fields for frontend
                    scene_type = scene.get("scene", "Scene")
                    intent = scene.get("intent", "")
                    copy = scene.get("copy", "")
                    
                    # Clean the copy
                    copy = copy.replace("Product", product)
                    copy = copy.replace("product", product)
                    copy = copy.replace("प्रोडक्ट", product)
                    copy = copy.replace("उत्पाद", product)
                    
                    processed_scenes.append({
                        "scene": scene_type,
                        "intent": intent,
                        "voiceover": copy,
                        "visual_continuity": scene.get("visual_continuity", "")
                    })
            
            return processed_scenes
        except Exception as e:
            print(f"   LLM Script failed: {e}. Falling back.")
            return self.generate_script(fallback=True)

    def generate_script(self, fallback=False):
        """Standard template-based generator."""
        rules = self._language_rules()
        script = []
        
        scene_flow = self.pattern.get("scene_flow", ["Hook", "Problem", "Solution", "CTA"])
        
        for scene in scene_flow:
            candidates = TEMPLATES.get(scene, [])
            if not candidates:
                continue
            
            # Pick a random template
            line = random.choice(candidates)
            
            # Format CTA into template
            # Format CTA into template
            if scene == "CTA":
                # NEW: Use synthesized winning punch line if available
                strategy = self.context.get("ai_strategy", {})
                winning_punch = strategy.get("winning_punch_line_strategy", {}).get("punch_line")
                if winning_punch:
                    line = winning_punch
                else:
                    line = line.format(cta=rules["cta"])

            
            # Apply tone injection

            line = self._inject_tone(line, scene)
            
            # Replace generic trust with real signals
            if scene == "Trust":
                line = self._inject_trust_signals(line)
            
            # Replace basic Product placeholder with actual product name
            product_info = self.context.get("product_understanding", {})
            product_name = product_info.get("product_name") or self.context.get("product_name") or "Product"
            line = line.replace("Product", product_name).replace("product", product_name).replace("प्रोडक्ट", product_name).replace("उत्पाद", product_name)
            
            script.append({
                "scene": scene,
                "intent": SCENE_INTENT.get(scene, "Convey message"),
                "voiceover": line
            })
        
        return script
    
    def generate_output(self, language="Hindi", platform="Instagram Reels", ad_length=30):
        """Produces the full STEP 3 output object."""
        script = self.generate_script_llm(language, platform, ad_length)
        return {
            "campaign_id": self.context.get("campaign_id", "unknown"),
            "ad_length": ad_length,
            "platform": platform,
            "script_type": "scene_wise",
            "pattern_used": {
                "hook_type": self.pattern.get("hook_type"),
                "opening_style": self.pattern.get("opening_style"),
                "angle": self.pattern.get("angle"),
                "tone": self.pattern.get("tone"),
                "text_density": self.pattern.get("text_density")
            },
            "scenes": script
        }


if __name__ == "__main__":
    # Test with local files
    bp_path = os.path.join("output", "pattern_blueprint.json")
    ctx_path = os.path.join("output", "campaign_psychology.json")
    
    if os.path.exists(bp_path) and os.path.exists(ctx_path):
        with open(bp_path, "r") as f:
            bp_data = json.load(f)
        with open(ctx_path, "r") as f:
            ctx_data = json.load(f)
        
        # Extract the pattern_blueprint from the Step 2 output
        pattern = bp_data.get("pattern_blueprint", bp_data)
        
        gen = ScriptGenerator(pattern, ctx_data)
        print(json.dumps(gen.generate_output(), indent=2))
    else:
        print("Missing pattern_blueprint.json or campaign_psychology.json in output/")
