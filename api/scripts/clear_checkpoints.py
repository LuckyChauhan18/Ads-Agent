import os
from pymongo import MongoClient
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://luckymilak243_db_user:cb2v...fallback")

def clear_checkpoints():
    try:
        client = MongoClient(MONGODB_URL)
        # 1. Check ai_ad_generator DB
        db1 = client["ai_ad_generator"]
        # 2. Check default MongoDBSaver DB
        db2 = client["checkpointing_db"]
        
        for db in [db1, db2]:
            print(f"Checking Database: {db.name}...")
            colls = db.list_collection_names()
            for coll in ["checkpoints", "checkpoint_writes"]:
                if coll in colls:
                    print(f" -> Clearing collection: {coll} in {db.name}...")
                    res = db[coll].delete_many({})
                    print(f"    Deleted {res.deleted_count} documents.")
        
        print("Graph Checkpoints cleared successfully.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    clear_checkpoints()
