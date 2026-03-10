"""
Memory Injector — Bridges LTM/STM into agent decision-making.

Short-Term Memory (STM): Current session state stored in LangGraph checkpoints.
Long-Term Memory (LTM): Persistent per-company preferences in MongoDB.

This module provides helpers that agents call to:
1. Read learned preferences from LTM
2. Apply preferences as context/constraints
3. Record observations to STM for the current session
"""


def get_research_preferences(memory: dict) -> dict:
    """Extract research-specific preferences from LTM."""
    research_mem = memory.get("research_memory", {})
    return {
        "preferred_competitors": research_mem.get("preferred_competitors", []),
        "avoided_competitors": research_mem.get("avoided_competitors", []),
        "preferred_ad_sources": research_mem.get("preferred_ad_sources", []),
        "learned_preference": research_mem.get("learned_preference", ""),
    }


def get_strategy_preferences(memory: dict) -> dict:
    """Extract strategy-specific preferences from LTM."""
    strategy_mem = memory.get("strategy_memory", {})
    return {
        "preferred_tones": strategy_mem.get("preferred_tones", []),
        "preferred_hooks": strategy_mem.get("preferred_hooks", []),
        "avoided_angles": strategy_mem.get("avoided_angles", []),
        "preferred_funnel_stage": strategy_mem.get("preferred_funnel_stage", ""),
        "learned_preference": strategy_mem.get("learned_preference", ""),
    }


def get_creative_preferences(memory: dict) -> dict:
    """Extract creative-specific preferences from LTM."""
    creative_mem = memory.get("creative_memory", {})
    return {
        "preferred_languages": creative_mem.get("preferred_languages", []),
        "preferred_scene_count": creative_mem.get("preferred_scene_count", None),
        "preferred_avatar_style": creative_mem.get("preferred_avatar_style", ""),
        "brand_voice_notes": creative_mem.get("brand_voice_notes", ""),
        "learned_preference": creative_mem.get("learned_preference", ""),
    }


def get_production_preferences(memory: dict) -> dict:
    """Extract production-specific preferences from LTM."""
    production_mem = memory.get("production_memory", {})
    return {
        "preferred_render_style": production_mem.get("preferred_render_style", ""),
        "preferred_aspect_ratio": production_mem.get("preferred_aspect_ratio", "9:16"),
        "preferred_music_style": production_mem.get("preferred_music_style", ""),
        "learned_preference": production_mem.get("learned_preference", ""),
    }


def build_memory_context_prompt(preferences: dict, agent_name: str) -> str:
    """
    Build a context string from LTM preferences that can be injected
    into LLM prompts to guide agent behavior.
    """
    lines = []
    learned = preferences.get("learned_preference", "")
    if learned:
        lines.append(f"[LEARNED] The brand has previously expressed: {learned}")

    for key, val in preferences.items():
        if key == "learned_preference" or not val:
            continue
        if isinstance(val, list) and val:
            lines.append(f"- {key.replace('_', ' ').title()}: {', '.join(str(v) for v in val)}")
        elif isinstance(val, str) and val:
            lines.append(f"- {key.replace('_', ' ').title()}: {val}")

    if not lines:
        return ""

    header = f"\n--- Brand Memory ({agent_name}) ---\n"
    return header + "\n".join(lines) + "\n--- End Memory ---\n"


def merge_stm_observations(current_stm: dict, new_observations: dict) -> dict:
    """
    Merge new short-term observations into the current session's STM.
    STM is stored in the LangGraph state and persists via checkpointer.
    """
    merged = dict(current_stm)
    for key, value in new_observations.items():
        if key in merged and isinstance(merged[key], list) and isinstance(value, list):
            merged[key] = merged[key] + value
        elif key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key].update(value)
        else:
            merged[key] = value
    return merged
