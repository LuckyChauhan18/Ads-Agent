import asyncio
import os
import sys
import shutil

# Ensure root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.db_mongo_service import connect_to_mongo, close_mongo_connection, mongo, DB_NAME

async def cleanup():
    print("🧹 Starting Database and local file cleanup...")
    
    # Connect to Mongo
    await connect_to_mongo()
    if mongo.db is None:
        print("❌ Could not connect to MongoDB for cleanup.")
        return

    # Drop collections
    collections = [
        "campaign_history", # Sometimes used instead of campaigns
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

    # Drop the entire database (safer for "Complete Clean")
    try:
        await mongo.client.drop_database(DB_NAME)
        print(f"   Dropped entire database: {DB_NAME}")
    except Exception as e:
        print(f"   ⚠️ Could not drop database '{DB_NAME}': {e}")

    await close_mongo_connection()

    # Clear Local Folders
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    folders_to_clear = ["video", "tmp", "output", "assets"]
    
    for folder in folders_to_clear:
        path = os.path.join(base_dir, folder)
        if os.path.exists(path):
            try:
                # Instead of deleting the folder, delete contents to keep structure
                for filename in os.listdir(path):
                    file_path = os.path.join(path, filename)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        print(f"      Could not delete {file_path}: {e}")
                print(f"   Cleared local folder: {folder}")
            except Exception as e:
                print(f"   ⚠️ Could not clear folder '{folder}': {e}")

    # Specific JSON outputs
    files_to_delete = ["render_error.txt", "global_error_log.txt", "latest_campaign_debug.json"]
    for f in files_to_delete:
        p = os.path.join(base_dir, f)
        if os.path.exists(p):
            os.remove(p)
            print(f"   Deleted file: {f}")

    print("\n✅ Cleanup Complete! You have a fresh start.")

if __name__ == "__main__":
    asyncio.run(cleanup())
