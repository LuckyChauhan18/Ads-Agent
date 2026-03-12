"""
Social Media Publishing Service for Spectra AI.

Manages platform connections and ad publishing to:
- Meta (Facebook/Instagram)  ← REAL integration via Graph API
- YouTube   (placeholder)
- TikTok    (placeholder)
- LinkedIn  (placeholder)

Stores platform credentials and publish history in MongoDB.
"""

import os
import asyncio
import httpx
from datetime import datetime
from api.services.db_mongo_service import mongo

META_GRAPH_URL = "https://graph.facebook.com/v21.0"

SUPPORTED_PLATFORMS = {
    "meta": {
        "name": "Meta (Facebook & Instagram)",
        "fields": [
            "access_token",
            "page_id",
            "instagram_account_id",
        ],
        "icon": "facebook",
        "description": "Publish video ads as Instagram Reels and Facebook posts.",
    },
    "youtube": {
        "name": "YouTube",
        "fields": ["api_key", "channel_id"],
        "icon": "youtube",
        "description": "Upload video ads to your YouTube channel.",
    },
    "tiktok": {
        "name": "TikTok",
        "fields": ["access_token", "advertiser_id"],
        "icon": "tiktok",
        "description": "Publish short-form video ads on TikTok.",
    },
    "linkedin": {
        "name": "LinkedIn",
        "fields": ["access_token", "organization_id"],
        "icon": "linkedin",
        "description": "Share video ads on your LinkedIn company page.",
    },
}


# ─── Index Setup ──────────────────────────────────────────────

async def init_publish_indexes():
    """Create indexes for publish collections."""
    if mongo.db is None:
        return
    await mongo.db.platform_connections.create_index(
        [("user_id", 1), ("platform", 1)], unique=True
    )
    await mongo.db.publish_history.create_index(
        [("campaign_id", 1), ("created_at", -1)]
    )


# ─── Platform CRUD ────────────────────────────────────────────

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
                "description": info.get("description", ""),
            })

    return platforms


async def connect_platform(user_id: str, platform: str, credentials: dict) -> dict:
    """
    Connect a social media platform with credentials.

    For Meta: validates the access token by calling /me endpoint,
    then auto-discovers the Instagram Business Account ID if not provided.
    """
    if platform not in SUPPORTED_PLATFORMS:
        raise ValueError(f"Unsupported platform: {platform}")

    if mongo.db is None:
        return {"status": "error", "message": "Database unavailable"}

    account_name = credentials.get("account_name", "")

    # ── Meta: Validate token & discover IG account ────────────
    if platform == "meta":
        access_token = credentials.get("access_token", "")
        page_id = credentials.get("page_id", "")

        if not access_token:
            raise ValueError("access_token is required for Meta")
        if not page_id:
            raise ValueError("page_id is required for Meta")

        async with httpx.AsyncClient(timeout=30) as client:
            # 1. Validate token
            me_resp = await client.get(
                f"{META_GRAPH_URL}/me",
                params={"access_token": access_token},
            )
            if me_resp.status_code != 200:
                raise ValueError(
                    f"Invalid Meta access token: {me_resp.json().get('error', {}).get('message', 'unknown')}"
                )
            me_data = me_resp.json()
            account_name = me_data.get("name", account_name)

            # 2. Auto-discover Instagram Business Account if not provided
            ig_account_id = credentials.get("instagram_account_id", "")
            if not ig_account_id:
                ig_resp = await client.get(
                    f"{META_GRAPH_URL}/{page_id}",
                    params={
                        "fields": "instagram_business_account",
                        "access_token": access_token,
                    },
                )
                if ig_resp.status_code == 200:
                    ig_data = ig_resp.json()
                    ig_biz = ig_data.get("instagram_business_account", {})
                    ig_account_id = ig_biz.get("id", "")

                if not ig_account_id:
                    raise ValueError(
                        "Could not find an Instagram Business Account linked to this Page. "
                        "Make sure your Facebook Page is connected to an Instagram Professional account."
                    )

                credentials["instagram_account_id"] = ig_account_id

    doc = {
        "user_id": user_id,
        "platform": platform,
        "credentials": credentials,
        "account_name": account_name,
        "connected_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    await mongo.db.platform_connections.update_one(
        {"user_id": user_id, "platform": platform},
        {"$set": doc},
        upsert=True,
    )

    return {
        "status": "connected",
        "platform": platform,
        "account_name": account_name,
        "instagram_account_id": credentials.get("instagram_account_id", ""),
    }


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


