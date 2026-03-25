import asyncio
import os
import sys

# Ensure root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.db_mongo_service import connect_to_mongo, close_mongo_connection, mongo, DB_NAME

async def cleanup_mongo():
    print("🧹 Starting MongoDB-only cleanup...")
    
    # Connect to Mongo
    await connect_to_mongo()
    if mongo.db is None:
        print("❌ Could not connect to MongoDB for cleanup.")
        return

    # Drop collections
    collections = [
        "campaign_history",
        "campaigns",
        "scripts",
        "assets",
        "products",
        "research",
        "feedback",
        "user_assets",
        "fs.files",
        "fs.chunks",
        "storyboards"
    ]
    
    for coll in collections:
        try:
            await mongo.db[coll].drop()
            print(f"   Dropped collection: {coll}")
        except Exception as e:
            print(f"   ⚠️ Could not drop '{coll}': {e}")

    # Drop the entire database
    try:
        await mongo.client.drop_database(DB_NAME)
        print(f"   Dropped entire database: {DB_NAME}")
    except Exception as e:
        print(f"   ⚠️ Could not drop database '{DB_NAME}': {e}")

    await close_mongo_connection()
    print("\n✅ MongoDB Cleanup Complete!")

if __name__ == "__main__":
    asyncio.run(cleanup_mongo())
