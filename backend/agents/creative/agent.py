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

    strategy_data = state.get("strategy", {})
    campaign_psychology = strategy_data.get("campaign_psychology", {})
    pattern_blueprint = strategy_data.get("pattern_blueprint", {})
    
    creative_data = state.get("creative", {})
    # Prioritize avatar_config passed directly in state.creative
    avatar_config = creative_data.get("avatar_config") or creative_data.get("avatar_config", {})
    
    language = state.get("language", "Hindi")
    platform = state.get("platform", "Instagram Reels")
    ad_length = state.get("ad_length", 30)

    # ── Step 1: Script Generation ─────────────────────────────
    try:
        pattern_data = pattern_blueprint.get("pattern_blueprint", pattern_blueprint)
        engine_script = ScriptGenerator(pattern_data, campaign_psychology)
        script_output = engine_script.generate_output(language=language, platform=platform, ad_length=ad_length)
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
            
            # Use a fresh event loop in a separate thread to avoid "loop already running" or "no loop" issues
            import concurrent.futures
            
            def safe_async_run(coro_func, *args, **kwargs):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(coro_func(*args, **kwargs))
                finally:
                    loop.close()

            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(
                        safe_async_run, 
                        ai_assist_service.filter_storyboard_scenes_parallel, 
                        script_output["scenes"], 
                        language=language
                    )
                    script_output["scenes"] = future.result(timeout=60)
                print(f"   ✅ Scenes enhanced")
            except Exception as e:
                print(f"   ⚠️ Scene enhancement error (internal): {e}")
                # Fall back to original scenes if enhancement fails
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

    # ── Step 4: Reflection Loop (Self-Critique) ───────────────
    reflection_results = []
    try:
        from agents.creative.reflection_agent import run_reflection_loop
        script_output, reflection_results = run_reflection_loop(
            script_output, campaign_psychology, max_iterations=2
        )
        if reflection_results:
            final_score = reflection_results[-1].get("score", "N/A")
            print(f"   🔍 Reflection complete: final score={final_score}/10")
    except Exception as e:
        errors.append(f"ReflectionLoop error: {e}")
        print(f"   ⚠️ Reflection loop failed (non-fatal): {e}")

    print("🎨 [Creative Agent] Complete.\n")

    return {
        "creative": {
            "script_output": script_output,
            "avatar_config": avatar_config,
            "storyboard_output": storyboard_output,
        },
        "reflection_results": reflection_results,
        "errors": errors,
    }
