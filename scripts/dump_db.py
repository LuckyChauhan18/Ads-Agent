import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.db_mongo_service import connect_to_mongo, close_mongo_connection, mongo

async def dump_db():
    await connect_to_mongo()
    if mongo.db is None:
        print("❌ MongoDB connection failed")
        return

    # List all collections
    collections = await mongo.db.list_collection_names()
    print(f"📋 Collections: {collections}")

    for coll_name in collections:
        count = await mongo.db[coll_name].count_documents({})
        print(f"   {coll_name}: {count} documents")
        if count > 0 and count < 10:
            async for doc in mongo.db[coll_name].find({}).limit(3):
                keys = list(doc.keys())
                cid = doc.get("campaign_id", doc.get("_id", ""))
                print(f"      -> keys={keys}, campaign_id={cid}")

    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(dump_db())
