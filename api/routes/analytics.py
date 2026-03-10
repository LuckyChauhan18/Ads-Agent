"""
Analytics API routes for the admin panel.
Provides campaign performance metrics, event tracking, and dashboard analytics.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from api.auth_utils import get_current_user
from api.services.analytics_service import (
    track_event,
    get_campaign_analytics,
    get_campaign_analytics_timeline,
    get_dashboard_analytics,
    seed_demo_analytics,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


class TrackEventRequest(BaseModel):
    campaign_id: str
    event_type: str
    metadata: Optional[dict] = None


@router.post("/track")
async def track_analytics_event(req: TrackEventRequest, current_user: dict = Depends(get_current_user)):
    """Track a single analytics event (view, like, share, click, comment, impression)."""
    valid_events = {"view", "like", "comment", "share", "click", "impression"}
    if req.event_type not in valid_events:
        raise HTTPException(status_code=400, detail=f"Invalid event_type. Must be one of: {valid_events}")

    event_id = await track_event(
        campaign_id=req.campaign_id,
        event_type=req.event_type,
        user_id=str(current_user["_id"]),
        metadata=req.metadata,
    )
    return {"status": "tracked", "event_id": event_id}


@router.get("/campaign/{campaign_id}")
async def get_campaign_metrics(campaign_id: str, current_user: dict = Depends(get_current_user)):
    """Get aggregated analytics for a specific campaign."""
    analytics = await get_campaign_analytics(campaign_id)
    return analytics


@router.get("/campaign/{campaign_id}/timeline")
async def get_campaign_timeline(campaign_id: str, days: int = 30, current_user: dict = Depends(get_current_user)):
    """Get daily event breakdown for charts."""
    timeline = await get_campaign_analytics_timeline(campaign_id, days=days)
    return {"timeline": timeline}


@router.get("/dashboard")
async def get_analytics_dashboard(current_user: dict = Depends(get_current_user)):
    """Get aggregated analytics across all user campaigns."""
    user_id = str(current_user["_id"])
    dashboard = await get_dashboard_analytics(user_id)
    return dashboard


@router.post("/seed/{campaign_id}")
async def seed_analytics(campaign_id: str, current_user: dict = Depends(get_current_user)):
    """Seed demo analytics data for a campaign (for testing/demos)."""
    user_id = str(current_user["_id"])
    metrics = await seed_demo_analytics(campaign_id, user_id)
    return {"status": "seeded", "metrics": metrics}
