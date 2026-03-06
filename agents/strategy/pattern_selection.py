import random
import json
import os

# --- Step 2: Pattern Design Space ---
PATTERN_SPACE = {
    "hook_type": ["Problem", "Curiosity", "Relatable", "Authority"],
    "opening_style": [
        "Story-based",
        "POV Relatable",
        "Problem-first",
        "Comparison"
    ],
    "angle": ["Comfort", "Performance", "Trust", "Lifestyle"],
    "tone": ["Neutral", "Friendly", "Empathetic"],
    "scene_flow": [
        ["Hook", "Problem", "Relatable Moment", "Solution", "Trust", "CTA"],
        ["Hook", "Problem", "Solution", "Trust", "Proof", "CTA"],
        ["Hook", "Relatable Moment", "Solution", "Trust", "Proof", "CTA"]
    ],

    "text_density": ["short", "medium"]
}

# --- Funnel Bias Rules ---
FUNNEL_BIAS = {
    "cold": {
        "preferred_hooks": ["Problem", "Curiosity", "Relatable"],
        "allowed_text_density": ["short", "medium"],
        "allowed_tone": ["Neutral", "Friendly", "Empathetic"]
    },
    "warm": {
        "preferred_hooks": ["Authority", "Relatable"],
        "allowed_text_density": ["medium"],
        "allowed_tone": ["Neutral", "Friendly"]
    },
    "hot": {
        "preferred_hooks": ["Problem", "Authority"],
        "allowed_text_density": ["short"],
        "allowed_tone": ["Direct"]
    }
}

