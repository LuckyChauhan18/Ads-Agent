import json
import os
import random
from typing import List, Dict
from collections import Counter
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# Load .env from root directory (parent of src)
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)

# ── Constants for  creative  differentiation ─────────────────────────

PSYCHOLOGICAL_TRIGGERS = [
    "curiosity_gap",
    "social_proof",
    "authority",
    "fear_of_missing_out",
    "future_self_visualization",
    "pain_amplification",
    "identity_alignment",
    "contrast_principle",
    "loss_aversion",
    "reciprocity",
]

NARRATIVE_STYLES = [
    "founder_story",
    "customer_story",
    "problem_solution",
    "day_in_life",
    "before_after",
    "myth_busting",
]

# Strategy for deliberately breaking competitor patterns
HOOK_BREAK_STRATEGIES = {
    "Emotion": "Use curiosity or contrarian hook instead",
    "Curiosity": "Use emotional storytelling instead",
    "Question": "Use bold declarative statement hook instead",
    "Problem": "Use aspirational future vision instead",
    "Statement": "Use vulnerable confession or question hook instead",
}

TONE_BREAK_STRATEGIES = {
    "Neutral": "Use raw, relatable storytelling",
    "Serious": "Use playful, self-aware tone",
    "Friendly": "Use expert authority tone",
    "Professional": "Use casual, behind-the-scenes tone",
    "Aggressive": "Use calm, understated confidence",
}

# Memory file path
MEMORY_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "memory")
WINNING_CAMPAIGNS_FILE = os.path.join(MEMORY_DIR, "winning_campaigns.json")


