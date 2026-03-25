import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

async def count_docs():
    mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_url)
    db = client.get_database("ai_ad_generator")
    
    collections = await db.list_collection_names()
    print(f"Connected to database: {db.name}")
    print("--- Document Counts ---")
    
    total = 0
    for coll_name in collections:
        count = await db[coll_name].count_documents({})
        print(f"Collection '{coll_name}': {count} documents")
        total += count
        
    print("-----------------------")
    print(f"Total Documents: {total}")
    client.close()

if __name__ == "__main__":
    asyncio.run(count_docs())
