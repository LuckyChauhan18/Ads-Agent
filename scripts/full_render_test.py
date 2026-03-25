import asyncio
import os
import sys
import json
import time

# Ensure root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.db_mongo_service import connect_to_mongo, close_mongo_connection, mongo
from agents.production.agent import run_production

async def execute_full_test():
    await connect_to_mongo()
    if mongo.db is None: 
        print("❌ MongoDB connection failed")
        return

    campaign_id = "poco__6029"
    print(f"🔍 Fetching render data for: {campaign_id}")
    
    script_doc = await mongo.db.scripts.find_one({"campaign_id": campaign_id})
    if not script_doc:
        print(f"❌ No script found for {campaign_id}")
        await close_mongo_connection()
        return

    # Mock state for ProductionAgent
    state = {
        "creative": {
            "storyboard_output": script_doc.get("storyboard_output"),
            "script_output": script_doc.get("script_output"),
            "audio_planning": script_doc.get("audio_planning"),
            "avatar_config": {
                "selected_avatars": {
                    "gender": "young person",
                    "avatar_preferences": {"gender": "young person"},
                    "voice_preferences": {"language": "Hindi"}
                }
            }
        },
        "campaign_id": campaign_id,
        "user_id": script_doc.get("user_id") or script_doc.get("owner_id"),
        "strategy": {
            "campaign_psychology": {
                "campaign_id": campaign_id,
                "user_id": script_doc.get("user_id") or script_doc.get("owner_id"),
                "audio_planning": script_doc.get("audio_planning")
            }
        }
    }

    print(f"🚀 Render Starting...")
    result = await run_production(state)
    await close_mongo_connection()
    
    render_results = result.get("production", {}).get("render_results", [])
    if render_results:
        print(f"✅ SUCCESS! Ad generated.")
        print(f"📂 Video Path: {render_results[0].get('local_path')}")
    else:
        print("❌ FAILED. Render results empty.")

if __name__ == "__main__":
    asyncio.run(execute_full_test())
