import asyncio
import os
import sys
import json
import time
import traceback

# Ensure root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.db_mongo_service import connect_to_mongo, close_mongo_connection, mongo
from agents.creative.agent import run_creative
from agents.production.agent import run_production

async def master_execute():
    try:
        await connect_to_mongo()
        if mongo.db is None: 
            print("❌ MongoDB connection failed")
            return

        print(f"🎬 [Master] Searching for campaigns...")
        
        # List all campaigns
        all_c = []
        async for c in mongo.db.campaigns.find({}):
            cid = c.get("campaign_id", str(c.get("_id", "")))
            all_c.append((cid, c))
        print(f"📋 Found {len(all_c)} campaigns in DB: {[x[0] for x in all_c]}")

        if not all_c:
            print("❌ No campaigns found in DB. Please create one via the frontend first.")
            return
        
        # Use the first (most recent) campaign
        campaign_id, campaign_doc = all_c[0]
        print(f"✅ Using campaign: {campaign_id}")
        print(f"   Keys: {list(campaign_doc.keys())}")

        # Prepare initial state
        state = {
            "campaign_id": campaign_id,
            "user_id": str(campaign_doc.get("user_id")),
            "strategy": campaign_doc.get("strategy", {}),
            "creative": campaign_doc.get("creative", {}),
            "language": "Hindi",
            "platform": "Instagram Reels",
            "ad_length": 30,
            "errors": []
        }

        # ── Phase 1: Creative Agent ──
        print("\n🚀 [Phase 1] Running Creative Agent (Script + Storyboard)...")
        creative_result = run_creative(state)
        
        # Sync state with creative results
        res = creative_result.get("creative", {})
        state["creative"].update(res)
        
        # ── PERSIST TO DB ──
        print(f"   💾 Persisting script/storyboard to DB for {campaign_id}...")
        from api.services.db_mongo_service import save_document
        script_data = {
            "campaign_id": campaign_id,
            "user_id": state["user_id"],
            "script_output": res.get("script_output"),
            "storyboard_output": res.get("storyboard_output"),
            "audio_planning": res.get("audio_planning"),
            "status": "completed",
            "updated_at": str(time.time())
        }
        await save_document("scripts", script_data)
        print("   ✅ Persisted.")
        
        if state["errors"]:
            print(f"⚠️ Creative Agent reported errors: {state['errors']}")

        # ── Phase 2: Production Agent ──
        print("\n🚀 [Phase 2] Running Production Agent (Video Rendering)...")
        # Integration: Ensure audio_planning is passed to production
        production_result = await run_production(state)
        
        render_results = production_result.get("production", {}).get("render_results", [])
        
        if render_results:
            print("\n" + "="*50)
            print(f"✨ SUCCESS! Ad generated for {campaign_id}")
            print(f"📁 Final Video: {render_results[0].get('local_path')}")
            print(f"🆔 Video ID: {render_results[0].get('video_id')}")
            print("="*50)
            
            # Save to JSON for verification
            with open("scripts/master_execution_result.json", "w") as f:
                json.dump(render_results, f, indent=2)
        else:
            print("\n❌ FAILED. No render results produced.")
            if production_result.get("errors"):
                print(f"   Errors: {production_result['errors']}")

    except Exception as e:
        print(f"❌ Master Execution Exception: {e}")
        traceback.print_exc()
    finally:
        await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(master_execute())
