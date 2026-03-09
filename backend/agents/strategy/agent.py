"""
Strategy Agent — LangGraph Node

Responsibilities:
  1. Campaign Psychology Engine (emotional angles, objections, trust)
  2. Pattern Selection Engine (ad structure, tone, angle)

Reads from state:  founder_input, competitor_results, product_understanding
Writes to state:   campaign_psychology, pattern_blueprint
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from agents.shared.state import AdGenState
from agents.strategy.campaign_psychology import CampaignPsychologyEngine
from agents.strategy.pattern_selection import PatternSelectionEngine


def run_strategy(state: AdGenState) -> dict:
    """
    LangGraph node for the Strategy Agent.
    
    Generates campaign psychology and selects the optimal ad pattern.
    """
    print("\n🧠 [Strategy Agent] Starting...")
    errors = list(state.get("errors", []))

    strategy_data = state.get("strategy", {})
    founder_data = state.get("founder_input", {})
    research_data = state.get("research", {})
    competitor_results = research_data.get("competitor_results", [])
    product_understanding = research_data.get("product_understanding", {})

    # ── Step 1: Campaign Psychology Engine ─────────────────────
    try:
        engine_1 = CampaignPsychologyEngine(founder_data, competitor_results)
        campaign_psychology = engine_1.generate_campaign_psychology()

        # Inject product understanding into psychology context
        if product_understanding:
            campaign_psychology["product_understanding"] = product_understanding

        print(f"   ✅ Campaign psychology generated")
    except Exception as e:
        errors.append(f"CampaignPsychology error: {e}")
        campaign_psychology = {"product_understanding": product_understanding}
        print(f"   ⚠️ Campaign psychology failed: {e}")

    # ── Step 2: Pattern Selection Engine ───────────────────────
    try:
        engine_2 = PatternSelectionEngine(campaign_psychology)
        pattern_blueprint = engine_2.generate_blueprint()
        print(f"   ✅ Ad pattern selected: {pattern_blueprint.get('pattern_name', 'Unknown')}")
    except Exception as e:
        errors.append(f"PatternSelection error: {e}")
        pattern_blueprint = {}
        print(f"   ⚠️ Pattern selection failed: {e}")

    print("🧠 [Strategy Agent] Complete.\n")

    return {
        "strategy": {
            "campaign_psychology": campaign_psychology,
            "pattern_blueprint": pattern_blueprint,
        },
        "errors": errors,
    }
