"""
MongoDB service for asset storage using Motor + GridFS.
Redis handles state/users/campaigns. MongoDB handles file assets.
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from dotenv import load_dotenv

load_dotenv(override=True)

MONGODB_URL = os.getenv("MONGODB_URL")
if not MONGODB_URL:
    raise ValueError("MONGODB_URL not found in environment")

DB_NAME = "ai_ad_generator"


class MongoDB:
    client: AsyncIOMotorClient = None
    db = None
    fs: AsyncIOMotorGridFSBucket = None


mongo = MongoDB()


async def connect_to_mongo():
    """Initialize the MongoDB connection and GridFS bucket with high resilience."""
    try:
        # serverSelectionTimeoutMS=5000: Fail fast (5s) instead of hanging for 20s
        mongo.client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
        mongo.db = mongo.client[DB_NAME]
        
        # Verify connection immediately
        await mongo.client.admin.command('ping')
        
        mongo.fs = AsyncIOMotorGridFSBucket(mongo.db)
        
        # Initialize indexes
        await mongo.db.users.create_index("username", unique=True)
        # Drop old strict email index if it exists, then create sparse version
        try:
            await mongo.db.users.drop_index("email_1")
        except Exception:
            pass  # Index might not exist yet
        # Sparse index: only enforce unique email when email is actually set (not null)
        await mongo.db.users.create_index("email", unique=True, sparse=True)
        await mongo.db.user_assets.create_index([("user_id", 1), ("_id", -1)])
        
        print(f"✅ Connected to MongoDB: {MONGODB_URL[:40]}...")
    except Exception as e:
        print(f"❌ MongoDB Connection Failed: {e}")
        # Mark as unavailable so CRUD ops can fallback
        mongo.client = None
        mongo.db = None
        mongo.fs = None

# ── Generic Document CRUD ───────────────────────────────────────────

async def save_document(collection_name: str, data: dict):
    """
    Saves a document to MongoDB.
    If '_id' is present and exists, updates it. Else inserts new.
    """
    from datetime import datetime
    from bson import ObjectId

    if mongo.db is None:
        print(f"⚠️ [Fallback] MongoDB unavailable. Mocking save for {collection_name}")
        return str(ObjectId())

    data["updated_at"] = datetime.now().isoformat()
    
    doc_id = data.get("_id")
    if doc_id:
        if isinstance(doc_id, str):
            try:
                doc_id = ObjectId(doc_id)
            except:
                pass # Already a string or custom ID
        
        # Create a copy to avoid modifying original and remove _id for $set
        update_data = dict(data)
        if "_id" in update_data:
            del update_data["_id"]

        await mongo.db[collection_name].update_one(
            {"_id": doc_id},
            {"$set": update_data},
            upsert=True
        )
        return str(doc_id)
    else:

        result = await mongo.db[collection_name].insert_one(data)
        return str(result.inserted_id)


async def get_document(collection_name: str, doc_id: str):
    """Fetch a single document by ID."""
    from bson import ObjectId
    try:
        oid = ObjectId(doc_id)
    except:
        oid = doc_id
    
    if mongo.db is None:
        return None
        
    doc = await mongo.db[collection_name].find_one({"_id": oid})
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc


async def get_latest_document(collection_name: str, user_id: str = None):
    """Fetch the most recent document for a user."""
    if mongo.db is None:
        return None
    query = {"user_id": user_id} if user_id else {}
    doc = await mongo.db[collection_name].find_one(query, sort=[("_id", -1)])
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc


async def get_all_documents(collection_name: str, limit: int = 50, user_id: str = None):
    """Fetch history for a user, sorted newest first."""
    if mongo.db is None:
        return []
    query = {"user_id": user_id} if user_id else {}
    docs = []
    cursor = mongo.db[collection_name].find(query).sort("_id", -1).limit(limit)
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        docs.append(doc)
    return docs


# ── User CRUD ────────────────────────────────────────────────────────

async def find_user_by_username(username: str):
    """Look up user by username."""
    if mongo.db is None:
        # DEV BYPASS: Allow 'admin' to login even when DB is down
        if username == "admin":
            return {"_id": "000000000000000000000001", "username": "admin", "hashed_password": "MOCK_PASSWORD", "full_name": "Dev Admin"}
        return None
    user = await mongo.db.users.find_one({"username": username})
    if user:
        user["_id"] = str(user["_id"])
    return user


async def find_user_by_email(email: str):
    """Look up user by email."""
    user = await mongo.db.users.find_one({"email": email})
    if user:
        user["_id"] = str(user["_id"])
    return user


async def create_user(user_data: dict):
    """Insert a new user document."""
    if mongo.db is None:
        raise Exception("Database is not connected. Please check your MongoDB configuration.")
    result = await mongo.db.users.insert_one(user_data)
    return str(result.inserted_id)



async def close_mongo_connection():
    """Close the MongoDB connection."""
    if mongo.client is not None:
        mongo.client.close()
        print("🔌 Closed MongoDB connection")


# ── GridFS Asset Operations ──────────────────────────────────────────

async def upload_file_to_gridfs(filename: str, content: bytes, metadata: dict = None):
    """
    Upload a file to MongoDB GridFS.
    Returns the GridFS file_id as a string.
    Videos are REJECTED — they are stored on local disk, not in MongoDB.
    """
    if mongo.fs is None:
        print(f"⚠️ [Fallback] MongoDB GridFS unavailable. Mocking upload for {filename}")
        from bson import ObjectId
        return str(ObjectId())

    # ── Block video files from being stored in MongoDB ──
    VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".webm", ".mkv", ".wmv", ".flv", ".m4v"}
    VIDEO_CONTENT_TYPES = {"video/mp4", "video/quicktime", "video/x-msvideo", "video/webm", "video/x-matroska"}

    ext = os.path.splitext(filename)[1].lower()
    content_type = (metadata or {}).get("content_type", "")

    if ext in VIDEO_EXTENSIONS or content_type in VIDEO_CONTENT_TYPES:
        raise ValueError(
            f"Video files are not stored in MongoDB. "
            f"Rejected: '{filename}' (type={content_type or ext}). "
            f"Videos should be served from local disk."
        )
    file_id = await mongo.fs.upload_from_stream(
        filename,
        content,
        metadata=metadata or {}
    )
    
    # Index asset for the user so we can query by user later
    if metadata and "user_id" in metadata:
        user_id = metadata["user_id"]
        # Store a reference doc in a 'user_assets' collection for quick lookups
        await mongo.db.user_assets.insert_one({
            "user_id": user_id,
            "file_id": file_id,
            "filename": filename,
            "metadata": metadata,
        })
    
    return str(file_id)


async def get_file_from_gridfs(file_id: str):
    """
    Download a file from MongoDB GridFS by its ID.
    Returns (bytes, metadata_dict).
    """
    from bson import ObjectId
    oid = ObjectId(file_id)
    
    # Read the bytes
    grid_out = await mongo.fs.open_download_stream(oid)
    content = await grid_out.read()
    metadata = grid_out.metadata or {}
    
    return content, metadata


async def get_user_assets(user_id: str):
    """
    Fetch all asset metadata for a given user from MongoDB.
    Returns a list of dicts with _id, filename, metadata.
    """
    assets = []
    cursor = mongo.db.user_assets.find({"user_id": user_id}).sort("_id", -1)
    async for doc in cursor:
        assets.append({
            "_id": str(doc["file_id"]),
            "file_id": doc["file_id"], # Keep the ObjectId for generation_time
            "filename": doc.get("filename", ""),
            "metadata": doc.get("metadata", {}),
        })
    return assets


async def delete_file_from_gridfs(file_id: str):
    """Delete a file from GridFS."""
    from bson import ObjectId
    oid = ObjectId(file_id)
    await mongo.fs.delete(oid)
    # Also remove from user_assets index
    await mongo.db.user_assets.delete_many({"file_id": oid})


# ── Feedback Operations ──────────────────────────────────────────────

async def save_feedback(feedback_data: dict):
    """
    Save video/ad feedback to the 'feedback' MongoDB collection.
    Returns the inserted document ID as a string.
    """
    result = await mongo.db.feedback.insert_one(feedback_data)
    return str(result.inserted_id)


async def get_all_feedback(limit: int = 50):
    """
    Retrieve recent feedback entries from the 'feedback' collection.
    Returns a list of dicts.
    """
    feedback_list = []
    cursor = mongo.db.feedback.find().sort("_id", -1).limit(limit)
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        feedback_list.append(doc)
    return feedback_list


async def get_user_avatar_history(user_id: str):
    """
    Fetch all unique avatars used by the user from their asset history.
    """
    avatars = []
    # Query user_assets for type='avatar'
    cursor = mongo.db.user_assets.find({
        "user_id": user_id,
        "$or": [
            {"metadata.asset_type": "avatar"},
            {"metadata.type": "avatar"}
        ]
    }).sort("_id", -1)
    
    async for doc in cursor:
        avatars.append({
            "id": str(doc["file_id"]),
            "url": f"/files/{str(doc['file_id'])}",
            "filename": doc.get("filename", "Previous Avatar"),
            "created_at": doc["_id"].generation_time.isoformat()
        })
    return avatars
