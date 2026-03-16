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
from agents.memory.memory_injector import get_strategy_preferences, build_memory_context_prompt


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

    # ── Memory: Load LTM preferences ──────────────────────────
    memory = state.get("memory", {})
    strategy_prefs = get_strategy_preferences(memory)
    memory_context = build_memory_context_prompt(strategy_prefs, "Strategy")
    if memory_context:
        print(f"   🧠 LTM loaded for strategy agent")
        # Inject preferences into founder_data so engines can use them
        if strategy_prefs.get("preferred_tones"):
            founder_data.setdefault("preferred_tones", strategy_prefs["preferred_tones"])
        if strategy_prefs.get("preferred_hooks"):
            founder_data.setdefault("preferred_hooks", strategy_prefs["preferred_hooks"])
        if strategy_prefs.get("learned_preference"):
            founder_data["memory_note"] = strategy_prefs["learned_preference"]

    # ── Step 1: Campaign Psychology Engine ─────────────────────
    try:
        print(f"   📡 Running Campaign Psychology Engine...")
        engine_1 = CampaignPsychologyEngine(founder_data, competitor_results)
        campaign_psychology = engine_1.generate_campaign_psychology()
        print(f"   ✅ Campaign Psychology Engine completed.")

        # Inject product understanding into psychology context
        if product_understanding:
            campaign_psychology["product_understanding"] = product_understanding

        print(f"   ✅ Campaign psychology generated")
    except Exception as e:
        errors.append(f"CampaignPsychology error: {e}")
        campaign_psychology = {"product_understanding": product_understanding}
        print(f"   ⚠️ Campaign psychology failed: {e}")

    try:
        print(f"   📡 Running Pattern Selection Engine...")
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
