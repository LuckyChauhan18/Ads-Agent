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
            
        # Enforce strict 7-part advertising framework requested by user
        scene_count = 7
        
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
        
        # --- Build Character Persona for story consistency ---
        gender_label = self.context.get("avatar_gender", "")
        if not gender_label or gender_label.lower() in ("any", "unknown", "auto"):
            gender_label = "young person"
        
        character_persona = (
            f"A relatable {gender_label} in their late 20s to early 30s who personally experienced {user_problem}. "
            f"They discovered {product} by {brand} and it transformed their daily routine. "
            f"The ad follows THEIR authentic journey: frustration, discovery, transformation."
        )

        # Extract research and pricing data
        price_range = product_info.get("price_range", "Competitive")
        target_user = product_info.get("target_user", "General Audience")
        
        # Extract research / competitor insights
        research_data = self.context.get("research", {})
        competitor_results = research_data.get("competitor_results", [])
        top_competitor_punchlines = []
        for res in competitor_results:
            if res.get("top_punchline"):
                top_competitor_punchlines.append(res["top_punchline"])
        
        competitor_insight_section = ""
        if top_competitor_punchlines:
            competitor_insight_section = f"- Successful Competitor Hook/Taglines: {', '.join(top_competitor_punchlines[:3])}"

        prompt = f"""You are a {writer_role}.
Create a high-converting, psychologically persuasive {language} video ad script for {product} by {brand}.

We are moving AWAY from generic product explanations and static talking-heads.
The ad MUST follow a strict 7-part emotional advertising structure based on competitor insights and audience psychology.

CHARACTER PERSONA (USE CONSISTENTLY ACROSS ALL SCENES):
{character_persona}
- The SAME person appears ONLY in the Hook and CTA scenes. They are the narrator throughout.
- Write the script as THEIR personal story. Use first-person perspective where natural.
- The character's emotional journey MUST flow chronologically: Frustrated -> Agitated -> Relieved -> Transformed -> Confident.

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
{creative_dna_section}

CRITICAL VISUAL RULES FOR VIDEO GENERATION:
1. Scene 1 (Hook) and Scene 7 (CTA) MUST feature the Avatar speaking to the camera.
2. Scenes 2, 3, 4, 5, and 6 MUST BE B-ROLL (No Faces).
3. Do NOT describe "person talking" for the intermediate scenes. Use action-oriented B-roll (e.g., "Macro shot of product texture", "Hands struggling with problem", "Wide atmospheric shot of messy room").
4. Product MUST ONLY be introduced visually in Scene 4. Do NOT show the product directly in Scenes 1, 2, or 3.

CRITICAL SCRIPT RULES:
1. ONE CONTINUOUS STORY: The voiceover must read like a single flowing paragraph, NOT disjointed statements.
2. NO REPETITIVE INTRODUCTIONS: Do not introduce the person multiple times. Start the hook with a strong pattern interrupt.
3. COMPETITOR INSIGHT: The Hook (Scene 1) MUST use the insights from "Successful Competitor Hook/Taglines" to create a compelling pattern interrupt.
4. The word "{product}" MUST appear literally in Scene 4 and Scene 7.
5. If an Offer is provided, mention it in the CTA.

STRICT 7-PART SCENE STRUCTURE (YOU MUST RETURN EXACTLY 7 SCENES):
1. "Hook": Pattern interrupt based on audience pain point.
2. "Problem": Identify the problem visually and verbally. 
3. "Agitation": Deepen the emotional pain of the problem.
4. "Solution": Product introduction (First visual reveal of the product).
5. "Benefits": Key benefits linked directly back to the pain points.
6. "Transformation": Show the result/outcome using the product.
7. "CTA": Clear call to action from the Hook actor.

Return ONLY valid JSON. The JSON must be an array of exactly 7 objects matching this exact format:
[
  {{
    "scene_objective": "Hook",
    "visual_description": "Close-up face, frustrated expression, sighing contextually.",
    "voiceover": "{language} text",
    "camera_style": "50mm lens, handheld, slight push-in",
    "emotion": "Frustrated"
  }},
  {{
    "scene_objective": "Problem",
    "visual_description": "...",
    "voiceover": "...",
    "camera_style": "...",
    "emotion": "..."
  }}
]"""
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
            
            # Post-process mapping for downstream compatibility
            processed_scenes = []
            for scene in scenes:
                if isinstance(scene, dict):
                    scene_obj = scene.get("scene_objective", scene.get("scene", "Scene"))
                    voice = scene.get("voiceover", scene.get("copy", ""))
                    vis_desc = scene.get("visual_description", scene.get("visual_continuity", ""))
                    cam_style = scene.get("camera_style", "")
                    
                    combined_visual = f"{vis_desc}. Camera: {cam_style}".strip()
                    if combined_visual == ". Camera:": combined_visual = ""
                    
                    # Clean the copy
                    voice = voice.replace("Product", product)
                    voice = voice.replace("product", product)
                    voice = voice.replace("प्रोडक्ट", product)
                    voice = voice.replace("उत्पाद", product)
                    
                    processed_scenes.append({
                        "scene": scene_obj,
                        "intent": scene.get("emotion", scene.get("intent", "Neutral")),
                        "voiceover": voice,
                        "visual_continuity": combined_visual
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
