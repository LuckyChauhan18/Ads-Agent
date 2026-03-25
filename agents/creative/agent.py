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
from agents.creative.script_generators import get_script_generator
from agents.creative.storyboard_builders import get_storyboard_builder
from agents.creative.audio_planner import AudioPlannerEngine
from agents.memory.memory_injector import get_creative_preferences, build_memory_context_prompt


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
    avatar_config = creative_data.get("avatar_config") or creative_data.get("avatar_config", {})

    language = state.get("language", "Hindi")
    platform = state.get("platform", "Instagram Reels")
    ad_length = state.get("ad_length", 30)

    # Force ad_length to template duration if available to prevent pacing mismatches
    ad_template = strategy_data.get("script_planning", {}).get("template", {})
    if isinstance(ad_template, dict) and ad_template.get("duration"):
        ad_length = ad_template.get("duration")
        print(f"   ⏱️ Overriding ad_length with template duration: {ad_length}s")

    # ── Memory: Load LTM preferences ──────────────────────────
    # [LTM Disabled for Current Version]
    # memory = state.get("memory", {})
    # creative_prefs = get_creative_preferences(memory)
    # memory_context = build_memory_context_prompt(creative_prefs, "Creative")
    # if memory_context:
    #     print(f"   🧠 LTM loaded for creative agent")
    #     # Apply language preference from memory
    #     if creative_prefs.get("preferred_languages"):
    #         pref_lang = creative_prefs["preferred_languages"][0]
    #         if not state.get("language"):
    #             language = pref_lang
    #     # Inject brand voice notes into psychology context
    #     if creative_prefs.get("brand_voice_notes"):
    #         campaign_psychology["memory_brand_voice"] = creative_prefs["brand_voice_notes"]
    #     if creative_prefs.get("learned_preference"):
    #         campaign_psychology["memory_creative_note"] = creative_prefs["learned_preference"]

    # ── Step 1: Script Generation ─────────────────────────────
    try:
        ad_type = strategy_data.get("script_planning", {}).get("ad_type", "product_demo")
        pattern_data = pattern_blueprint.get("pattern_blueprint", pattern_blueprint)
        campaign_context = {**campaign_psychology, "strategy": strategy_data}
        engine_script = get_script_generator(ad_type, pattern_data, campaign_context)
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
                    script_output["scenes"] = future.result(timeout=120)
                print(f"   ✅ Scenes enhanced")
            except Exception as e:
                print(f"   ⚠️ Scene enhancement error (internal) [{type(e).__name__}]: {e}")
                # Fall back to original scenes if enhancement fails
    except Exception as e:
        errors.append(f"SceneEnhancement error: {e}")
        print(f"   ⚠️ Scene enhancement failed (non-fatal): {e}")

    # ── Step 3: Reflection Loop (Self-Critique) ───────────────
    reflection_results = []
    try:
        from agents.creative.reflection_agent import run_reflection_loop
        script_output, reflection_results = run_reflection_loop(
            script_output, strategy_data, ad_type=ad_type, max_iterations=2
        )
        if reflection_results:
            final_score = reflection_results[-1].get("score", "N/A")
            print(f"   🔍 Reflection complete: final score={final_score}/10")
    except Exception as e:
        errors.append(f"ReflectionLoop error: {e}")
        print(f"   ⚠️ Reflection loop failed (non-fatal): {e}")

    # ── Step 4: Storyboard Building ───────────────────────────
    try:
        engine_sb = get_storyboard_builder(ad_type, script_output, avatar_config, strategy_data)
        storyboard_output = engine_sb.generate_output()
        print(f"   ✅ Storyboard built")
    except Exception as e:
        errors.append(f"StoryboardBuilder error: {e}")
        storyboard_output = script_output  # fallback: use raw script
        print(f"   ⚠️ Storyboard building failed: {e}")

    # ── Step 5: Audio Planning ────────────────────────────────
    try:
        # Get ad_type from strategy state
        script_planning = strategy_data.get("script_planning", {})
        ad_type = script_planning.get("ad_type", "product_demo")
        print(f"   📡 [Creative Agent] Running Audio Planner for: {ad_type}")
        
        audio_planner = AudioPlannerEngine(ad_type)
        audio_planning = audio_planner.plan_audio()
        print(f"   ✅ Audio planned: voice={audio_planning.get('voice_type')}, music={audio_planning.get('music_style')}")
    except Exception as e:
        errors.append(f"AudioPlanner error: {e}")
        audio_planning = {}
        print(f"   ⚠️ Audio planning failed: {e}")

    print("🎨 [Creative Agent] Complete.\n")

    return {
        "creative": {
            "script_output": script_output,
            "avatar_config": avatar_config,
            "storyboard_output": storyboard_output,
            "audio_planning": audio_planning,
        },
        "reflection_results": reflection_results,
        "errors": errors,
    }
