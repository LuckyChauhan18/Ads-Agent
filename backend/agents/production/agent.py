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

from utils.logger import logger
from agents.shared.state import AdGenState
from agents.production.variant_engine import VariantEngine
from agents.production.gemini_renderer import GeminiRenderer


async def run_production(state: AdGenState) -> dict:
    """
    LangGraph node for the Production Agent.
    
    Generates variants and renders the final video with overlays.
    """
    logger.info("🎬 [Production Agent] Starting...")
    errors = list(state.get("errors", []))

    creative_data = state.get("creative", {})
    storyboard_output = creative_data.get("storyboard_output", {})
    script_output = creative_data.get("script_output", {})
    avatar_config = creative_data.get("avatar_config", {})
    
    strategy_data = state.get("strategy", {})
    campaign_psychology = strategy_data.get("campaign_psychology", {})
    production_data = state.get("production", {})

    # Ensure campaign_id and user_id are in context for asset loading
    user_id = state.get("user_id") or strategy_data.get("user_id") or campaign_psychology.get("user_id")
    campaign_id = state.get("campaign_id") or campaign_psychology.get("campaign_id")
    
    if campaign_id:
        campaign_psychology["campaign_id"] = campaign_id
    if user_id:
        campaign_psychology["user_id"] = user_id
        
    logger.info(f"   📋 Context: campaign={campaign_id}, user={user_id}")
    logger.debug(f"   Creative Keys: {list(creative_data.keys())}")
    if "storyboard_output" in creative_data:
        sb = creative_data["storyboard_output"]
        logger.debug(f"   Storyboard type: {type(sb)} (keys: {list(sb.keys()) if isinstance(sb, dict) else 'N/A'})")

    # ── Step 1: Variant Generation ────────────────────────────
    try:
        logger.info("   🔄 Generating variants...")
        engine_variant = VariantEngine(storyboard_output, script_output, campaign_psychology)
        variants_output = engine_variant.generate_output()
        logger.info(f"   ✅ Variants generated")
    except Exception as e:
        errors.append(f"VariantEngine error: {e}")
        variants_output = storyboard_output  # fallback
        logger.error(f"   ⚠️ Variant generation failed: {e}")

    # ── Step 2: Video Rendering ───────────────────────────────
    try:
        logger.info("   🔄 Initializing Gemini Renderer...")
        engine_render = GeminiRenderer(variants_output, avatar_config, campaign_psychology)
        # We need to initialize the renderer (load assets) asynchronously
        await engine_render.initialize()
        
        logger.info("   🎬 Rendering video...")
        video_output = await engine_render.generate_output(wait_for_render=True)
        render_results = video_output.get("render_results", [])
        logger.info(f"   ✅ Video rendered: {len(render_results)} variants")
    except Exception as e:
        import traceback
        traceback.print_exc()
        errors.append(f"GeminiRenderer error: {e}")
        video_output = {"render_results": []}
        render_results = []
        logger.error(f"   ⚠️ Video rendering failed: {e}")

    logger.info("🎬 [Production Agent] Complete.")

    return {
        "production": {
            "variants_output": variants_output,
            "render_results": render_results,
        },
        "errors": errors,
    }
