import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.db_mongo_service import connect_to_mongo, close_mongo_connection, mongo

async def get_context():
    await connect_to_mongo()
    if mongo.db is None: return

    print("📋 Campaigns:")
    cursor = mongo.db.campaigns.find({})
    async for doc in cursor:
        print(f"   - ID: {doc.get('campaign_id')} | Product: {doc.get('product_name')}")

    print("\n📋 Scripts:")
    cursor = mongo.db.scripts.find({})
    async for doc in cursor:
        print(f"   - Campaign: {doc.get('campaign_id')} | Status: {doc.get('status')}")

    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(get_context())
