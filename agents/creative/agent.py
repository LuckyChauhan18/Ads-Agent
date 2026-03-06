"""
Creative Agent — LangGraph Node

Responsibilities:
  1. Script Generation (scene-by-scene voiceover in target language)
  2. Avatar Discovery & Selection
  3. Storyboard Building (binding assets to scenes)

Reads from state:  campaign_psychology, pattern_blueprint, avatar_config, language
Writes to state:   script_output, storyboard_output
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from agents.shared.state import AdGenState
from agents.creative.script_generator import ScriptGenerator
from agents.creative.storyboard_builder import StoryboardBuilder


def run_creative(state: AdGenState) -> dict:
    """
    LangGraph node for the Creative Agent.
    
    Generates the ad script, selects avatars, and builds the storyboard.
    """
    print("\n🎨 [Creative Agent] Starting...")
    errors = list(state.get("errors", []))

    campaign_psychology = state.get("campaign_psychology", {})
    pattern_blueprint = state.get("pattern_blueprint", {})
    avatar_config = state.get("avatar_config", {})
    language = state.get("language", "Hindi")

    # ── Step 1: Script Generation ─────────────────────────────
    try:
        pattern_data = pattern_blueprint.get("pattern_blueprint", pattern_blueprint)
        engine_script = ScriptGenerator(pattern_data, campaign_psychology)
        script_output = engine_script.generate_output(language=language)
        scene_count = len(script_output.get("scenes", []))
        print(f"   ✅ Script generated: {scene_count} scenes in {language}")
    except Exception as e:
        errors.append(f"ScriptGeneration error: {e}")
        script_output = {"scenes": []}
        print(f"   ⚠️ Script generation failed: {e}")

    # ── Step 2: LLM Scene Enhancement ────────────────────────
    try:
        from api.services.ai_assist_service import ai_assist_service
        import asyncio

        if "scenes" in script_output and script_output["scenes"]:
            print(f"   🔄 Enhancing {len(script_output['scenes'])} scenes via LLM filter...")
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    script_output["scenes"] = pool.submit(
                        asyncio.run,
                        ai_assist_service.filter_storyboard_scenes_parallel(
                            script_output["scenes"], language=language
                        )
                    ).result()
            else:
                script_output["scenes"] = asyncio.run(
                    ai_assist_service.filter_storyboard_scenes_parallel(
                        script_output["scenes"], language=language
                    )
                )
            print(f"   ✅ Scenes enhanced")
    except Exception as e:
        errors.append(f"SceneEnhancement error: {e}")
        print(f"   ⚠️ Scene enhancement failed (non-fatal): {e}")

    # ── Step 3: Storyboard Building ───────────────────────────
    try:
        engine_sb = StoryboardBuilder(script_output, avatar_config, campaign_psychology)
        storyboard_output = engine_sb.generate_output()
        print(f"   ✅ Storyboard built")
    except Exception as e:
        errors.append(f"StoryboardBuilder error: {e}")
        storyboard_output = script_output  # fallback: use raw script
        print(f"   ⚠️ Storyboard building failed: {e}")

    print("🎨 [Creative Agent] Complete.\n")

    return {
        "script_output": script_output,
        "storyboard_output": storyboard_output,
        "errors": errors,
    }
