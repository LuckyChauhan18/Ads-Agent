import os
from pymongo import MongoClient
from dotenv import load_dotenv

env_path = r"c:\Users\Lucky\OneDrive\Desktop\langgraph_add\.env"
if os.path.exists(env_path):
    load_dotenv(env_path)

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://luckymilak243_db_user:bQgoOdIb2bqV2NBk@cluster0.k6ibp6d.mongodb.net/?appName=Cluster0")
DB_NAME = "ai_ad_generator"

def list_collections():
    try:
        client = MongoClient(MONGODB_URL)
        db = client[DB_NAME]
        print(f"Collections in {DB_NAME}:")
        for coll in db.list_collection_names():
            print(f" - {coll} ({db[coll].count_documents({})} docs)")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_collections()
