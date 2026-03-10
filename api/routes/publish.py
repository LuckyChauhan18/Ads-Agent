"""
Social Media Publishing API routes.
Manages platform connections and ad publishing.
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
    """Connect a social media platform."""
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
    """Publish an ad to one or more social media platforms."""
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
