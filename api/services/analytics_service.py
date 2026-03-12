"""
Analytics Service for Spectra AI.

Tracks campaign performance metrics: views, likes, comments, shares, CTR, impressions.
Stores analytics events in MongoDB and provides aggregated dashboard data.
"""

from datetime import datetime, timedelta
from api.services.db_mongo_service import mongo


async def init_analytics_indexes():
    """Create indexes for analytics collections."""
    if mongo.db is None:
        return
    await mongo.db.analytics_events.create_index([("campaign_id", 1), ("event_type", 1)])
    await mongo.db.analytics_events.create_index([("created_at", -1)])
    await mongo.db.campaign_metrics.create_index("campaign_id", unique=True)


async def track_event(campaign_id: str, event_type: str, user_id: str = None, metadata: dict = None):
    """
    Track a single analytics event (view, like, comment, share, click, impression).
    Also updates the aggregated campaign_metrics document.
    """
    if mongo.db is None:
        return None

    event = {
        "campaign_id": campaign_id,
        "event_type": event_type,
        "user_id": user_id,
        "metadata": metadata or {},
        "created_at": datetime.utcnow().isoformat(),
    }
    result = await mongo.db.analytics_events.insert_one(event)

    # Update aggregated metrics
    increment_field = f"metrics.{event_type}s"
    await mongo.db.campaign_metrics.update_one(
        {"campaign_id": campaign_id},
        {
            "$inc": {increment_field: 1},
            "$set": {"updated_at": datetime.utcnow().isoformat()},
            "$setOnInsert": {
                "campaign_id": campaign_id,
                "created_at": datetime.utcnow().isoformat(),
                "metrics": {
                    "views": 0,
                    "likes": 0,
                    "comments": 0,
                    "shares": 0,
                    "clicks": 0,
                    "impressions": 0,
                },
            },
        },
        upsert=True,
    )

    return str(result.inserted_id)


async def get_campaign_analytics(campaign_id: str) -> dict:
    """Get aggregated analytics for a single campaign."""
    if mongo.db is None:
        return _empty_metrics(campaign_id)

    doc = await mongo.db.campaign_metrics.find_one({"campaign_id": campaign_id})
    if not doc:
        return _empty_metrics(campaign_id)

    metrics = doc.get("metrics", {})
    impressions = metrics.get("impressions", 0)
    clicks = metrics.get("clicks", 0)
    views = metrics.get("views", 0)

    # Calculate CTR
    ctr = round((clicks / impressions * 100), 2) if impressions > 0 else 0
    engagement_rate = round(
        ((metrics.get("likes", 0) + metrics.get("comments", 0) + metrics.get("shares", 0)) / views * 100), 2
    ) if views > 0 else 0

    return {
        "campaign_id": campaign_id,
        "metrics": {
            **metrics,
            "ctr": ctr,
            "engagement_rate": engagement_rate,
        },
        "source": doc.get("source", "manual"),  # "manual" or "instagram"
        "updated_at": doc.get("updated_at"),
    }


async def get_campaign_analytics_timeline(campaign_id: str, days: int = 30) -> list:
    """Get daily breakdown of analytics events for charts."""
    if mongo.db is None:
        return []

    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    pipeline = [
        {"$match": {"campaign_id": campaign_id, "created_at": {"$gte": cutoff}}},
        {
            "$group": {
                "_id": {
                    "date": {"$substr": ["$created_at", 0, 10]},
                    "event_type": "$event_type",
                },
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id.date": 1}},
    ]

    results = []
    async for doc in mongo.db.analytics_events.aggregate(pipeline):
        results.append({
            "date": doc["_id"]["date"],
            "event_type": doc["_id"]["event_type"],
            "count": doc["count"],
        })
    return results


async def get_dashboard_analytics(user_id: str) -> dict:
    """Get aggregated analytics across all campaigns for a user."""
    if mongo.db is None:
        return {"total": _empty_totals(), "campaigns": []}

    # Get all campaign IDs for this user
    campaign_ids = []
    async for doc in mongo.db.campaigns.find({"user_id": user_id}, {"_id": 1}):
        campaign_ids.append(str(doc["_id"]))

    if not campaign_ids:
        return {"total": _empty_totals(), "campaigns": []}

    # Aggregate metrics across all campaigns
    totals = {"views": 0, "likes": 0, "comments": 0, "shares": 0, "clicks": 0, "impressions": 0}
    campaign_analytics = []

    for cid in campaign_ids:
        analytics = await get_campaign_analytics(cid)
        campaign_analytics.append(analytics)
        for key in totals:
            totals[key] += analytics["metrics"].get(key, 0)

    total_impressions = totals["impressions"]
    total_clicks = totals["clicks"]
    total_views = totals["views"]
    totals["ctr"] = round((total_clicks / total_impressions * 100), 2) if total_impressions > 0 else 0
    total_engagement = totals["likes"] + totals["comments"] + totals["shares"]
    totals["engagement_rate"] = round((total_engagement / total_views * 100), 2) if total_views > 0 else 0
    totals["total_campaigns"] = len(campaign_ids)

    # Sort campaigns by views descending
    campaign_analytics.sort(key=lambda x: x["metrics"].get("views", 0), reverse=True)

    return {
        "total": totals,
        "campaigns": campaign_analytics[:20],
    }


async def seed_demo_analytics(campaign_id: str, user_id: str):
    """Seed demo analytics data for a campaign (useful for demos)."""
    import random

    views = random.randint(1000, 50000)
    impressions = int(views * random.uniform(1.5, 3.0))
    likes = int(views * random.uniform(0.02, 0.08))
    comments = int(views * random.uniform(0.005, 0.02))
    shares = int(views * random.uniform(0.01, 0.04))
    clicks = int(impressions * random.uniform(0.01, 0.05))

    metrics = {
        "views": views,
        "impressions": impressions,
        "likes": likes,
        "comments": comments,
        "shares": shares,
        "clicks": clicks,
    }

    await mongo.db.campaign_metrics.update_one(
        {"campaign_id": campaign_id},
        {
            "$set": {
                "metrics": metrics,
                "updated_at": datetime.utcnow().isoformat(),
            },
            "$setOnInsert": {
                "campaign_id": campaign_id,
                "created_at": datetime.utcnow().isoformat(),
            },
        },
        upsert=True,
    )
    return metrics


def _empty_metrics(campaign_id: str) -> dict:
    return {
        "campaign_id": campaign_id,
        "metrics": {
            "views": 0,
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "clicks": 0,
            "impressions": 0,
            "saves": 0,
            "reach": 0,
            "ctr": 0,
            "engagement_rate": 0,
        },
        "source": "manual",
        "updated_at": None,
    }


def _empty_totals() -> dict:
    return {
        "views": 0,
        "likes": 0,
        "comments": 0,
        "shares": 0,
        "clicks": 0,
        "impressions": 0,
        "saves": 0,
        "reach": 0,
        "ctr": 0,
        "engagement_rate": 0,
        "total_campaigns": 0,
    }
