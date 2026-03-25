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
from agents.production.gemini_renderer import get_renderer
from agents.memory.memory_injector import get_production_preferences, build_memory_context_prompt


async def run_production(state: AdGenState) -> dict:
    """
    LangGraph node for the Production Agent.

    Generates variants and renders the final video with overlays.
    """
    print("\n[Production Agent] Starting...")
    errors = list(state.get("errors", []))

    creative_data = state.get("creative", {})
    storyboard_output = creative_data.get("storyboard_output", {})
    script_output = creative_data.get("script_output", {})
    avatar_config = creative_data.get("avatar_config", {})
    audio_planning = creative_data.get("audio_planning", {})

    # ── Memory: Load LTM preferences ──────────────────────────
    # [LTM Disabled for Current Version]
    # memory = state.get("memory", {})
    # production_prefs = get_production_preferences(memory)
    # memory_context = build_memory_context_prompt(production_prefs, "Production")
    # if memory_context:
    #     print(f"   🧠 LTM loaded for production agent")
    
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
    
    # Pass audio plan and full template into context for renderer
    if audio_planning:
        print(f"   🔊 [Production Agent] Injecting audio_planning into context: {audio_planning.get('voice_type')}")
        campaign_psychology["audio_planning"] = audio_planning
    else:
        print("   ⚠️ [Production Agent] audio_planning is EMPTY in state!")
        
    ad_template = strategy_data.get("script_planning", {}).get("template", {})
    if ad_template:
        print(f"   📝 [Production Agent] Injecting full ad_template into context: {ad_template.get('ad_type')}")
        campaign_psychology["ad_template"] = ad_template
        
    print(f"   [Production Agent] Context: campaign={campaign_id}, user={user_id}")
    print(f"   [Production Agent] Creative Keys: {list(creative_data.keys())}")
    if "storyboard_output" in creative_data:
        sb = creative_data["storyboard_output"]
        print(f"   [Production Agent] Storyboard looks like: {type(sb)} (keys: {list(sb.keys()) if isinstance(sb, dict) else 'N/A'})")

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
        # Get ad_type from script_planning instead of audio_planning (where it's missing)
        # Fallback to product_demo if not found
        script_planning = strategy_data.get("script_planning", {})
        ad_type = script_planning.get("ad_type", "product_demo")
        
        print(f"   🎬 Renderer Selection: ad_type={ad_type}")
        engine_render = get_renderer(ad_type, variants_output, avatar_config, campaign_psychology)
        # We need to initialize the renderer (load assets) asynchronously
        await engine_render.initialize()
        
        video_output = await engine_render.generate_output(wait_for_render=True)
        render_results = video_output.get("render_results", [])
        print(f"   [OK] Video rendered: {len(render_results)} variants")
    except Exception as e:
        import traceback
        traceback.print_exc()
        errors.append(f"GeminiRenderer error: {e}")
        video_output = {"render_results": []}
        render_results = []
        print(f"   [WARN] Video rendering failed: {e}")

    print("[Production Agent] Complete.\n")

    return {
        "production": {
            "variants_output": variants_output,
            "render_results": render_results,
        },
        "errors": errors,
    }
