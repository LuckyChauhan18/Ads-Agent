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

from utils.logger import logger
from agents.shared.state import AdGenState
from agents.creative.script_generator import ScriptGenerator
from agents.creative.storyboard_builder import StoryboardBuilder
from agents.creative.scene_planner import ScenePlanner


def run_creative(state: AdGenState) -> dict:
    """
    LangGraph node for the Creative Agent.
    
    Generates the ad script, selects avatars, and builds the storyboard.
    """
    logger.info("🎨 [Creative Agent] Starting...")
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

    # ── Step 0: Scene Planning (NEW) ─────────────────────────
    scene_plan = None
    try:
        # Build avatar list from avatar_config
        avatar_list = []
        if isinstance(avatar_config, list):
            avatar_list = avatar_config
        elif isinstance(avatar_config, dict):
            selected = avatar_config.get("selected_avatars", avatar_config.get("results", []))
            if isinstance(selected, list):
                avatar_list = selected
            elif selected:
                avatar_list = [selected]
        
        logger.info(f"   🧠 Running Scene Planner for {ad_length}s ad with {len(avatar_list)} avatar(s)...")
        planner = ScenePlanner(campaign_psychology, avatar_list=avatar_list)
        scene_plan = planner.plan_scenes_llm(ad_length, platform)
        logger.info(f"   ✅ Scene plan ready: {len(scene_plan)} scenes")
    except Exception as e:
        errors.append(f"ScenePlanner error: {e}")
        logger.warning(f"   ⚠️ Scene planning failed (non-fatal): {e}. Script will use defaults.")

    # ── Step 1: Script Generation ─────────────────────────────
    try:
        logger.info(f"   🔄 Generating script ({ad_length}s, {language}, {platform})...")
        pattern_data = pattern_blueprint.get("pattern_blueprint", pattern_blueprint)
        memory = strategy_data.get("memory", {})
        engine_script = ScriptGenerator(pattern_data, campaign_psychology, memory=memory)
        script_output = engine_script.generate_output(language=language, platform=platform, ad_length=ad_length, scene_plan=scene_plan)
        scene_count = len(script_output.get("scenes", []))
        logger.info(f"   ✅ Script generated: {scene_count} scenes in {language}")
    except Exception as e:
        errors.append(f"ScriptGeneration error: {e}")
        script_output = {"scenes": []}
        logger.error(f"   ⚠️ Script generation failed: {e}")


    # ── Step 2: LLM Scene Enhancement ────────────────────────
    try:
        from api.services.ai_assist_service import ai_assist_service
        import asyncio

        if "scenes" in script_output and script_output["scenes"]:
            logger.info(f"   🔄 Enhancing {len(script_output['scenes'])} scenes via LLM filter...")
            
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
                logger.info(f"   ✅ Scenes enhanced")
            except Exception as e:
                logger.warning(f"   ⚠️ Scene enhancement error (internal): {e}")
                # Fall back to original scenes if enhancement fails
    except Exception as e:
        errors.append(f"SceneEnhancement error: {e}")
        logger.warning(f"   ⚠️ Scene enhancement failed (non-fatal): {e}")

    # ── Step 3: Storyboard Building ───────────────────────────
    try:
        logger.info("   🔄 Building storyboard...")
        engine_sb = StoryboardBuilder(script_output, avatar_config, campaign_psychology)
        storyboard_output = engine_sb.generate_output()
        logger.info(f"   ✅ Storyboard built")
    except Exception as e:
        errors.append(f"StoryboardBuilder error: {e}")
        storyboard_output = script_output  # fallback: use raw script
        logger.error(f"   ⚠️ Storyboard building failed: {e}")

    # ── Step 4: Reflection Loop (Self-Critique) ───────────────
    reflection_results = []
    try:
        logger.info("   🔄 Running reflection loop...")
        from agents.creative.reflection_agent import run_reflection_loop
        script_output, reflection_results = run_reflection_loop(
            script_output, campaign_psychology, max_iterations=2
        )
        if reflection_results:
            final_score = reflection_results[-1].get("score", "N/A")
            logger.info(f"   🔍 Reflection complete: final score={final_score}/10")
    except Exception as e:
        errors.append(f"ReflectionLoop error: {e}")
        logger.warning(f"   ⚠️ Reflection loop failed (non-fatal): {e}")

    logger.info("🎨 [Creative Agent] Complete.")

    return {
        "creative": {
            "script_output": script_output,
            "avatar_config": avatar_config,
            "storyboard_output": storyboard_output,
        },
        "reflection_results": reflection_results,
        "errors": errors,
    }
