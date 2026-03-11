import asyncio
import os
import sys
from pprint import pprint

# Ensure project root is on path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from agents.shared.state import AdGenState
from agents.strategy.agent import run_strategy
from agents.creative.agent import run_creative
from agents.production.agent import run_production

async def main():
    print("🚀 Starting Video Improvement Test Pipeline...")

    # Mock State for a Skincare Product
    state: AdGenState = {
        "product_input": {
            "product_name": "Lumina Vitamin C Serum",
            "description": "A brightening serum that fades dark spots and evens skin tone in 14 days.",
            "brand_name": "Lumina Beauty"
        },
        "founder_input": {
            "user_problem": "Dull skin, dark spots, and uneven tone making you look tired.",
            "offer_details": "20% off + free shipping on first order"
        },
        "research": {
            "product_understanding": {
                "product_name": "Lumina Vitamin C Serum",
                "brand_name": "Lumina Beauty",
                "category": "Skincare",
                "features": ["Brightens skin", "Fades dark spots", "Evens skin tone", "Visible results in 14 days"]
            },
            "competitor_results": []
        },
        "language": "English",
        "ad_length": 30, # 4-5 scenes
        "platform": "Instagram Reels",
        "creative": {
            "avatar_config": {
                "avatar_profile": {
                    "gender": "female",
                    "avatar_type": "presenter",
                    "camera_style": "studio",
                    "facial_expression": "friendly"
                }
            }
        },
        "errors": []
    }

    # 1. Run Strategy
    print("\n--- Running Strategy ---")
    strategy_output = run_strategy(state)
    state.update(strategy_output)
    print("✓ Strategy Complete")

    # 2. Run Creative
    print("\n--- Running Creative ---")
    creative_output = run_creative(state)
    state.update(creative_output)
    
    print("\n📝 Generated Storyboard Scenes:")
    scenes = state["creative"]["storyboard_output"]["storyboard"]
    for i, s in enumerate(scenes):
        print(f"  Scene {i+1} ({s['scene']}): {s['shot_type']} -> {s['realistic_directives']}")

    # 3. Run Production
    print("\n--- Running Production (Veo 3.1 generation) ---")
    # run_production is async
    production_output = await run_production(state)
    state.update(production_output)

    print("\n🎬 Production Complete!")
    
    if state["production"]["render_results"]:
        for res in state["production"]["render_results"]:
            print(f"✅ Video ready: {res.get('final_video_url', res.get('final_video'))}")
    else:
        print("❌ No video rendered. Check errors:")
        pprint(state["errors"])

if __name__ == "__main__":
    asyncio.run(main())
