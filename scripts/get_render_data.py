import asyncio
import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.db_mongo_service import connect_to_mongo, close_mongo_connection, mongo

async def get_render_data():
    await connect_to_mongo()
    if mongo.db is None: return

    campaign_id = "poco__6029"
    script_doc = await mongo.db.scripts.find_one({"campaign_id": campaign_id})
    if not script_doc:
        print(f"❌ No script found for {campaign_id}")
        return

    # Extract what the Production Agent needs
    data = {
        "storyboard_output": script_doc.get("storyboard_output"),
        "script_output": script_doc.get("script_output"),
        "audio_planning": script_doc.get("audio_planning"),
        "campaign_id": campaign_id,
        "user_id": script_doc.get("user_id")
    }
    
    with open("scripts/render_payload.json", "w") as f:
        json.dump(data, f, indent=2)
    
    print("✅ Render data saved to scripts/render_payload.json")
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(get_render_data())
