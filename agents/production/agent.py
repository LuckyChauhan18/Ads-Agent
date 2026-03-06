"""
Production Agent — LangGraph Node

Responsibilities:
  1. Variant Engine (generate ad variants from storyboard)
  2. Gemini Renderer (AI video generation + FFmpeg overlays)
  3. Audio Service (Sarvam TTS voiceover)

Reads from state:  storyboard_output, script_output, avatar_config, campaign_psychology, campaign_id
Writes to state:   variants_output, render_results
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from agents.shared.state import AdGenState
from agents.production.variant_engine import VariantEngine
from agents.production.gemini_renderer import GeminiRenderer


def run_production(state: AdGenState) -> dict:
    """
    LangGraph node for the Production Agent.
    
    Generates variants and renders the final video with overlays.
    """
    print("\n[Production Agent] Starting...")
    errors = list(state.get("errors", []))

    storyboard_output = state.get("storyboard_output", {})
    script_output = state.get("script_output", {})
    avatar_config = state.get("avatar_config", {})
    campaign_psychology = state.get("campaign_psychology", {})

    # Ensure campaign_id is in context for asset loading
    if state.get("campaign_id"):
        campaign_psychology["campaign_id"] = state["campaign_id"]

    # ── Step 1: Variant Generation ────────────────────────────
    try:
        engine_variant = VariantEngine(storyboard_output, script_output, campaign_psychology)
        variants_output = engine_variant.generate_output()
        print(f"   [OK] Variants generated")
    except Exception as e:
        errors.append(f"VariantEngine error: {e}")
        variants_output = storyboard_output  # fallback
        print(f"   [WARN] Variant generation failed: {e}")

    # ── Step 2: Video Rendering ───────────────────────────────
    try:
        engine_render = GeminiRenderer(variants_output, avatar_config, campaign_psychology)
        video_output = engine_render.generate_output(wait_for_render=True)
        render_results = video_output.get("render_results", [])
        print(f"   [OK] Video rendered: {len(render_results)} variants")
    except Exception as e:
        errors.append(f"GeminiRenderer error: {e}")
        video_output = {"render_results": []}
        render_results = []
        print(f"   [WARN] Video rendering failed: {e}")

    print("[Production Agent] Complete.\n")

    return {
        "variants_output": variants_output,
        "render_results": render_results,
        "errors": errors,
    }
