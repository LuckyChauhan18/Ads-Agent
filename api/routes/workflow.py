import os
import time
from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File, Depends
import traceback
import shutil
from api.services.pipeline_service import run_pipeline_background

router = APIRouter(prefix="/workflow", tags=["Workflow"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
VIDEO_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "video_output.json")

from api.services.db_mongo_service import (
    save_document, get_document, get_latest_document, get_all_documents,
    upload_file_to_gridfs, get_user_assets
)
from api.auth_utils import get_current_user
from datetime import datetime
from pydantic import BaseModel
from bson import ObjectId

import json

def clean_objectids(obj):
    """Ensure object is JSON serializable by converting through JSON string."""
    return json.loads(json.dumps(obj, default=str))

@router.get("/history")
async def get_history(current_user: dict = Depends(get_current_user)):
    """Fetch campaign history for the current user."""
    campaigns = await get_all_documents("campaigns", limit=20, user_id=str(current_user["_id"]))
    return clean_objectids({"results": campaigns})

@router.get("/dashboard")
async def get_dashboard(current_user: dict = Depends(get_current_user)):
    """Fetch all user-specific data for the dashboard."""
    user_id = str(current_user["_id"])
    
    # Fetch campaigns
    campaigns = await get_all_documents("campaigns", limit=50, user_id=user_id)
    
    # Fetch assets from Redis
    assets_list = await get_user_assets(user_id)
    
    # Group assets
    assets = {"logos": [], "products": [], "avatars": []}
    for asset in assets_list:
        asset_type = asset.get("metadata", {}).get("asset_type") or asset.get("metadata", {}).get("type")
        asset_id = str(asset["_id"])
        url = f"/files/{asset_id}"
        
        if asset_type == "logo":
            assets["logos"].append({"id": asset_id, "url": url, "filename": asset["filename"]})
        elif asset_type == "product":
            assets["products"].append({"id": asset_id, "url": url, "filename": asset["filename"]})
        elif asset_type == "avatar":
            assets["avatars"].append({"id": asset_id, "url": url, "filename": asset["filename"]})

    return clean_objectids({
        "campaigns": campaigns,
        "assets": assets,
        "user_info": {
            "username": current_user["username"],
            "email": current_user.get("email"),
            "full_name": current_user.get("full_name")
        }
    })

class StepRequest(BaseModel):
    id: str = None
    data: dict = None

@router.post("/upload-assets/{campaign_id}/{asset_type}")
async def upload_campaign_assets(campaign_id: str, asset_type: str, files: list[UploadFile] = File(...), current_user: dict = Depends(get_current_user)):
    """Upload product or logo assets for a specific campaign to GridFS."""
    if asset_type not in ["product", "logo"]:
        raise HTTPException(status_code=400, detail="Invalid asset type. Must be 'product' or 'logo'.")
    
    saved_file_ids = []
    for file in files:
        content = await file.read()
        file_id = await upload_file_to_gridfs(
            filename=file.filename,
            content=content,
            metadata={
                "campaign_id": campaign_id,
                "asset_type": asset_type,
                "content_type": file.content_type,
                "user_id": str(current_user["_id"])
            }
        )
        saved_file_ids.append(file_id)
        
    return {
        "message": f"Successfully uploaded {len(saved_file_ids)} {asset_type} assets to GridFS.",
        "file_ids": saved_file_ids,
        "urls": [f"/files/{fid}" for fid in saved_file_ids]
    }

@router.post("/step/discover")
async def run_step_discover(req: StepRequest, current_user: dict = Depends(get_current_user)):
    """Phase 1: Discovery"""
    from agents.graph import research_graph
    
    # Generate a temporary ID for discovery phase
    campaign_id = req.data.get("campaign_id") or f"discovery_{datetime.now().timestamp()}"
    
    state_in = {"product_input": req.data, "scrape_enabled": False}
    # LangGraph invoke with thread_id for memory
    config = {"configurable": {"thread_id": campaign_id}}
    state_out = research_graph.invoke(state_in, config)
    
    results = {
        "understanding": state_out.get("product_understanding", {}),
        "brands": state_out.get("curated_brands", [])
    }
    results["user_id"] = str(current_user["_id"])
    return {"results": results}

@router.post("/step/research")
async def run_step_research(req: StepRequest, current_user: dict = Depends(get_current_user)):
    """Phase 2: Research"""
    user_id = str(current_user["_id"])
    from agents.graph import research_graph
    
    # The frontend creates campaign_id in wizard later, but we need it here if possible.
    # We'll use product_input campaign_id if it exists, else generate one.
    campaign_id = req.data.get("campaign_id") or f"research_{datetime.now().timestamp()}"
    
    state_in = {
        "product_input": req.data["product"],
        "curated_brands": req.data["curated_brands"],
        "scrape_enabled": True
    }
    config = {"configurable": {"thread_id": campaign_id}}
    state_out = research_graph.invoke(state_in, config)
    results = state_out.get("competitor_results", [])
    
    # Save to MongoDB
    product_data = req.data["product"]
    product_data["user_id"] = user_id
    product_id = await save_document("products", product_data)
    
    research_data = {"product_id": product_id, "results": results, "user_id": user_id}
    research_id = await save_document("research", research_data)
    return {"product_id": product_id, "research_id": research_id, "results": results}

@router.post("/step/psychology")
async def run_step_psychology(req: StepRequest, current_user: dict = Depends(get_current_user)):
    """Step 2 & 4: Psychology & Patterns"""
    try:
        user_id = str(current_user["_id"])
        # req.data should contain founder_data and competitor_results and understanding
        understanding = req.data.get("understanding", {})
        
        from agents.graph import strategy_graph
        state_in = {
            "founder_input": req.data["founder_data"],
            "competitor_results": req.data["competitor_results"],
            "product_understanding": understanding,
        }
        
        # We need the real campaign_id for downstream persistence
        campaign_req_id = req.data.get("founder_data", {}).get("campaign_id", f"camp_{int(datetime.now().timestamp())}")
        config = {"configurable": {"thread_id": campaign_req_id}}
        
        state_out = strategy_graph.invoke(state_in, config)
        results = {
            "campaign_psychology": state_out.get("campaign_psychology", {}),
            "pattern_blueprint": state_out.get("pattern_blueprint", {}),
        }
        
        # Add metadata for history view - use understanding for accurate names
        results["product_name"] = understanding.get("product_name") or req.data["founder_data"].get("product_name", "Unknown Product")
        results["brand_name"] = understanding.get("brand_name") or req.data["founder_data"].get("brand_name", "Unknown Brand")
        results["platform"] = req.data["founder_data"].get("platform", "Unknown")
        results["funnel_stage"] = req.data["founder_data"].get("funnel_stage", "cold")
        results["primary_emotions"] = req.data["founder_data"].get("primary_emotions", [])
        results["timestamp"] = datetime.now().isoformat()
        results["user_id"] = user_id
        
        campaign_id = await save_document("campaigns", results)
        # CRITICAL: Inject campaign_id into the results for downstream steps
        results["campaign_id"] = campaign_id
        
        return clean_objectids({"campaign_id": campaign_id, "results": results})
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Psychology endpoint crash: {e}")
        raise HTTPException(status_code=500, detail=f"Internal processing error: {str(e)}")

@router.post("/step/script")
async def run_step_script(req: StepRequest, current_user: dict = Depends(get_current_user)):
    """Step 5: Script"""
    user_id = str(current_user["_id"])
    
    from agents.graph import creative_graph
    
    campaign_req_id = req.data.get("campaign_psychology", {}).get("campaign_id", f"camp_{int(datetime.now().timestamp())}")
    
    state_in = {
        "pattern_blueprint": req.data["pattern_blueprint"],
        "campaign_psychology": req.data["campaign_psychology"],
        "language": req.data.get("language", "English")
    }
    config = {"configurable": {"thread_id": campaign_req_id}}
    state_out = creative_graph.invoke(state_in, config)
    results = state_out.get("script_output", {})
    
    script_data = {"content": results, "user_id": user_id}
    script_id = await save_document("scripts", script_data)
    return {"script_id": script_id, "results": results}

@router.post("/step/avatar/generate")
async def run_step_avatar_generate(req: StepRequest, current_user: dict = Depends(get_current_user)):
    """Step 6: AI Avatar Generation"""
    from agents.creative.avatar_selector import AvatarSelector
    selector = AvatarSelector()
    results = selector.select_avatars(
        req.data["gender"],
        req.data["style"],
        req.data.get("custom_prompt")
    )
    return {"results": results}

@router.post("/step/render")
async def run_step_render(req: StepRequest, current_user: dict = Depends(get_current_user)):
    """Step 7: Render"""
    try:
        user_id = str(current_user["_id"])
        
        from agents.graph import production_graph
        
        campaign_req_id = req.data.get("campaign_psychology", {}).get("campaign_id", f"camp_{int(datetime.now().timestamp())}")
        
        state_in = {
            "script_output": req.data["script_output"],
            "avatar_config": req.data["avatar_config"],
            "campaign_psychology": req.data["campaign_psychology"],
            "campaign_id": campaign_req_id
        }
        config = {"configurable": {"thread_id": campaign_req_id}}
        state_out = production_graph.invoke(state_in, config)
        results = {
            "variants_output": state_out.get("variants_output", {}),
            "render_results": state_out.get("render_results", []),
        }
        
        results["user_id"] = user_id
        asset_id = await save_document("assets", results)

        # Update the campaign history with the final storyboard and avatar config
        campaign_id = req.data.get("campaign_psychology", {}).get("campaign_id")
        if campaign_id:
            campaign = await get_document("campaigns", campaign_id)
            if campaign:
                campaign["final_storyboard"] = req.data["script_output"]
                campaign["avatar_config"] = req.data["avatar_config"]
                campaign["asset_id"] = asset_id
                campaign["user_id"] = user_id
                if "render_results" in results and results["render_results"]:
                    first_variant = results["render_results"][0]
                    if "local_path" in first_variant:
                        filename = os.path.basename(first_variant['local_path'])
                        campaign["video_url"] = f"http://localhost:8000/videos/{filename}"
                await save_document("campaigns", campaign)

        return clean_objectids({"asset_id": asset_id, "results": results})
    except Exception as e:
        import traceback
        with open("render_error.txt", "w") as f:
            f.write(traceback.format_exc())
        print(f"Render endpoint crash: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Render error: {str(e)}")


# ── Video Feedback ──────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    rating: int  # 1-5 stars
    feedback_text: str = ""
    campaign_id: str = ""
    video_url: str = ""


@router.post("/feedback")
async def submit_feedback(req: FeedbackRequest, current_user: dict = Depends(get_current_user)):
    """Submit feedback for a generated video ad. Stored in MongoDB for future learning."""
    from api.services.db_mongo_service import save_feedback

    feedback_data = {
        "user_id": str(current_user["_id"]),
        "username": current_user.get("username", ""),
        "rating": max(1, min(5, req.rating)),
        "feedback_text": req.feedback_text,
        "campaign_id": req.campaign_id,
        "video_url": req.video_url,
        "created_at": datetime.utcnow().isoformat(),
    }

    feedback_id = await save_feedback(feedback_data)
    print(f"   📝 Feedback saved: rating={req.rating}, id={feedback_id}")
    return {"status": "ok", "feedback_id": feedback_id}


@router.get("/feedback")
async def get_feedback(current_user: dict = Depends(get_current_user)):
    """Retrieve feedback history."""
    from api.services.db_mongo_service import get_all_feedback

    feedback_list = await get_all_feedback(limit=50)
    return {"feedback": feedback_list}