class CampaignPsychologyEngine:
    FUNNEL_RULES = {
        "cold": {
            "allowed_cta": ["Discover the Secret", "See How it Works", "Experience the Story"],
            "focus": "impact_discovery",
            "urgency": "low",
            "voice_directive": "Be a relatable friend sharing a discovery, not a salesperson."
        },
        "warm": {
            "allowed_cta": ["See the Transformation", "Hear from the Community", "Explore Features"],
            "focus": "impact_validation",
            "urgency": "medium",
            "voice_directive": "Be a trusted guide validating their needs with proof."
        },
        "hot": {
            "allowed_cta": ["Start Your Journey", "Try it Risk-Free", "Join the Brand"],
            "focus": "impact_transformation",
            "urgency": "high",
            "voice_directive": "Be the bridge to their desired transformation, focusing on value over price."
        }
    }

    def __init__(self, founder_input: Dict, competitor_data: List[Dict], api_key: str = None):
        self.founder_input = founder_input
        self.competitor_data = competitor_data
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")

        # ── Improvement #6: temperature 0.7 for creative variation ──
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            openai_api_key=self.api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.7,
            timeout=60  # Added timeout to prevent hanging
        )

    # ────────────────────────────────────────────────────────────────
    # Validation
    # ────────────────────────────────────────────────────────────────

    def validate_inputs(self):
        required_fields = [
            "funnel_stage",
            "platform"
        ]
        for field in required_fields:
            if field not in self.founder_input or not self.founder_input[field]:
                raise ValueError(f"Missing required field in founder_input: {field}")

        if self.founder_input["funnel_stage"] not in self.FUNNEL_RULES:
            raise ValueError(f"Invalid funnel stage: {self.founder_input['funnel_stage']}")

        if not self.founder_input.get("user_problem_raw"):
            self.founder_input["user_problem_raw"] = "Not specified"

        if not self.founder_input.get("primary_emotions"):
            self.founder_input["primary_emotions"] = ["Curiosity"]

        return True

    # ────────────────────────────────────────────────────────────────
    # Market Context (unchanged core, enriched output)
    # ────────────────────────────────────────────────────────────────

    def get_market_context(self) -> Dict:
        """Aggregates ALL competitor ads into frequency distributions."""
        total = len(self.competitor_data)
        if total == 0:
            return self._default_market_context()

        hook_types, tones, angles, ctas, text_lengths, punch_lines = [], [], [], [], [], []

        for ad in self.competitor_data:
            dna = ad.get("dna", {})
            if dna.get("hook_type"): hook_types.append(dna["hook_type"])
            if dna.get("tone"): tones.append(dna["tone"])
            if dna.get("angle"): angles.append(dna["angle"])
            if dna.get("cta"): ctas.append(dna["cta"])
            if dna.get("text_length"): text_lengths.append(dna["text_length"])
            if dna.get("punch_line") and dna["punch_line"] != "string":
                punch_lines.append(dna["punch_line"])

        def to_weights(items):
            if not items:
                return {}
            counts = Counter(items)
            return {k: round(v / len(items), 2) for k, v in counts.items()}

        def classify_signals(weights):
            return {
                "baseline": {k: v for k, v in weights.items() if v >= 0.6},
                "variation": {k: v for k, v in weights.items() if 0.2 <= v < 0.6},
                "weak": {k: v for k, v in weights.items() if v < 0.2},
            }

        def text_density_bucket(length):
            if length < 150: return "short"
            elif length < 350: return "medium"
            else: return "long"

        text_buckets = [text_density_bucket(t) for t in text_lengths]
        hook_weights = to_weights(hook_types)
        tone_weights = to_weights(tones)
        angle_weights = to_weights(angles)
        cta_weights = to_weights(ctas)
        density_weights = to_weights(text_buckets)

        def dominant(weights, fallback="Unknown"):
            return max(weights, key=weights.get) if weights else fallback

        return {
            "total_ads_analyzed": total,
            "dominant_hook_type": dominant(hook_weights, "Emotion"),
            "dominant_tone": dominant(tone_weights, "Neutral"),
            "dominant_angle": dominant(angle_weights, "General"),
            "common_cta": dominant(cta_weights, "Learn More"),
            "dominant_text_density": dominant(density_weights, "medium"),
            "hook_type_weights": hook_weights,
            "tone_weights": tone_weights,
            "angle_weights": angle_weights,
            "cta_weights": cta_weights,
            "text_density_weights": density_weights,
            "signal_tiers": {
                "hook_type": classify_signals(hook_weights),
                "tone": classify_signals(tone_weights),
                "angle": classify_signals(angle_weights),
                "cta": classify_signals(cta_weights),
                "text_density": classify_signals(density_weights),
            },
            "avg_text_length": round(sum(text_lengths) / len(text_lengths)) if text_lengths else 0,
            "top_punch_lines": punch_lines[:5],
        }

    def _default_market_context(self):
        return {
            "total_ads_analyzed": 0,
            "dominant_hook_type": "Emotion",
            "dominant_tone": "Neutral",
            "dominant_angle": "General",
            "common_cta": "Learn More",
            "dominant_text_density": "medium",
            "hook_type_weights": {"Emotion": 1.0},
            "tone_weights": {"Neutral": 1.0},
            "angle_weights": {"General": 1.0},
            "cta_weights": {"Learn More": 1.0},
            "text_density_weights": {"medium": 1.0},
            "signal_tiers": {},
            "avg_text_length": 200,
        }

    # ────────────────────────────────────────────────────────────────
    # Improvement #1: Pattern Break Strategy
    # ────────────────────────────────────────────────────────────────

    def generate_pattern_break(self, market_context: Dict) -> Dict:
        """Deliberately break competitor patterns to stand out."""
        dominant_hook = market_context.get("dominant_hook_type", "Emotion")
        dominant_tone = market_context.get("dominant_tone", "Neutral")

        return {
            "hook_pattern_break": HOOK_BREAK_STRATEGIES.get(dominant_hook, "Use contrarian hook"),
            "tone_pattern_break": TONE_BREAK_STRATEGIES.get(dominant_tone, "Use unexpected tone"),
            "rationale": (
                f"Competitors mostly use '{dominant_hook}' hooks with '{dominant_tone}' tone. "
                f"We deliberately break this pattern to capture attention in a crowded feed."
            ),
        }

    # ────────────────────────────────────────────────────────────────
    # Improvement #3: Market Gap Detection
    # ────────────────────────────────────────────────────────────────

    def detect_market_gaps(self, market_context: Dict) -> List[str]:
        """Find underused angles that competitors ignore."""
        angle_weights = market_context.get("angle_weights", {})
        gaps = [angle for angle, weight in angle_weights.items() if weight < 0.2]

        if not gaps:
            gaps = ["Behind-the-scenes", "Founder story", "User journey"]

        return gaps[:3]

    # ────────────────────────────────────────────────────────────────
    # Improvement #4: Hook Pattern Extraction
    # ────────────────────────────────────────────────────────────────

    def extract_hook_patterns(self) -> Dict:
        """Learn hook STRUCTURE from competitor scripts, not just frequency."""
        hooks = []
        for ad in self.competitor_data:
            text = ad.get("dna", {}).get("punch_line", "") or ad.get("script", "")
            if not text:
                continue
            first_80 = text[:80].lower()
            if "?" in first_80:
                hooks.append("question_hook")
            elif first_80.startswith("what if"):
                hooks.append("curiosity_hook")
            elif "ever" in first_80 or "remember" in first_80:
                hooks.append("relatable_hook")
            elif "most people" in first_80 or "nobody" in first_80:
                hooks.append("contrarian_hook")
            elif first_80.startswith(("don't", "stop", "never")):
                hooks.append("negative_hook")
            else:
                hooks.append("statement_hook")

        distribution = dict(Counter(hooks))
        dominant = max(distribution, key=distribution.get) if distribution else "statement_hook"
        return {
            "hook_structure_distribution": distribution,
            "dominant_hook_structure": dominant,
        }

    # ────────────────────────────────────────────────────────────────
    # Improvement #8: Creative DNA (bundles 1-5)
    # ────────────────────────────────────────────────────────────────

    # Removed random build_creative_dna pick loop to use LLM structures instead.

    # ────────────────────────────────────────────────────────────────
    # Improvement #9: Winning Strategy Memory
    # ────────────────────────────────────────────────────────────────

    def _load_winning_campaigns(self) -> List[Dict]:
        """Load historical winning campaigns from memory."""
        if os.path.exists(WINNING_CAMPAIGNS_FILE):
            try:
                with open(WINNING_CAMPAIGNS_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def save_winning_campaign(self, campaign_data: Dict) -> None:
        """Save a campaign result to the winning strategies memory."""
        os.makedirs(MEMORY_DIR, exist_ok=True)
        history = self._load_winning_campaigns()
        entry = {
            "timestamp": datetime.now().isoformat(),
            "hook_type": campaign_data.get("creative_dna", {}).get("pattern_break", {}).get("hook_pattern_break", ""),
            "narrative_style": campaign_data.get("creative_dna", {}).get("narrative_style", ""),
            "psychological_triggers": campaign_data.get("creative_dna", {}).get("psychological_triggers", []),
            "angle": campaign_data.get("market_context", {}).get("dominant_angle", ""),
            "tone": campaign_data.get("brand_voice", ""),
            "funnel_stage": campaign_data.get("funnel_stage", ""),
        }
        history.append(entry)
        # Keep last 50 entries
        history = history[-50:]
        with open(WINNING_CAMPAIGNS_FILE, "w") as f:
            json.dump(history, f, indent=2)
        print(f"   💾 Campaign saved to winning strategies memory ({len(history)} total)")

    def _get_past_strategies_summary(self) -> str:
        """Summarize past campaigns to avoid repetition."""
        history = self._load_winning_campaigns()
        if not history:
            return "No past campaigns on record."

        recent = history[-5:]
        lines = []
        for h in recent:
            lines.append(
                f"  - Style: {h.get('narrative_style')}, "
                f"Triggers: {', '.join(h.get('psychological_triggers', []))}, "
                f"Hook: {h.get('hook_type')}"
            )
        return "Recent past campaigns (AVOID repeating these exact combos):\n" + "\n".join(lines)

    # ────────────────────────────────────────────────────────────────
    # Main generation (Improvements #6, #7, #8 — core rewrite)
    # ────────────────────────────────────────────────────────────────

    def generate_campaign_psychology(self) -> Dict:
        self.validate_inputs()

        market_context = self.get_market_context()
        funnel_stage = self.founder_input["funnel_stage"]

        # Generate pattern break & market context
        pattern_break = self.generate_pattern_break(market_context)
        market_gaps = self.detect_market_gaps(market_context)
        past_summary = self._get_past_strategies_summary()

        # ── STRUCTURED PROBLEM EXTRACTION ──
        problem_structure = self.founder_input.get("target_audience_problem", {})
        structured_desc = ""
        if isinstance(problem_structure, dict) and any(problem_structure.values()):
            structured_desc = f"""
- Primary Problem: {problem_structure.get('primary_problem', '')}
- Root Cause: {problem_structure.get('root_cause', '')}
- Emotional Impact: {problem_structure.get('emotional_impact', '')}
- Desired Outcome: {problem_structure.get('desired_outcome', '')}"""

        # ── CANDIDATE STRATEGY OPTIONS ──
        candidate_narratives = ["Problem -> Discovery -> Transformation", "Science Proof & Breakdown", "Lifestyle Routine / Day in the Life", "Social Proof Showcase", "Contrarian Belief Narrative", "Myth Busting / educational"]
        candidate_hooks = ["Contrarian (Surprising/Counter-intuitive)", "Problem Disclosure", "Curiosity (Open Loop)", "Aspirational Future Visualization", "Vulnerable confession"]
        candidate_visuals = ["Aesthetic Lifestyle", "Product Demonstration closeups", "Home Routine / GRWM style", "Dynamic B-Roll Montage"]
        candidate_proofs = ["Product demonstration demo", "Before/After result", "Customer testimonial review"]
        candidate_ctas = ["Discover the Secret", "Try Now Risk-Free", "Claim limited offer", "See it working"]

        prompt = f"""You are a world-class direct response advertising strategist. Your goal is to create a structured CREATIVE DNA for an ad campaign that strictly avoids generic marketing statements.

═══════════════════════════════════════
FOUNDER INTENT & CAMPAIGN DATA
═══════════════════════════════════════
- Funnel Stage: {funnel_stage} (Allowed focus: {self.FUNNEL_RULES[funnel_stage]["focus"]})
- Product Category Focus: {self.founder_input.get("category_focus", "General")}
- Primary Emotions: {", ".join(self.founder_input.get("primary_emotions", []))}
- Structured Pain Points: {structured_desc if structured_desc else "Not Structured"}
- Raw Context Problem: {self.founder_input.get("user_problem_raw", "None")}
- Objections: {", ".join(self.founder_input.get("objections", []))}
- Trust Signals: {", ".join(self.founder_input.get("trust_signals_available", []))}
- Offer Details: {json.dumps(self.founder_input.get("offer_and_risk_reversal", {}))}
- Brand Voice: {self.founder_input.get("brand_voice")}
- Platform: {self.founder_input.get("platform")}

═══════════════════════════════════════
MARKET INTELLIGENCE (Differentiate)
═══════════════════════════════════════
- Dominant hook competitors use: {market_context.get("dominant_hook_type")}
- Common angles: {market_context.get("dominant_angle")}
- Suggested Pattern Break: {pattern_break["hook_pattern_break"]}
- Underused Angles (Market Gaps): {", ".join(market_gaps)}

═══════════════════════════════════════
ALLOWED CREATIVE OPTIONS (Pick EXACT selectors)
═══════════════════════════════════════
1. Narrative Style candidates: {candidate_narratives}
2. Hook Mechanism candidates: {candidate_hooks}
3. Visual Style candidates: {candidate_visuals}
4. Proof Type candidates: {candidate_proofs}
5. CTA Type candidates: {candidate_ctas}

═══════════════════════════════════════
YOUR TASK (Return JSON)
═══════════════════════════════════════
Determine the structured Creative DNA for this campaign. 
Pick ONE item for each field from the Allowed Creative Options lists above that best suits the product and funnel stage.

Return ONLY a JSON object with this exact structure:
{{
  "creative_dna": {{
    "narrative_type": "Exact item from Narrative list",
    "hook_mechanism": "Exact item from Hook list",
    "visual_style": "Exact item from Visual list",
    "psychology_trigger": "Curiosity OR Confidence OR Relief",
    "proof_type": "Exact item from Proof list",
    "cta_type": "Exact item from CTA list",
    "hook_line_recommendation": "A bold specific sample hook sentence based on the mechanism picked"
  }},
  "empathy_statement": "Detailed sentence reflecting user's real pain point.",
  "objection_handling_plan": "Short description of how to handle objections.",
  "final_brief": "Vivid energetic summary describing the flow of how these fit together."
}}
"""
        try:
            print(f"   📡 Calling LLM for Creative DNA generation...")
            response = self.llm.invoke([
                SystemMessage(content="You are an advertising strategist who strictly structures Creative DNA outputs. Return ONLY JSON."),
                HumanMessage(content=prompt)
            ])
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()

            refined_strategy = json.loads(content)
            creative_dna = refined_strategy.get("creative_dna", {})

            # Standard wrapper mapping for pipeline
            campaign_psychology = {
                "campaign_id": self.founder_input.get("campaign_id", "unnamed"),
                "funnel_stage": funnel_stage,
                "emotions": self.founder_input.get("primary_emotions", ["Curiosity"]),
                "user_problem_raw": self.founder_input.get("user_problem_raw", "Problem not specified"),
                "objections": self.founder_input.get("objections", []),
                "trust_signals": self.founder_input.get("trust_signals_available", []),
                "offer": self.founder_input.get("offer_and_risk_reversal", {}),
                "platform": self.founder_input.get("platform", "instagram"),
                "brand_voice": self.founder_input.get("brand_voice", "Neutral"),
                "market_context": market_context,
                "creative_dna": creative_dna,
                "ai_strategy": refined_strategy
            }

            self.save_winning_campaign(campaign_psychology)
            return campaign_psychology

        except Exception as e:
            print(f"   ⚠️ AI Psychology generation failed: {e}.")
            return {
                "campaign_id": self.founder_input.get("campaign_id", "unnamed"),
                "funnel_stage": funnel_stage,
                "market_context": market_context,
                "creative_dna": {
                    "narrative_type": candidate_narratives[0],
                    "hook_mechanism": candidate_hooks[2],
                    "visual_style": candidate_visuals[0],
                    "psychology_trigger": "Curiosity",
                    "proof_type": candidate_proofs[0],
                    "cta_type": candidate_ctas[0],
                    "hook_line_recommendation": "Check this out."
                },
                "ai_strategy": {"final_brief": "Fallback strategy"}
            }


if __name__ == "__main__":
    sample_founder = {
        "funnel_stage": "cold",
        "primary_emotions": ["curiosity", "frustration"],
        "user_problem_raw": "My running shoes look good but start hurting after long runs",
        "objections": ["quality", "return"],
        "trust_signals_available": ["reviews", "easy_return"],
        "offer_and_risk_reversal": {"free_shipping": True},
        "platform": "meta_reels",
        "brand_voice": "relatable"
    }

    sample_competitor = [{
        "brand": "Competitor X",
        "dna": {
            "hook_type": "Emotion",
            "tone": "Neutral",
            "angle": "Style",
            "cta": "Learn More",
            "text_length": 428,
            "punch_line": "Feel the difference from the first step"
        }
    }]

    engine = CampaignPsychologyEngine(sample_founder, sample_competitor)
    result = engine.generate_campaign_psychology()
    print(json.dumps(result, indent=2))