# ─── Publishing ───────────────────────────────────────────────

async def publish_ad(
    user_id: str, campaign_id: str, platforms: list, config: dict = None
) -> dict:
    """
    Publish an ad to one or more platforms.

    For Meta: uploads video to Instagram as a Reel via the Graph API.
    Other platforms: returns a placeholder (not yet integrated).
    """
    if mongo.db is None:
        return {"status": "error", "message": "Database unavailable"}

    from bson import ObjectId

    try:
        campaign = await mongo.db.campaigns.find_one({"_id": ObjectId(campaign_id)})
    except Exception:
        campaign = await mongo.db.campaigns.find_one({"_id": campaign_id})

    if not campaign:
        raise ValueError(f"Campaign {campaign_id} not found")

    if campaign.get("user_id") != user_id:
        raise ValueError("Unauthorized: campaign does not belong to user")

    results = []
    for platform in platforms:
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

        # ── Route to the correct publisher ────────────────────
        if platform == "meta":
            publish_result = await _publish_to_meta(campaign, connection, config or {})
        else:
            publish_result = await _placeholder_publish(platform, campaign)

        # Save to publish history
        history_entry = {
            "campaign_id": campaign_id,
            "user_id": user_id,
            "platform": platform,
            "status": publish_result["status"],
            "external_id": publish_result.get("external_id"),
            "external_url": publish_result.get("external_url"),
            "ig_media_id": publish_result.get("ig_media_id"),
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


# ─── Meta / Instagram Publishing (REAL) ──────────────────────

async def _publish_to_meta(campaign: dict, connection: dict, config: dict) -> dict:
    """
    Publish a video ad to Instagram as a Reel via Meta Graph API.

    Flow:
      1. Get the video's public URL (upload to R2 if needed)
      2. Create an IG media container (type=REELS, video_url, caption)
      3. Poll until the container is FINISHED
      4. Publish the container
      5. Return the media ID and permalink
    """
    creds = connection.get("credentials", {})
    access_token = creds.get("access_token", "")
    ig_account_id = creds.get("instagram_account_id", "")

    if not access_token or not ig_account_id:
        return {
            "platform": "meta",
            "status": "error",
            "message": "Missing access_token or instagram_account_id. Reconnect Meta.",
        }

    # ── 1. Resolve a publicly accessible video URL ────────────
    video_url = await _resolve_video_url(campaign, config)
    if not video_url:
        return {
            "platform": "meta",
            "status": "error",
            "message": "No video URL found for this campaign. Render the ad first.",
        }

    # Build caption from campaign data
    caption = _build_caption(campaign, config)

    async with httpx.AsyncClient(timeout=120) as client:
        # ── 2. Create media container ─────────────────────────
        container_resp = await client.post(
            f"{META_GRAPH_URL}/{ig_account_id}/media",
            params={
                "media_type": "REELS",
                "video_url": video_url,
                "caption": caption,
                "share_to_feed": "true",
                "access_token": access_token,
            },
        )

        if container_resp.status_code != 200:
            error = container_resp.json().get("error", {})
            return {
                "platform": "meta",
                "status": "error",
                "message": f"IG container creation failed: {error.get('message', container_resp.text)}",
                "error_code": error.get("code"),
            }

        container_id = container_resp.json().get("id")
        if not container_id:
            return {
                "platform": "meta",
                "status": "error",
                "message": "No container ID returned from Instagram.",
            }

        # ── 3. Poll container status until FINISHED ───────────
        status = "IN_PROGRESS"
        max_polls = 30  # ~5 minutes
        for _ in range(max_polls):
            await asyncio.sleep(10)
            status_resp = await client.get(
                f"{META_GRAPH_URL}/{container_id}",
                params={
                    "fields": "status_code,status",
                    "access_token": access_token,
                },
            )
            if status_resp.status_code == 200:
                data = status_resp.json()
                status = data.get("status_code", data.get("status", "IN_PROGRESS"))
                if status == "FINISHED":
                    break
                if status == "ERROR":
                    return {
                        "platform": "meta",
                        "status": "error",
                        "message": f"IG media processing failed: {data}",
                    }

        if status != "FINISHED":
            return {
                "platform": "meta",
                "status": "error",
                "message": "Instagram video processing timed out. Try again later.",
            }

        # ── 4. Publish the container ──────────────────────────
        publish_resp = await client.post(
            f"{META_GRAPH_URL}/{ig_account_id}/media_publish",
            params={
                "creation_id": container_id,
                "access_token": access_token,
            },
        )

        if publish_resp.status_code != 200:
            error = publish_resp.json().get("error", {})
            return {
                "platform": "meta",
                "status": "error",
                "message": f"IG publish failed: {error.get('message', publish_resp.text)}",
            }

        media_id = publish_resp.json().get("id")

        # ── 5. Get the permalink ──────────────────────────────
        permalink = ""
        if media_id:
            perm_resp = await client.get(
                f"{META_GRAPH_URL}/{media_id}",
                params={
                    "fields": "permalink,shortcode",
                    "access_token": access_token,
                },
            )
            if perm_resp.status_code == 200:
                perm_data = perm_resp.json()
                permalink = perm_data.get("permalink", "")

        return {
            "platform": "meta",
            "status": "published",
            "external_id": media_id or container_id,
            "ig_media_id": media_id,
            "external_url": permalink or f"https://www.instagram.com/p/{media_id}/",
            "message": "Ad published to Instagram as a Reel",
            "published_at": datetime.utcnow().isoformat(),
        }


async def _resolve_video_url(campaign: dict, config: dict) -> str:
    """
    Get a publicly accessible video URL for a campaign.

    Priority:
      1. config.video_url (explicit override from frontend)
      2. campaign.video_url if it's already a public URL (R2 / https)
      3. Upload local file to R2 and return public URL
    """
    # Explicit override
    if config.get("video_url"):
        return config["video_url"]

    video_url = campaign.get("video_url", "")

    # Already a public URL
    if video_url.startswith("https://"):
        return video_url

    # Local file → upload to R2
    if video_url.startswith("http://localhost") or video_url.startswith("http://127.0.0.1"):
        local_path = _url_to_local_path(video_url)
        if local_path and os.path.isfile(local_path):
            from api.services.r2_service import upload_video_to_r2

            campaign_id = str(campaign.get("_id", ""))
            public_url = upload_video_to_r2(local_path, campaign_id)

            # Update campaign with the new public URL
            if mongo.db is not None:
                await mongo.db.campaigns.update_one(
                    {"_id": campaign["_id"]},
                    {"$set": {"video_url": public_url}},
                )

            return public_url

    # Check render_results for local path
    production = campaign.get("production", {})
    render_results = production.get("render_results", [])
    if not render_results:
        render_results = campaign.get("render_results", [])

    if render_results:
        first = render_results[0] if isinstance(render_results, list) else {}
        local_path = first.get("local_path", "")
        if local_path and os.path.isfile(local_path):
            from api.services.r2_service import upload_video_to_r2

            campaign_id = str(campaign.get("_id", ""))
            public_url = upload_video_to_r2(local_path, campaign_id)

            # Update campaign with public URL
            if mongo.db is not None:
                await mongo.db.campaigns.update_one(
                    {"_id": campaign["_id"]},
                    {"$set": {"video_url": public_url}},
                )

            return public_url

    return video_url


def _url_to_local_path(url: str) -> str:
    """Convert a localhost video URL to a local filesystem path."""
    # http://localhost:8000/videos/ad_variant_A_gemini_A_123456.mp4
    # → /path/to/project/agents/video/ad_variant_A_gemini_A_123456.mp4
    try:
        filename = url.split("/videos/")[-1]
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(base_dir, "agents", "video", filename)
    except Exception:
        return ""


def _build_caption(campaign: dict, config: dict) -> str:
    """Build an Instagram caption from campaign data."""
    if config.get("caption"):
        return config["caption"]

    parts = []

    # Campaign name / brand
    brand = campaign.get("brand_name", "") or campaign.get("product_name", "")
    if brand:
        parts.append(brand)

    # Tagline or hook from script
    creative = campaign.get("creative", {})
    script = creative.get("script_output", {})
    if isinstance(script, dict):
        hook = script.get("hook", "") or script.get("opening_hook", "")
        if hook:
            parts.append(hook)

    # Offer
    strategy = campaign.get("strategy", {})
    psych = strategy.get("campaign_psychology", {})
    offer = psych.get("offer", psych.get("offer_and_risk_reversal", {}))
    if isinstance(offer, dict):
        offers = offer.get("offers", [])
        for o in offers:
            disc = o.get("discount", "")
            if disc:
                parts.append(disc)
                break

    # Hashtags
    parts.append("")
    parts.append("#ad #spectraai #reels")

    return "\n".join(parts)


# ─── Instagram Insights (REAL) ────────────────────────────────

async def fetch_instagram_insights(user_id: str, campaign_id: str) -> dict:
    """
    Fetch real Instagram insights for a published ad.

    Looks up the ig_media_id from publish_history, then calls
    the Instagram Insights API for reach, impressions, likes, etc.
    Returns metrics dict or empty if not available.
    """
    if mongo.db is None:
        return {"status": "error", "message": "Database unavailable"}

    # Find the most recent successful Meta publish for this campaign
    publish_entry = await mongo.db.publish_history.find_one(
        {
            "campaign_id": campaign_id,
            "platform": "meta",
            "status": "published",
            "ig_media_id": {"$exists": True, "$ne": None},
        },
        sort=[("created_at", -1)],
    )

    if not publish_entry:
        return {"status": "no_publish", "message": "No Instagram publish found for this campaign."}

    ig_media_id = publish_entry.get("ig_media_id")
    if not ig_media_id:
        return {"status": "error", "message": "No Instagram media ID found."}

    # Get access token from platform connection
    connection = await mongo.db.platform_connections.find_one(
        {"user_id": user_id, "platform": "meta"}
    )
    if not connection:
        return {"status": "error", "message": "Meta platform not connected."}

    access_token = connection.get("credentials", {}).get("access_token", "")
    if not access_token:
        return {"status": "error", "message": "No access token found."}

    # ── Call Instagram Insights API ───────────────────────────
    # Reels metrics
    metrics_str = "impressions,reach,likes,comments,shares,saved,plays,total_interactions"

    async with httpx.AsyncClient(timeout=30) as client:
        # Try Reels-specific insights first
        insights_resp = await client.get(
            f"{META_GRAPH_URL}/{ig_media_id}/insights",
            params={
                "metric": metrics_str,
                "access_token": access_token,
            },
        )

        metrics = {}

        if insights_resp.status_code == 200:
            insights_data = insights_resp.json().get("data", [])
            for item in insights_data:
                name = item.get("name", "")
                values = item.get("values", [])
                value = values[0].get("value", 0) if values else 0
                metrics[name] = value
        else:
            # Fallback: try basic media fields
            fields_resp = await client.get(
                f"{META_GRAPH_URL}/{ig_media_id}",
                params={
                    "fields": "like_count,comments_count,media_type,permalink,timestamp",
                    "access_token": access_token,
                },
            )
            if fields_resp.status_code == 200:
                data = fields_resp.json()
                metrics["likes"] = data.get("like_count", 0)
                metrics["comments"] = data.get("comments_count", 0)
                metrics["permalink"] = data.get("permalink", "")

        # ── Map IG metrics → our analytics format ─────────────
        mapped = {
            "views": metrics.get("plays", metrics.get("impressions", 0)),
            "impressions": metrics.get("impressions", metrics.get("reach", 0)),
            "likes": metrics.get("likes", metrics.get("like_count", 0)),
            "comments": metrics.get("comments", metrics.get("comments_count", 0)),
            "shares": metrics.get("shares", 0),
            "saves": metrics.get("saved", 0),
            "reach": metrics.get("reach", 0),
            "total_interactions": metrics.get("total_interactions", 0),
        }

        return {
            "status": "ok",
            "platform": "meta",
            "ig_media_id": ig_media_id,
            "metrics": mapped,
            "fetched_at": datetime.utcnow().isoformat(),
        }


async def sync_instagram_to_analytics(user_id: str, campaign_id: str) -> dict:
    """
    Fetch Instagram insights and sync them into our analytics_service.

    This updates the campaign_metrics collection so the dashboard
    shows real numbers from Instagram.
    """
    insights = await fetch_instagram_insights(user_id, campaign_id)

    if insights.get("status") != "ok":
        return insights

    metrics = insights.get("metrics", {})

    if mongo.db is None:
        return {"status": "error", "message": "Database unavailable"}

    # Upsert into campaign_metrics
    now = datetime.utcnow().isoformat()
    await mongo.db.campaign_metrics.update_one(
        {"campaign_id": campaign_id},
        {
            "$set": {
                "metrics.views": metrics.get("views", 0),
                "metrics.impressions": metrics.get("impressions", 0),
                "metrics.likes": metrics.get("likes", 0),
                "metrics.comments": metrics.get("comments", 0),
                "metrics.shares": metrics.get("shares", 0),
                "metrics.saves": metrics.get("saves", 0),
                "metrics.reach": metrics.get("reach", 0),
                "source": "instagram",
                "updated_at": now,
            },
            "$setOnInsert": {
                "campaign_id": campaign_id,
                "created_at": now,
            },
        },
        upsert=True,
    )

    # Calculate derived metrics
    views = metrics.get("views", 0)
    impressions = metrics.get("impressions", 0)
    likes = metrics.get("likes", 0)
    comments = metrics.get("comments", 0)
    shares = metrics.get("shares", 0)

    ctr = 0
    engagement_rate = 0
    if impressions > 0:
        ctr = round((views / impressions * 100), 2)
    if views > 0:
        engagement_rate = round(((likes + comments + shares) / views * 100), 2)

    await mongo.db.campaign_metrics.update_one(
        {"campaign_id": campaign_id},
        {
            "$set": {
                "metrics.ctr": ctr,
                "metrics.engagement_rate": engagement_rate,
            }
        },
    )

    return {
        "status": "synced",
        "campaign_id": campaign_id,
        "metrics": {**metrics, "ctr": ctr, "engagement_rate": engagement_rate},
        "synced_at": now,
    }


# ─── Placeholder for other platforms ──────────────────────────

async def _placeholder_publish(platform: str, campaign: dict) -> dict:
    """
    Placeholder for platforms not yet integrated.
    Returns a clear message telling the user it's not ready.
    """
    return {
        "platform": platform,
        "status": "not_implemented",
        "message": (
            f"{SUPPORTED_PLATFORMS.get(platform, {}).get('name', platform)} "
            f"publishing is coming soon. Currently only Meta (Instagram) is supported."
        ),
    }
