"""
Social Media Publishing Service for Spectra AI.

Manages platform connections and ad publishing to:
- Meta (Facebook/Instagram)
- YouTube
- TikTok
- LinkedIn

Stores platform credentials and publish history in MongoDB.
"""

import os
from datetime import datetime
from api.services.db_mongo_service import mongo


SUPPORTED_PLATFORMS = {
    "meta": {
        "name": "Meta (Facebook & Instagram)",
        "fields": ["access_token", "ad_account_id", "page_id"],
        "icon": "facebook",
    },
    "youtube": {
        "name": "YouTube",
        "fields": ["api_key", "channel_id"],
        "icon": "youtube",
    },
    "tiktok": {
        "name": "TikTok",
        "fields": ["access_token", "advertiser_id"],
        "icon": "tiktok",
    },
    "linkedin": {
        "name": "LinkedIn",
        "fields": ["access_token", "organization_id"],
        "icon": "linkedin",
    },
}


async def init_publish_indexes():
    """Create indexes for publish collections."""
    if mongo.db is None:
        return
    await mongo.db.platform_connections.create_index(
        [("user_id", 1), ("platform", 1)], unique=True
    )
    await mongo.db.publish_history.create_index([("campaign_id", 1), ("created_at", -1)])


async def get_connected_platforms(user_id: str) -> list:
    """Get all connected platforms for a user."""
    if mongo.db is None:
        return []

    platforms = []
    async for doc in mongo.db.platform_connections.find({"user_id": user_id}):
        platforms.append({
            "platform": doc["platform"],
            "name": SUPPORTED_PLATFORMS.get(doc["platform"], {}).get("name", doc["platform"]),
            "connected": True,
            "connected_at": doc.get("connected_at"),
            "account_name": doc.get("account_name", ""),
        })

    # Add disconnected platforms
    connected = {p["platform"] for p in platforms}
    for key, info in SUPPORTED_PLATFORMS.items():
        if key not in connected:
            platforms.append({
                "platform": key,
                "name": info["name"],
                "connected": False,
                "fields": info["fields"],
            })

    return platforms


async def connect_platform(user_id: str, platform: str, credentials: dict) -> dict:
    """Connect a social media platform with credentials."""
    if platform not in SUPPORTED_PLATFORMS:
        raise ValueError(f"Unsupported platform: {platform}")

    if mongo.db is None:
        return {"status": "error", "message": "Database unavailable"}

    doc = {
        "user_id": user_id,
        "platform": platform,
        "credentials": credentials,
        "account_name": credentials.get("account_name", ""),
        "connected_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    await mongo.db.platform_connections.update_one(
        {"user_id": user_id, "platform": platform},
        {"$set": doc},
        upsert=True,
    )

    return {"status": "connected", "platform": platform}


async def disconnect_platform(user_id: str, platform: str) -> dict:
    """Disconnect a social media platform."""
    if mongo.db is None:
        return {"status": "error", "message": "Database unavailable"}

    result = await mongo.db.platform_connections.delete_one(
        {"user_id": user_id, "platform": platform}
    )

    if result.deleted_count > 0:
        return {"status": "disconnected", "platform": platform}
    return {"status": "not_found", "platform": platform}


async def publish_ad(user_id: str, campaign_id: str, platforms: list, config: dict = None) -> dict:
    """
    Publish an ad to one or more platforms.

    In production, this would call each platform's API.
    Currently stores publish intent and simulates the push.
    """
    if mongo.db is None:
        return {"status": "error", "message": "Database unavailable"}

    # Get campaign data
    from bson import ObjectId
    try:
        campaign = await mongo.db.campaigns.find_one({"_id": ObjectId(campaign_id)})
    except Exception:
        campaign = await mongo.db.campaigns.find_one({"_id": campaign_id})

    if not campaign:
        raise ValueError(f"Campaign {campaign_id} not found")

    # Verify user owns this campaign
    if campaign.get("user_id") != user_id:
        raise ValueError("Unauthorized: campaign does not belong to user")

    results = []
    for platform in platforms:
        # Check if platform is connected
        connection = await mongo.db.platform_connections.find_one(
            {"user_id": user_id, "platform": platform}
        )

        if not connection:
            results.append({
                "platform": platform,
                "status": "error",
                "message": f"{platform} is not connected. Please connect it first.",
            })
            continue

        # Simulate publishing (in production, call real APIs)
        publish_result = await _simulate_platform_publish(
            platform, campaign, connection, config or {}
        )

        # Save to publish history
        history_entry = {
            "campaign_id": campaign_id,
            "user_id": user_id,
            "platform": platform,
            "status": publish_result["status"],
            "external_id": publish_result.get("external_id"),
            "external_url": publish_result.get("external_url"),
            "config": config or {},
            "created_at": datetime.utcnow().isoformat(),
        }
        await mongo.db.publish_history.insert_one(history_entry)

        results.append(publish_result)

    return {"results": results}


async def get_publish_history(campaign_id: str) -> list:
    """Get publish history for a campaign."""
    if mongo.db is None:
        return []

    history = []
    async for doc in mongo.db.publish_history.find(
        {"campaign_id": campaign_id}
    ).sort("created_at", -1):
        doc["_id"] = str(doc["_id"])
        history.append(doc)

    return history


async def _simulate_platform_publish(platform: str, campaign: dict, connection: dict, config: dict) -> dict:
    """
    Simulate publishing to a platform.
    In production, this would use real platform APIs:
    - Meta: Marketing API to create ad creative + campaign
    - YouTube: YouTube Data API to upload video
    - TikTok: TikTok Marketing API
    - LinkedIn: LinkedIn Marketing API
    """
    import random
    import string

    external_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))

    platform_urls = {
        "meta": f"https://www.facebook.com/ads/library/?id={external_id}",
        "youtube": f"https://youtube.com/watch?v={external_id[:11]}",
        "tiktok": f"https://www.tiktok.com/@brand/video/{external_id}",
        "linkedin": f"https://www.linkedin.com/feed/update/urn:li:activity:{external_id}",
    }

    return {
        "platform": platform,
        "status": "published",
        "external_id": external_id,
        "external_url": platform_urls.get(platform, ""),
        "message": f"Ad published to {SUPPORTED_PLATFORMS.get(platform, {}).get('name', platform)}",
        "published_at": datetime.utcnow().isoformat(),
    }
