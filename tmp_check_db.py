import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def list_db_contents():
    mongo_url = os.getenv("MONGODB_URL")
    if not mongo_url:
        with open("db_contents.txt", "w") as f:
            f.write("MONGODB_URL not found in .env\n")
        return
        
    client = AsyncIOMotorClient(mongo_url)
    db = client.get_database("ai_ad_generator")
    
    output = []
    output.append(f"Checking database: {db.name}\n")
    collections = await db.list_collection_names()
    
    if not collections:
        output.append("No collections found.\n")
    else:
        for coll_name in collections:
            count = await db[coll_name].count_documents({})
            output.append(f"Collection: {coll_name}, Count: {count}\n")
            
    client.close()
    
    with open("db_contents.txt", "w") as f:
        f.writelines(output)

if __name__ == "__main__":
    asyncio.run(list_db_contents())
