import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def list_ltm_db_contents():
    mongo_url = os.getenv("LTM_MONGODB_URL")
    if not mongo_url:
        with open("ltm_db_contents.txt", "w") as f:
            f.write("LTM_MONGODB_URL not found in .env\n")
        return
        
    client = AsyncIOMotorClient(mongo_url)
    # I don't know the DB name for LTM, so I'll list all databases
    dbs = await client.list_database_names()
    
    output = []
    output.append(f"Databases in LTM: {dbs}\n")
    
    for db_name in dbs:
        if db_name in ["admin", "local", "config"]:
            continue
        db = client[db_name]
        output.append(f"\nChecking database: {db.name}\n")
        collections = await db.list_collection_names()
        for coll_name in collections:
            count = await db[coll_name].count_documents({})
            output.append(f"Collection: {coll_name}, Count: {count}\n")
            
    client.close()
    
    with open("ltm_db_contents.txt", "w") as f:
        f.writelines(output)

if __name__ == "__main__":
    asyncio.run(list_ltm_db_contents())
