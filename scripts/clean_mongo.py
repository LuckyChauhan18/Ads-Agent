import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Ensure root is in path to load .env correctly
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(base_dir, '.env')
load_dotenv(env_path, override=True)

MONGODB_URL = os.getenv("MONGODB_URL")
DB_NAME = "ai_ad_generator"

async def clean_mongo():
    if not MONGODB_URL:
        print("❌ MONGODB_URL not found in environment!")
        return

    print(f"🧹 Connecting to MongoDB for cleanup...")
    client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
    
    try:
        # Verify connection
        await client.admin.command('ping')
        print(f"✅ Connected to MongoDB.")
        
        # Confirmation
        print(f"⚠️  DANGEROUS: About to drop database '{DB_NAME}'")
        
        # Drop the entire database
        await client.drop_database(DB_NAME)
        print(f"🚀 Dropped database: {DB_NAME}")
        
        # Verify
        dbs = await client.list_database_names()
        if DB_NAME not in dbs:
            print(f"✨ Database '{DB_NAME}' has been successfully removed.")
        else:
            # Sometimes drop_database doesn't immediately reflect in list_database_names
            # Check for collections instead
            db = client[DB_NAME]
            colls = await db.list_collection_names()
            if not colls:
                print(f"✨ All collections in '{DB_NAME}' have been removed.")
            else:
                print(f"❌ Database '{DB_NAME}' still contains collections: {colls}")

    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
    finally:
        client.close()
        print("🔌 Connection closed.")

if __name__ == "__main__":
    asyncio.run(clean_mongo())
