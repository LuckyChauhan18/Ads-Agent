"""
MongoDB service for asset storage using Motor + GridFS.
Redis handles state/users/campaigns. MongoDB handles file assets.
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from dotenv import load_dotenv

load_dotenv()

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
    """Initialize the MongoDB connection and GridFS bucket."""
    mongo.client = AsyncIOMotorClient(MONGODB_URL)
    mongo.db = mongo.client[DB_NAME]
    mongo.fs = AsyncIOMotorGridFSBucket(mongo.db)
    
    # Initialize indexes
    await mongo.db.users.create_index("username", unique=True)
    await mongo.db.users.create_index("email", unique=True)
    await mongo.db.user_assets.create_index([("user_id", 1), ("_id", -1)])
    
    print(f"✅ Connected to MongoDB: {MONGODB_URL[:40]}...")

# ── Generic Document CRUD ───────────────────────────────────────────

async def save_document(collection_name: str, data: dict):
    """
    Saves a document to MongoDB.
    If '_id' is present and exists, updates it. Else inserts new.
    """
    from datetime import datetime
    from bson import ObjectId

    data["updated_at"] = datetime.now().isoformat()
    
    doc_id = data.get("_id")
    if doc_id:
        if isinstance(doc_id, str):
            try:
                doc_id = ObjectId(doc_id)
            except:
                pass # Already a string or custom ID
        
        await mongo.db[collection_name].update_one(
            {"_id": doc_id},
            {"$set": data},
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
        
    doc = await mongo.db[collection_name].find_one({"_id": oid})
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc


async def get_latest_document(collection_name: str, user_id: str = None):
    """Fetch the most recent document for a user."""
    query = {"user_id": user_id} if user_id else {}
    doc = await mongo.db[collection_name].find_one(query, sort=[("_id", -1)])
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc


async def get_all_documents(collection_name: str, limit: int = 50, user_id: str = None):
    """Fetch history for a user, sorted newest first."""
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
    result = await mongo.db.users.insert_one(user_data)
    return str(result.inserted_id)



async def close_mongo_connection():
    """Close the MongoDB connection."""
    if mongo.client:
        mongo.client.close()
        print("🔌 Closed MongoDB connection")


# ── GridFS Asset Operations ──────────────────────────────────────────

async def upload_file_to_gridfs(filename: str, content: bytes, metadata: dict = None):
    """
    Upload a file to MongoDB GridFS.
    Returns the GridFS file_id as a string.
    Videos are REJECTED — they are stored on local disk, not in MongoDB.
    """
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
