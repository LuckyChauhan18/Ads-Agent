"""
Research Agent — LangGraph Node

Responsibilities:
  1. Product Understanding (AI analysis of user's product input)
  2. Competitor Discovery (LLM-based brand finding)
  3. Meta Ads Scraping & DNA Extraction
  4. Ad Verification & Refinement

Reads from state:  product_input, curated_brands
Writes to state:   product_understanding, competitor_results
"""

import os
import sys

# Ensure project root is on path for helper imports
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from agents.shared.state import AdGenState
from agents.research.product_understanding import ProductUnderstandingEngine
from agents.research.ai_competitor_finder import AICompetitorFinder
from agents.research.multi_ad_extractor import run_extraction
from agents.research.filter import DNAFilter
from agents.memory.memory_injector import get_research_preferences, build_memory_context_prompt

OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def run_research(state: AdGenState) -> dict:
    """
    LangGraph node for the Research Agent.

    Phase 1: Discovery — Analyze product, find competitors.
    Phase 2: Research  — Scrape Meta ads, extract DNA.
    """
    print("\n🔍 [Research Agent] Starting...")
    errors = list(state.get("errors", []))

    product_data = state.get("product_input", {})
    curated_brands = state.get("curated_brands", [])

    # ── Memory: Load LTM preferences ──────────────────────────
    memory = state.get("memory", {})
    research_prefs = get_research_preferences(memory)
    memory_context = build_memory_context_prompt(research_prefs, "Research")
    if memory_context:
        print(f"   🧠 LTM loaded for research agent")
        # Add preferred/avoided competitors from memory
        if research_prefs.get("preferred_competitors"):
            for comp in research_prefs["preferred_competitors"]:
                if not any(b["name"] == comp for b in curated_brands):
                    curated_brands.append({"name": comp, "target_count": 3, "source": "memory"})
        if research_prefs.get("avoided_competitors"):
            avoided = set(research_prefs["avoided_competitors"])
            curated_brands = [b for b in curated_brands if b["name"] not in avoided]

    # ── Step 1: Product Understanding ─────────────────────────
    try:
        engine = ProductUnderstandingEngine(product_data)
        understanding = engine.get_understanding()
        if product_data.get("root_product"):
            understanding["root_product"] = product_data["root_product"]
        print(f"   ✅ Product understood: {understanding.get('product_name', 'Unknown')}")
    except Exception as e:
        errors.append(f"ProductUnderstanding error: {e}")
        understanding = {"product_name": product_data.get("product_name", "Unknown")}
        print(f"   ⚠️ Product understanding failed: {e}")

    # ── Step 2: Competitor Discovery (if no curated brands) ───
    if not curated_brands:
        try:
            ai_finder = AICompetitorFinder()
            brand_queue = ai_finder.find_competitors(understanding)
            brands = list(dict.fromkeys(
                [b for b in brand_queue if " ads" not in b.lower() and len(b) > 2]
            ))[:5]
            curated_brands = [{"name": b, "target_count": 3} for b in brands]
            print(f"   ✅ Discovered {len(curated_brands)} competitor brands")
        except Exception as e:
            errors.append(f"CompetitorDiscovery error: {e}")
            curated_brands = []
            print(f"   ⚠️ Competitor discovery failed: {e}")

    # ── Step 3: Meta Ads Scraping & DNA Extraction ────────────
    competitor_results = []
    
    if state.get("scrape_enabled", True):
        ai_finder = AICompetitorFinder()
        for brand_info in curated_brands:
            brand_name = brand_info["name"]
            target_count = brand_info.get("target_count", 3)
            product_context = understanding.get("root_product") or understanding.get("category", "")

            print(f"   📡 Scraping {brand_name} (target: {target_count})...")

            try:
                competitor_output_path = os.path.join(OUTPUT_DIR, f"ads_dna_{brand_name.lower()}.json")
                raw_results = run_extraction(
                    brand_queue=[brand_name],
                    max_unique_brands=1,
                    ads_per_brand=target_count,
                    output_file=competitor_output_path,
                    product_context=product_context
                )

                brand_verified = []
                for ad in raw_results:
                    if ai_finder.verify_ad_match(ad, understanding):
                        refined_ad = ai_finder.refine_ad_dna(ad)
                        brand_verified.append(refined_ad)

                competitor_results.append({
                    "company": brand_name,
                    "target_count": target_count,
                    "actual_count": len(brand_verified),
                    "punch_lines": [ad["dna"]["punch_line"] for ad in brand_verified],
                    "top_punchline": brand_verified[0]["dna"]["punch_line"] if brand_verified else "No ads found",
                    "ads": brand_verified
                })
                print(f"   ✅ {brand_name}: {len(brand_verified)} verified ads")
            except Exception as e:
                errors.append(f"Scraping {brand_name} error: {e}")
                competitor_results.append({
                    "company": brand_name,
                    "target_count": target_count,
                    "actual_count": 0,
                    "punch_lines": [],
                    "top_punchline": "Scraping failed",
                    "ads": []
                })
                print(f"   ⚠️ Scraping {brand_name} failed: {e}")

        print(f"🔍 [Research Agent] Scraping Complete. {len(competitor_results)} brands processed.\n")
    else:
        print(f"🔍 [Research Agent] Discovery Complete. Scraping paused.\n")

    return {
        "research": {
            "product_understanding": understanding,
            "competitor_results": competitor_results,
        },
        "curated_brands": curated_brands,
        "errors": errors,
    }
