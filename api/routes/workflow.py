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
        metadata = asset.get("metadata", {})
        asset_type = metadata.get("asset_type") or metadata.get("type")
        asset_id = str(asset["_id"])
        url = f"/files/{asset_id}"
        
        if asset_type == "logo":
            assets["logos"].append({"id": asset_id, "url": url, "filename": asset["filename"]})
        elif asset_type == "product":
            assets["products"].append({"id": asset_id, "url": url, "filename": asset["filename"]})
        elif asset_type == "avatar":
            # asset['file_id'] is an ObjectId from get_user_assets
            assets["avatars"].append({
                "id": asset_id, 
                "url": url, 
                "filename": asset["filename"], 
                "created_at": asset["file_id"].generation_time.isoformat() if hasattr(asset["file_id"], "generation_time") else None
            })

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

    # [LTM Disabled for Current Version]
    # company_id = current_user.get("company_id")
    # if company_id:
    #     from api.services.memory_service import get_company_memory
    #     memory = await get_company_memory(company_id)
    #     state_in["memory"] = memory
    #     state_in["company_id"] = company_id

    # LangGraph invoke with thread_id for memory
    config = {"configurable": {"thread_id": campaign_id}}
    state_out = await research_graph.ainvoke(state_in, config)
    
    research_state = state_out.get("research", {})
    results = {
        "understanding": research_state.get("product_understanding", {}),
        "brands": research_state.get("curated_brands", []) or state_out.get("curated_brands", [])
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
    state_out = await research_graph.ainvoke(state_in, config)
    results = state_out.get("research", {}).get("competitor_results", [])
    
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
            "research": {
                "competitor_results": req.data["competitor_results"],
                "product_understanding": understanding
            }
        }

        # [LTM Disabled for Current Version]
        # company_id = current_user.get("company_id")
        # if company_id:
        #     from api.services.memory_service import get_company_memory
        #     memory = await get_company_memory(company_id)
        #     state_in["memory"] = memory
        #     state_in["company_id"] = company_id

        campaign_req_id = req.data.get("founder_data", {}).get("campaign_id", f"camp_{int(datetime.now().timestamp())}")
        config = {"configurable": {"thread_id": campaign_req_id}}
        
        state_out = await strategy_graph.ainvoke(state_in, config)
        results = {
            "campaign_psychology": state_out.get("strategy", {}).get("campaign_psychology", {}),
            "pattern_blueprint": state_out.get("strategy", {}).get("pattern_blueprint", {}),
            "script_planning": state_out.get("strategy", {}).get("script_planning", {}),
        }
        
        # Add metadata for history view - use understanding for accurate names
        results["product_name"] = understanding.get("product_name") or req.data["founder_data"].get("product_name", "Unknown Product")
        results["brand_name"] = understanding.get("brand_name") or req.data["founder_data"].get("brand_name", "Unknown Brand")
        results["platform"] = req.data["founder_data"].get("platform", "Unknown")
        results["ad_length"] = req.data["founder_data"].get("ad_length", 30)
        results["funnel_stage"] = req.data["founder_data"].get("funnel_stage", "cold")
        results["primary_emotions"] = req.data["founder_data"].get("primary_emotions", [])
        results["timestamp"] = datetime.now().isoformat()
        results["user_id"] = user_id
        
        # Use the frontend's campaign_id if available so we don't lose the link to uploaded assets!
        frontend_cam_id = req.data["founder_data"].get("campaign_id")
        if frontend_cam_id:
            results["_id"] = frontend_cam_id
        
        campaign_id = await save_document("campaigns", results)
        
        # CRITICAL: Inject the REAL database campaign_id everywhere
        results["campaign_id"] = campaign_id
        if "campaign_psychology" in results:
             results["campaign_psychology"]["campaign_id"] = campaign_id
        if "pattern_blueprint" in results:
             results["pattern_blueprint"]["campaign_id"] = campaign_id
             if "pattern_blueprint" in results["pattern_blueprint"]:
                  results["pattern_blueprint"]["pattern_blueprint"]["campaign_id"] = campaign_id
        
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
        "strategy": {
            "pattern_blueprint": req.data["pattern_blueprint"],
            "campaign_psychology": req.data["campaign_psychology"],
            "script_planning": req.data.get("script_planning", {})
        },
        "language": req.data.get("language", "English"),
        "platform": req.data.get("platform") or req.data.get("campaign_psychology", {}).get("platform", "Instagram Reels"),
        "ad_length": req.data.get("ad_length") or req.data.get("campaign_psychology", {}).get("ad_length") or 30,
        "creative": {
            "avatar_config": req.data.get("avatar_config", {})
        }
    }

    # [LTM Disabled for Current Version]
    # company_id = current_user.get("company_id")
    # if company_id:
    #     from api.services.memory_service import get_company_memory
    #     memory = await get_company_memory(company_id)
    #     state_in["memory"] = memory
    #     state_in["company_id"] = company_id

    config = {"configurable": {"thread_id": campaign_req_id}}
    state_out = await creative_graph.ainvoke(state_in, config)
    
    # Extract ALL creative outputs
    creative_results = state_out.get("creative", {})
    script_output = creative_results.get("script_output", {})
    audio_planning = creative_results.get("audio_planning", {})
    
    # We also need the strategy planning state to preserve ad_type
    script_planning = state_out.get("strategy", {}).get("script_planning", {})
    
    print(f"DEBUG: run_step_script results keys: {list(script_output.keys()) if script_output else 'NONE'}")
    # Update individual script record
    script_data = {"content": script_output, "user_id": user_id}
    script_id = await save_document("scripts", script_data)

    # NEW: Sync results back to the campaign document if campaign_id is provided
    campaign_id = req.data.get("campaign_id") or req.data.get("campaign_psychology", {}).get("campaign_id")
    print(f"DEBUG: run_step_script syncing to campaign_id: {campaign_id}")
    if campaign_id:
        campaign = await get_document("campaigns", campaign_id)
        if campaign:
            print(f"DEBUG: found campaign document for {campaign_id}. Syncing storyboard...")
            campaign["final_storyboard"] = script_output
            campaign["audio_planning"] = audio_planning
            campaign["script_planning"] = script_planning
            campaign["platform"] = state_in["platform"]
            campaign["ad_length"] = state_in["ad_length"]
            await save_document("campaigns", campaign)
            print(f"   🔄 Campaign {campaign_id} synced with new script and audio data.")
        else:
            print(f"DEBUG: campaign document NOT FOUND for {campaign_id}")

    return {
        "script_id": script_id, 
        "results": script_output, 
        "audio_planning": audio_planning,
        "script_planning": script_planning
    }

