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
            temperature=0.7
        )

    # ────────────────────────────────────────────────────────────────
    # Validation
    # ────────────────────────────────────────────────────────────────

    def validate_inputs(self):
        required_fields = [
            "funnel_stage",
            "user_problem_raw",
            "platform"
        ]
        for field in required_fields:
            if field not in self.founder_input or not self.founder_input[field]:
                raise ValueError(f"Missing required field in founder_input: {field}")

        if self.founder_input["funnel_stage"] not in self.FUNNEL_RULES:
            raise ValueError(f"Invalid funnel stage: {self.founder_input['funnel_stage']}")

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

    def build_creative_dna(self, market_context: Dict) -> Dict:
        """Build a unique creative fingerprint for this campaign."""
        return {
            # #5: Narrative style
            "narrative_style": random.choice(NARRATIVE_STYLES),
            # #2: Psychological triggers
            "psychological_triggers": random.sample(PSYCHOLOGICAL_TRIGGERS, 3),
            # #1: Pattern break
            "pattern_break": self.generate_pattern_break(market_context),
            # #3: Market gaps
            "market_gaps": self.detect_market_gaps(market_context),
            # #4: Hook patterns
            "hook_patterns": self.extract_hook_patterns(),
        }

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

        # ── Build unique creative DNA for this campaign ──
        creative_dna = self.build_creative_dna(market_context)
        past_summary = self._get_past_strategies_summary()

        # ── Build feedback section for prompt ──
        feedback_section = ""
        feedback = getattr(self, "feedback", None)
        if feedback:
            feedback_section = f"\nCRITICAL FEEDBACK FROM PREVIOUS RUN (MUST FIX):\n\"{feedback}\"\n"

        # ── Improvement #7: Drastically improved LLM prompt ──
        prompt = f"""You are a world-class direct response advertising strategist.

Your goal is NOT to copy competitors or shout "BUY NOW".
Your goal is to create a psychologically impactful ad strategy
that makes the user DESIRE the product through authentic storytelling.

The ad should feel:
- IMPACT-FIRST: Show the transformation or the moment of relief clearly.
- SOFT-SELL: Never say "buy directly" or "purchase now" in the narrative. 
- AUTHENTIC: High-impact emotional believability.
- CONVERSATIONAL: Like a real person sharing a life-changing secret.

═══════════════════════════════════════
FOUNDER INTENT
═══════════════════════════════════════
- Funnel Stage: {funnel_stage}
- Primary Emotions: {", ".join(self.founder_input.get("primary_emotions", []))}
- Raw User Problem: {self.founder_input.get("user_problem_raw")}
- Objections: {", ".join(self.founder_input.get("objections", []))}
- Trust Signals: {", ".join(self.founder_input.get("trust_signals_available", []))}
- Offer Details: {json.dumps(self.founder_input.get("offer_and_risk_reversal", {}))}
- Brand Voice: {self.founder_input.get("brand_voice")}
- Platform: {self.founder_input.get("platform")}

═══════════════════════════════════════
MARKET INTELLIGENCE (What competitors do)
═══════════════════════════════════════
- Ads Analyzed: {market_context.get("total_ads_analyzed")}
- Dominant Hook: {market_context.get("dominant_hook_type")}
- Dominant Tone: {market_context.get("dominant_tone")}
- Dominant Angle: {market_context.get("dominant_angle")}
- Competitor Punch Lines: {", ".join(market_context.get("top_punch_lines", []))}
- Hook Structures Found: {json.dumps(creative_dna["hook_patterns"]["hook_structure_distribution"])}

═══════════════════════════════════════
CREATIVE DNA (How to differentiate)
═══════════════════════════════════════
- Narrative Style: {creative_dna["narrative_style"]}
- Psychological Triggers to Use: {", ".join(creative_dna["psychological_triggers"])}
- Pattern Break Hook: {creative_dna["pattern_break"]["hook_pattern_break"]}
- Pattern Break Tone: {creative_dna["pattern_break"]["tone_pattern_break"]}
- Market Gaps (underused angles): {", ".join(creative_dna["market_gaps"])}

═══════════════════════════════════════
PAST CAMPAIGN MEMORY
═══════════════════════════════════════
{past_summary}

═══════════════════════════════════════
FUNNEL RULES
═══════════════════════════════════════
- Focus: {self.FUNNEL_RULES[funnel_stage]["focus"]}
- Urgency: {self.FUNNEL_RULES[funnel_stage]["urgency"]}
- Allowed CTAs: {", ".join(self.FUNNEL_RULES[funnel_stage]["allowed_cta"])}

═══════════════════════════════════════
YOUR TASK
═══════════════════════════════════════
Create a campaign strategy that uses the CREATIVE DNA above.
DO NOT produce a generic strategy. Use the pattern breaks and
psychological triggers provided. Make the ad feel HUMAN and UNIQUE.

Return ONLY a JSON object with these keys:
1. "psychological_hook_strategy": Detailed hook plan using the PATTERN BREAK.
2. "empathy_statement": A raw, authentic sentence reflecting the user's real pain.
3. "objection_handling_plan": How to address the specific objections naturally.
4. "recommended_angles": List of 3 SPECIFIC ad angles that exploit MARKET GAPS.
5. "competitor_success_logic": Why competitor ads work + how we BEAT them.
6. "winning_punch_line_strategy": {{
    "framework": "The template (e.g., 'Confession + Revelation')",
    "punch_line": "A unique, non-generic punch line for our product."
}}
7. "narrative_approach": How to use the '{creative_dna["narrative_style"]}' style.
8. "trigger_implementation": How each trigger ({", ".join(creative_dna["psychological_triggers"])}) appears in the ad.
9. "compliance_reminders": Constraints and reminders.
10. "final_brief": A vivid, energetic summary paragraph for the copywriter.
"""

        try:
            response = self.llm.invoke([
                SystemMessage(content=(
                    "You are a world-class direct-response advertising strategist "
                    "known for creating ads that feel authentic, emotionally powerful, "
                    "and dramatically different from competitors. Return ONLY JSON."
                )),
                HumanMessage(content=prompt)
            ])

            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()

            refined_strategy = json.loads(content)

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
                "funnel_constraints": self.FUNNEL_RULES.get(funnel_stage, self.FUNNEL_RULES["cold"]),
                "ai_strategy": refined_strategy,
                # ── NEW: Creative DNA embedded in output ──
                "creative_dna": creative_dna,
            }

            # ── Improvement #9: Save to winning campaigns memory ──
            self.save_winning_campaign(campaign_psychology)

            return campaign_psychology

        except Exception as e:
            print(f"   ⚠️ AI Psychology generation failed: {e}. Falling back to basic object.")
            creative_dna_fallback = self.build_creative_dna(market_context)
            return {
                "campaign_id": self.founder_input.get("campaign_id", "unnamed"),
                "funnel_stage": funnel_stage,
                "emotions": self.founder_input.get("primary_emotions", ["Curiosity"]),
                "user_problem_raw": self.founder_input.get("user_problem_raw", "Problem not specified"),
                "objections": self.founder_input.get("objections", []),
                "trust_signals": self.founder_input.get("trust_signals_available", []),
                "offer": self.founder_input.get("offer_and_risk_reversal", {}),
                "platform": self.founder_input.get("platform", "instagram"),
                "brand_voice": self.founder_input.get("brand_voice", "Neutral"),
                "cta_preference": self.founder_input.get("cta_preference"),
                "market_context": market_context,
                "funnel_constraints": self.FUNNEL_RULES.get(funnel_stage, self.FUNNEL_RULES["cold"]),
                "creative_dna": creative_dna_fallback,
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
