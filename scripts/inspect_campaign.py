import asyncio
import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.db_mongo_service import connect_to_mongo, close_mongo_connection, mongo

async def inspect_campaign():
    await connect_to_mongo()
    if mongo.db is None: return

    campaign_id = "poco__6029"
    doc = await mongo.db.campaigns.find_one({"campaign_id": campaign_id})
    if doc:
        # Print keys and some content
        print(f"📋 Campaign Keys: {list(doc.keys())}")
        if "strategy" in doc: print("   ✅ Strategy data found")
        if "creative" in doc: print("   ✅ Creative data found")
        
        # Save a sample to check structure
        with open("scripts/campaign_sample.json", "w") as f:
            json.dump(doc, f, indent=2, default=str)
        print("✅ Sample saved to scripts/campaign_sample.json")
    else:
        print(f"❌ Campaign {campaign_id} not found")

    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(inspect_campaign())