class PatternSelectionEngine:
    def __init__(self, campaign_psychology):
        self.campaign = campaign_psychology

    def _freq_weighted_choice(self, options, market_weights=None, funnel_preferred=None, founder_preferred=None):
        """Makes a weighted choice combining 3 signal layers:
        
        1. Market weights (from frequency aggregation) - base signal
        2. Funnel bias (preferred hooks/tones for this stage) - strategic layer
        3. Founder preference (brand voice override) - highest priority
        
        Priority: Founder > Funnel > Market > Random
        """
        weights = {}
        for opt in options:
            # Start with market frequency (or equal if no data)
            w = market_weights.get(opt, 0.0) if market_weights else 0.0
            
            # Add funnel bias boost
            if funnel_preferred and opt in funnel_preferred:
                w += 0.3
            
            # Add founder preference boost (highest priority)
            if founder_preferred and opt in founder_preferred:
                w += 0.5
            
            # Ensure minimum weight so nothing is impossible
            weights[opt] = max(w, 0.05)
        
        labels = list(weights.keys())
        w_values = list(weights.values())
        return random.choices(labels, weights=w_values, k=1)[0]

    def select_pattern(self, max_retries=5):
        funnel = self.campaign.get("funnel_stage", "cold")
        market = self.campaign.get("market_context", {})
        
        bias = FUNNEL_BIAS.get(funnel, FUNNEL_BIAS["cold"])
        
        # Extract frequency weights from market context (NEW)
        hook_weights = market.get("hook_type_weights", {})
        tone_weights = market.get("tone_weights", {})
        angle_weights = market.get("angle_weights", {})
        cta_weights = market.get("cta_weights", {})
        density_weights = market.get("text_density_weights", {})

        for _ in range(max_retries):
            pattern = {}

            # 1. Hook type (Market frequency + Funnel bias)
            pattern["hook_type"] = self._freq_weighted_choice(
                PATTERN_SPACE["hook_type"],
                market_weights=hook_weights,
                funnel_preferred=bias["preferred_hooks"]
            )

            # 2. Opening style (Founder emotion-driven)
            if "frustration" in self.campaign.get("emotions", []):
                pattern["opening_style"] = self._freq_weighted_choice(
                    PATTERN_SPACE["opening_style"],
                    founder_preferred=["Story-based", "POV Relatable"]
                )
            else:
                pattern["opening_style"] = random.choice(PATTERN_SPACE["opening_style"])

            # 3. Angle (60/40 Rotation using market weights)
            dominant_angle = market.get("dominant_angle", "Comfort")
            if random.random() < 0.6:
                # Rotate AWAY: use inverse weights
                inverse_weights = {k: (1.0 - v) for k, v in angle_weights.items()} if angle_weights else {}
                other_angles = [a for a in PATTERN_SPACE["angle"] if a != dominant_angle]
                if other_angles:
                    pattern["angle"] = self._freq_weighted_choice(
                        other_angles,
                        market_weights=inverse_weights
                    )
                else:
                    pattern["angle"] = random.choice(PATTERN_SPACE["angle"])
            else:
                # Stay close: use actual market weights
                pattern["angle"] = self._freq_weighted_choice(
                    PATTERN_SPACE["angle"],
                    market_weights=angle_weights
                )

            # 4. Tone (Founder voice > Market signal)
            brand_voice = self.campaign.get("brand_voice", "relatable").capitalize()
            pattern["tone"] = self._freq_weighted_choice(
                bias["allowed_tone"],
                market_weights=tone_weights,
                founder_preferred=[brand_voice]
            )

            # 5. Scene flow (Driven by objections)
            objections = self.campaign.get("objections", [])
            if "quality" in objections or "trust" in objections:
                pattern["scene_flow"] = ["Hook", "Problem", "Solution", "Trust", "CTA"]
            else:
                pattern["scene_flow"] = random.choice(PATTERN_SPACE["scene_flow"])

            # 6. CTA (Founder constraints > Market CTA)
            allowed_cta = self.campaign.get("funnel_constraints", {}).get("allowed_cta", ["Learn More"])
            pattern["cta"] = self._freq_weighted_choice(
                allowed_cta,
                market_weights=cta_weights
            )

            # 7. Text density (Market frequency + Funnel bias)
            pattern["text_density"] = self._freq_weighted_choice(
                PATTERN_SPACE["text_density"],
                market_weights=density_weights,
                funnel_preferred=bias["allowed_text_density"]
            )

            # Check for repetition (Memory Check)
            pattern_hash = json.dumps(pattern, sort_keys=True)
            if pattern_hash not in self._get_recent_patterns():
                self._save_pattern(pattern_hash)
                return pattern
        
        return pattern # Fallback if retries exhausted

    def _get_recent_patterns(self):
        """Loads recently used patterns from a simple hidden file."""
        memory_file = os.path.join("output", ".pattern_memory.json")
        if os.path.exists(memory_file):
            try:
                with open(memory_file, "r") as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else []
            except:
                return []

        return []

    def _save_pattern(self, pattern_hash):
        """Saves current pattern hash to memory, keeping only the last 10."""
        memory_file = os.path.join("output", ".pattern_memory.json")
        memory = self._get_recent_patterns()
        memory.append(pattern_hash)
        # Keep last 10 for rotation
        memory = memory[-10:]
        try:
            with open(memory_file, "w") as f:
                json.dump(memory, f)
        except:
            pass

    def generate_blueprint(self):
        blueprint = self.select_pattern()
        market = self.campaign.get("market_context", {})
        ai_strat = self.campaign.get("ai_strategy", {})
        
        # Synthesize a human readable name
        pattern_name = f"{blueprint['hook_type']} x {blueprint['angle']} Strategy"
        
        # Pull strategic goal from AI psychology brief
        strategic_goal = ai_strat.get("psychological_hook_strategy", "Focus on market transition signals.")
        if not strategic_goal or strategic_goal == "":
             strategic_goal = ai_strat.get("final_brief", "Synthesize founder intent with market norms.")

        return {
            "campaign_id": self.campaign.get("campaign_id", "unknown"),
            "pattern_name": pattern_name,
            "strategic_goal": strategic_goal,
            "pattern_blueprint": blueprint,
            "derived_from": {
                "funnel_stage": self.campaign.get("funnel_stage"),
                "total_ads_analyzed": market.get("total_ads_analyzed", 0),
                "market_weights": {
                    "hook_type": market.get("hook_type_weights", {}),
                    "tone": market.get("tone_weights", {}),
                    "angle": market.get("angle_weights", {}),
                    "cta": market.get("cta_weights", {}),
                    "text_density": market.get("text_density_weights", {})
                },
                "signal_tiers": market.get("signal_tiers", {})
            }
        }

if __name__ == "__main__":
    # Test with local file if exists
    path = os.path.join("output", "campaign_psychology.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
        engine = PatternSelectionEngine(data)
        print(json.dumps(engine.generate_blueprint(), indent=2))
    else:
        print("No campaign_psychology.json found for testing.")
