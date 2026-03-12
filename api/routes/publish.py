"""
Social Media Publishing API routes.
Manages platform connections, ad publishing, and Instagram insights.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from api.auth_utils import get_current_user
from api.services.publish_service import (
    get_connected_platforms,
    connect_platform,
    disconnect_platform,
    publish_ad,
    get_publish_history,
    fetch_instagram_insights,
    sync_instagram_to_analytics,
)

router = APIRouter(prefix="/publish", tags=["Publish"])


class ConnectPlatformRequest(BaseModel):
    platform: str
    credentials: dict


class DisconnectPlatformRequest(BaseModel):
    platform: str


class PublishAdRequest(BaseModel):
    campaign_id: str
    platforms: List[str]
    config: Optional[dict] = None


@router.get("/platforms")
async def list_platforms(current_user: dict = Depends(get_current_user)):
    """Get all available platforms and their connection status."""
    user_id = str(current_user["_id"])
    platforms = await get_connected_platforms(user_id)
    return {"platforms": platforms}


@router.post("/platforms/connect")
async def connect(req: ConnectPlatformRequest, current_user: dict = Depends(get_current_user)):
    """
    Connect a social media platform.

    For Meta, provide:
      - access_token: Page Access Token with instagram_basic, instagram_content_publish, pages_read_engagement
      - page_id: Facebook Page ID
      - instagram_account_id: (optional) auto-discovered from Page if not provided
    """
    user_id = str(current_user["_id"])
    try:
        result = await connect_platform(user_id, req.platform, req.credentials)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/platforms/disconnect")
async def disconnect(req: DisconnectPlatformRequest, current_user: dict = Depends(get_current_user)):
    """Disconnect a social media platform."""
    user_id = str(current_user["_id"])
    result = await disconnect_platform(user_id, req.platform)
    return result


@router.post("/push")
async def push_ad(req: PublishAdRequest, current_user: dict = Depends(get_current_user)):
    """
    Publish an ad to one or more social media platforms.

    For Meta/Instagram: uploads the video as an Instagram Reel.
    Pass optional config.caption to override the auto-generated caption.
    Pass optional config.video_url to use a specific public video URL.
    """
    user_id = str(current_user["_id"])
    try:
        result = await publish_ad(user_id, req.campaign_id, req.platforms, req.config)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history/{campaign_id}")
async def publish_history(campaign_id: str, current_user: dict = Depends(get_current_user)):
    """Get publish history for a campaign."""
    history = await get_publish_history(campaign_id)
    return {"history": history}


# ─── Instagram Insights ──────────────────────────────────────

@router.get("/insights/{campaign_id}")
async def get_insights(campaign_id: str, current_user: dict = Depends(get_current_user)):
    """
    Fetch real-time Instagram insights for a published campaign.

    Returns metrics like views, impressions, likes, comments, shares,
    saves, and reach directly from the Instagram API.
    """
    user_id = str(current_user["_id"])
    try:
        result = await fetch_instagram_insights(user_id, campaign_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/insights/{campaign_id}/sync")
async def sync_insights(campaign_id: str, current_user: dict = Depends(get_current_user)):
    """
    Fetch Instagram insights and sync them into the analytics dashboard.

    After calling this, the analytics dashboard will show real Instagram
    metrics (views, likes, shares, etc.) instead of demo data.
    """
    user_id = str(current_user["_id"])
    try:
        result = await sync_instagram_to_analytics(user_id, campaign_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