@router.post("/step/avatar/generate")
async def run_step_avatar_generate(req: StepRequest, current_user: dict = Depends(get_current_user)):
    """Step 6: AI Avatar Generation"""
    from api.services.ai_assist_service import ai_assist_service
    results = await ai_assist_service.generate_avatars(
        req.data["gender"],
        req.data["style"],
        user_id=str(current_user["_id"]),
        custom_prompt=req.data.get("custom_prompt")
    )
    return {"results": results}

@router.post("/step/render")
async def run_step_render(req: StepRequest, current_user: dict = Depends(get_current_user)):
    """Step 7: Render"""
    try:
        user_id = str(current_user["_id"])
        
        from agents.graph import production_graph
        
        campaign_req_id = req.data.get("campaign_psychology", {}).get("campaign_id", f"camp_{int(datetime.now().timestamp())}")
        
        # Construct modular AdGenState for the production graph
        state_in = {
            "creative": {
                "script_output": req.data["script_output"],
                "avatar_config": req.data["avatar_config"],
                "storyboard_output": req.data.get("storyboard_output") or req.data["script_output"],
                "audio_planning": req.data.get("audio_planning", {})
            },
            "strategy": {
                "campaign_psychology": req.data["campaign_psychology"],
                "script_planning": req.data.get("script_planning", {})
            },
            "campaign_id": campaign_req_id,
            "user_id": user_id,
            "platform": req.data.get("platform") or req.data.get("campaign_psychology", {}).get("platform", "Instagram Reels"),
            "ad_length": req.data.get("ad_length") or req.data.get("campaign_psychology", {}).get("ad_length", 30)
        }
        
        # Inject user_id into campaign_psychology for asset loading in renderer
        state_in["strategy"]["campaign_psychology"]["user_id"] = user_id
        
        config = {"configurable": {"thread_id": campaign_req_id}}
        state_out = await production_graph.ainvoke(state_in, config)
        results = {
            "variants_output": state_out.get("production", {}).get("variants_output", {}),
            "render_results": state_out.get("production", {}).get("render_results", []),
        }
        
        results["user_id"] = user_id
        asset_id = await save_document("assets", results)

        # Update the campaign history with the final storyboard and avatar config
        campaign_id = req.data.get("campaign_id") or req.data.get("campaign_psychology", {}).get("campaign_id")
        print(f"DEBUG: run_step_render syncing to campaign_id: {campaign_id}")
        if campaign_id:
            campaign = await get_document("campaigns", campaign_id)
            if campaign:
                print(f"DEBUG: found campaign document for {campaign_id}. Syncing render data...")
                campaign["final_storyboard"] = req.data["script_output"]
                campaign["avatar_config"] = req.data["avatar_config"]
                campaign["asset_id"] = asset_id
                campaign["user_id"] = user_id
                video_url = None
                if "render_results" in results and results["render_results"]:
                    first_variant = results["render_results"][0]
                    if "local_path" in first_variant:
                        filename = os.path.basename(first_variant['local_path'])
                        video_url = f"http://localhost:8000/videos/{filename}"
                campaign["video_url"] = video_url # Set video_url here
                await save_document("campaigns", campaign)
                print(f"   🔄 Campaign {campaign_id} synced with video render result.")
            else:
                print(f"DEBUG: campaign document NOT FOUND for {campaign_id}")

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
    """Submit feedback for a generated video ad. Validates, structures, and learns from it."""
    from api.services.db_mongo_service import save_feedback
    from agents.shared.feedback_validator import FeedbackValidator
    # [LTM Disabled for Current Version]
    # from api.services.memory_service import (
    #     save_feedback_to_history,
    #     process_structured_feedback,
    # )

    user_id = str(current_user["_id"])
    company_id = current_user.get("company_id")

    feedback_data = {
        "user_id": user_id,
        "username": current_user.get("username", ""),
        "rating": max(1, min(5, req.rating)),
        "feedback_text": req.feedback_text,
        "campaign_id": req.campaign_id,
        "video_url": req.video_url,
        "created_at": datetime.utcnow().isoformat(),
    }

    # 1. Save raw feedback to main DB
    feedback_id = await save_feedback(feedback_data)
    print(f"   📝 Feedback saved: rating={req.rating}, id={feedback_id}")

    # [LTM Disabled for Current Version]
    # # 2. If company_id exists, run the two-stage evaluation pipeline
    # evaluation_result = None
    # if company_id and req.feedback_text.strip():
    #     # Save to LTM history
    #     await save_feedback_to_history(company_id, feedback_data)
    # 
    #     # Stage 1 + 2: Validate and extract
    #     validator = FeedbackValidator()
    #     evaluation_result = validator.evaluate(req.feedback_text)
    # 
    #     # 3. If valid, process structured feedback via memory service
    #     if evaluation_result.get("valid") and evaluation_result.get("structured_feedback"):
    #         memory_results = await process_structured_feedback(
    #             company_id=company_id,
    #             structured_feedback=evaluation_result["structured_feedback"],
    #             confidence=evaluation_result.get("confidence", 0.0),
    #         )
    #         evaluation_result["memory_results"] = memory_results
    #         print(f"   🧠 Memory processing complete for {company_id}")
    #     else:
    #         print(f"   ⛔ Feedback not valid or no structured feedback extracted.")

    return {
        "status": "ok",
        "feedback_id": feedback_id,
        "evaluation": evaluation_result,
    }


@router.get("/feedback")
async def get_feedback(current_user: dict = Depends(get_current_user)):
    """Retrieve feedback history."""
    from api.services.db_mongo_service import get_all_feedback

    feedback_list = await get_all_feedback(limit=50)
    return {"feedback": feedback_list}

@router.get("/avatars/history")
async def get_avatar_history(current_user: dict = Depends(get_current_user)):
    """Fetch unique avatars used in previous campaigns."""
    from api.services.db_mongo_service import get_user_avatar_history
    user_id = str(current_user["_id"])
    avatars = await get_user_avatar_history(user_id)
    return clean_objectids({"results": avatars})
