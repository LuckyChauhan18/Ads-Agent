"""
Global Shared State for the AI Ad Generator Multi-Agent System.

Every agent reads from this state and writes ONLY its own output keys.
This makes it safe to add memory later — each agent's "memory" will be
its own historical outputs.

Future: Add a `memory` key for MemorySaver checkpointing.
"""

from typing import TypedDict, Optional, List, Dict, Any


class AdGenState(TypedDict, total=False):
    """
    Shared state that flows through all agents via LangGraph.
    
    Convention:
      - INPUTS are set by the API layer before invoking the graph.
      - Each agent writes ONLY its designated output keys.
      - `errors` is an append-only list for non-fatal issues.
    """

    # ═══════════════════════════════════════════
    # INPUTS (set by API before graph invocation)
    # ═══════════════════════════════════════════
    product_input: Dict[str, Any]         # Raw user input from Step 1 (name, brand, URL, features)
    founder_input: Dict[str, Any]         # Strategy form from Step 4 (emotions, funnel, voice, platform)
    curated_brands: List[Dict[str, Any]]  # User-curated competitor brands from Step 2
    language: str                         # Target language (Hindi, English, etc.)
    scrape_enabled: bool                  # If False, Research Agent stops after discovery

    # ═══════════════════════════════════════════
    # RESEARCH AGENT OUTPUTS
    # ═══════════════════════════════════════════
    product_understanding: Dict[str, Any]   # AI-enriched product analysis (name, brand, category, features)
    competitor_results: List[Dict[str, Any]]  # Scraped ad DNA from Meta

    # ═══════════════════════════════════════════
    # STRATEGY AGENT OUTPUTS
    # ═══════════════════════════════════════════
    campaign_psychology: Dict[str, Any]     # Psychology framework + market context
    pattern_blueprint: Dict[str, Any]       # Selected ad pattern (structure, tone, angle)

    # ═══════════════════════════════════════════
    # CREATIVE AGENT OUTPUTS
    # ═══════════════════════════════════════════
    script_output: Dict[str, Any]           # Scene-by-scene script with voiceovers
    avatar_config: Dict[str, Any]           # Avatar selection + voice preferences
    storyboard_output: Dict[str, Any]       # Shot-by-shot visual storyboard

    # ═══════════════════════════════════════════
    # PRODUCTION AGENT OUTPUTS
    # ═══════════════════════════════════════════
    variants_output: Dict[str, Any]         # Generated ad variants
    render_results: List[Dict[str, Any]]    # Final video file paths + metadata

    # ═══════════════════════════════════════════
    # METADATA
    # ═══════════════════════════════════════════
    campaign_id: str                        # MongoDB campaign ID
    user_id: str                            # Authenticated user ID
    errors: List[str]                       # Non-fatal error accumulator
