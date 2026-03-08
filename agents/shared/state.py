"""
Global Shared State for the AI Ad Generator Multi-Agent System.

Every agent reads from this state and writes ONLY its own output keys.
This makes it safe to add memory later — each agent's "memory" will be
its own historical outputs.

Future: Add a `memory` key for MemorySaver checkpointing.
"""

from typing import TypedDict, Optional, List, Dict, Any

# ═══════════════════════════════════════════
# MODULAR SUB-STATES
# ═══════════════════════════════════════════

class ResearchState(TypedDict, total=False):
    product_understanding: Dict[str, Any]   # AI-enriched product analysis
    competitor_results: List[Dict[str, Any]]  # Scraped ad DNA

class StrategyState(TypedDict, total=False):
    campaign_psychology: Dict[str, Any]     # Psychology framework
    pattern_blueprint: Dict[str, Any]       # Selected ad pattern

class CreativeState(TypedDict, total=False):
    script_output: Dict[str, Any]           # Scene-by-scene script
    avatar_config: Dict[str, Any]           # Avatar selection
    storyboard_output: Dict[str, Any]       # Shot-by-shot visual storyboard

class ProductionState(TypedDict, total=False):
    variants_output: Dict[str, Any]         # Generated ad variants
    render_results: List[Dict[str, Any]]    # Final video file paths

# ═══════════════════════════════════════════
# MAIN SHARED STATE
# ═══════════════════════════════════════════

class AdGenState(TypedDict, total=False):
    """
    Shared state that flows through all agents via LangGraph.
    Now modularized into agent-specific sub-states.
    """

    # Global Inputs
    product_input: Dict[str, Any]         # Raw user input
    founder_input: Dict[str, Any]         # Strategy form
    curated_brands: List[Dict[str, Any]]  # User-curated competitor brands
    language: str                         # Target language
    platform: str                         # Social media platform (e.g., TikTok, LinkedIn)
    ad_length: int                        # Target duration in seconds (e.g., 15, 30, 45, 60)
    scrape_enabled: bool                  # Scrape control flag

    # Modular Agent States
    research: ResearchState
    strategy: StrategyState
    creative: CreativeState
    production: ProductionState

    # Long-Term Memory (injected at workflow start)
    memory: Dict[str, Any]                # Company-specific learned preferences

    # Reflection Loop Results
    reflection_results: List[Dict[str, Any]]  # Critique scores per iteration

    # Global Metadata
    campaign_id: str                        # MongoDB campaign ID
    user_id: str                            # Authenticated user ID
    company_id: str                         # Company ID for LTM lookup
    errors: List[str]                       # Non-fatal error accumulator

