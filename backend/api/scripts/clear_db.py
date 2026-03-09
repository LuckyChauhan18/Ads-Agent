import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Use absolute path for .env to avoid any confusion
env_path = r"c:\Users\Lucky\OneDrive\Desktop\AI Add Gen\.env"
if os.path.exists(env_path):
    print(f"Loading .env from: {env_path}")
    load_dotenv(env_path)
else:
    print(f"CRITICAL: .env NOT FOUND at {env_path}")

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://luckymilak243_db_user:bQgoOdIb2bqV2NBk@cluster0.k6ibp6d.mongodb.net/?appName=Cluster0")
DB_NAME = "ai_ad_generator"

def clear_db():
    try:
        client = MongoClient(MONGODB_URL)
        db = client[DB_NAME]
        
        collections = ["products", "research", "campaigns", "scripts", "assets"]
        
        for collection_name in collections:
            print(f"Clearing collection: {collection_name}...")
            result = db[collection_name].delete_many({})
            print(f"Deleted {result.deleted_count} documents from {collection_name}.")
            
        print("Database cleared successfully (schema preserved).")
    except Exception as e:
        print(f"Error clearing database: {e}")

if __name__ == "__main__":
    clear_db()
