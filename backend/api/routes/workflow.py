import os
import time
from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File, Depends
import traceback
import shutil
from api.services.pipeline_service import run_pipeline_background
from utils.logger import logger

router = APIRouter(prefix="/workflow", tags=["Workflow"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR = os.path.join(os.path.dirname(BASE_DIR), "extra", "output")
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
    
    return clean_objectids({
        "campaigns": campaigns,
        "assets": {"logos": [], "products": [], "avatars": []}, # Deprecated, keeping for backwards compatibility strictly
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
    """Upload product or logo assets for a specific campaign to Cloudflare R2 and link them to the Campaign Document."""
    import uuid
    from api.services.r2_service import upload_file_to_r2
    if asset_type not in ["product", "logo"]:
        raise HTTPException(status_code=400, detail="Invalid asset type. Must be 'product' or 'logo'.")
    
    saved_urls = []
    for file in files:
        content = await file.read()
        extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{campaign_id}/{asset_type}/{uuid.uuid4()}{extension}"
        
        url = await upload_file_to_r2(unique_filename, content, file.content_type)
        saved_urls.append(url)
        
    # Upsert to unified campaign document (create if not exists)
    campaign = await get_document("campaigns", campaign_id)
    if not campaign:
        campaign = {
            "_id": campaign_id,
            "campaign_id": campaign_id,
            "user_id": str(current_user["_id"]),
            "timestamp": datetime.now().isoformat()
        }
    
    if asset_type == "logo":
        campaign["product_logo"] = saved_urls[0] if saved_urls else None
    elif asset_type == "product":
        # Keep existing images and append new ones
        campaign["product_images"] = campaign.get("product_images", []) + saved_urls
        
    await save_document("campaigns", campaign)
        
    return {
        "message": f"Successfully uploaded {len(saved_urls)} {asset_type} assets to R2 and updated campaign.",
        "urls": saved_urls
    }

@router.post("/step/discover")
async def run_step_discover(req: StepRequest, current_user: dict = Depends(get_current_user)):
    """Phase 1: Discovery"""
    user_id = str(current_user["_id"])
    from agents.graph import research_graph
    
    # Generate a temporary ID for discovery phase
    campaign_id = req.data.get("campaign_id") or f"discovery_{datetime.now().timestamp()}"
    
    company_id = current_user.get("company_id") or "default_company"
    state_in = {
        "product_input": req.data,
        "scrape_enabled": False,
        "user_id": user_id,
        "company_id": company_id
    }

    # LangGraph invoke with thread_id for state tracking
    config = {"configurable": {"thread_id": campaign_id}}
    state_out = await research_graph.ainvoke(state_in, config)
    
    research_state = state_out.get("research", {})
    results = {
        "understanding": research_state.get("product_understanding", {}),
        "brands": research_state.get("curated_brands", []) or state_out.get("curated_brands", [])
    }
    results["user_id"] = user_id
    
    # NEW: Store initial discovery in the unified campaign document
    campaign = {
        "_id": campaign_id,
        "campaign_id": campaign_id,
        "user_id": user_id,
        "product_info": req.data,
        "discovery_results": results,
        "timestamp": datetime.now().isoformat()
    }
    await save_document("campaigns", campaign)
    
    return {"campaign_id": campaign_id, "results": results}

@router.post("/step/research")
async def run_step_research(req: StepRequest, current_user: dict = Depends(get_current_user)):
    """Phase 2: Research"""
    user_id = str(current_user["_id"])
    company_id = current_user.get("company_id") or "default_company"
    from agents.graph import research_graph
    
    # The frontend creates campaign_id in wizard later, but we need it here if possible.
    # We'll use product_input campaign_id if it exists, else generate one.
    campaign_id = req.data.get("campaign_id") or f"research_{datetime.now().timestamp()}"
    
    state_in = {
        "product_input": req.data["product"],
        "curated_brands": req.data["curated_brands"],
        "scrape_enabled": True,
        "user_id": user_id,
        "company_id": company_id
    }
    config = {"configurable": {"thread_id": campaign_id}}
    state_out = await research_graph.ainvoke(state_in, config)
    results = state_out.get("research", {}).get("competitor_results", [])
    
    # Save to unified campaigns document
    product_data = req.data["product"]
    
    campaign = await get_document("campaigns", campaign_id)
    if not campaign:
        campaign = {"_id": campaign_id, "campaign_id": campaign_id, "user_id": user_id}
        
    campaign["product_info"] = product_data
    campaign["research"] = {"results": results}
    campaign["curated_brands"] = req.data["curated_brands"]
    
    await save_document("campaigns", campaign)
    
    return {"campaign_id": campaign_id, "results": results}

@router.post("/step/psychology")
async def run_step_psychology(req: StepRequest, current_user: dict = Depends(get_current_user)):
    """Step 2 & 4: Psychology & Patterns"""
    try:
        user_id = str(current_user["_id"])
        company_id = current_user.get("company_id") or "default_company"
        # req.data should contain founder_data and competitor_results and understanding
        understanding = req.data.get("understanding", {})
        
        from agents.graph import strategy_graph
        state_in = {
            "founder_input": req.data["founder_data"],
            "research": {
                "competitor_results": req.data["competitor_results"],
                "product_understanding": understanding
            },
            "user_id": user_id,
            "company_id": company_id
        }

        # Langgraph Invoke Config
        campaign_req_id = req.data.get("founder_data", {}).get("campaign_id", f"camp_{int(datetime.now().timestamp())}")
        config = {"configurable": {"thread_id": campaign_req_id}}
        
        state_out = await strategy_graph.ainvoke(state_in, config)
        results = {
            "campaign_psychology": state_out.get("strategy", {}).get("campaign_psychology", {}),
            "pattern_blueprint": state_out.get("strategy", {}).get("pattern_blueprint", {}),
        }
        
        # Add metadata for history view - use understanding for accurate names
        results["product_name"] = understanding.get("product_name") or req.data["founder_data"].get("product_name", "Unknown Product")
        results["brand_name"] = understanding.get("brand_name") or req.data["founder_data"].get("brand_name", "Unknown Brand")
        results["platform"] = req.data["founder_data"].get("platform", "Unknown")
        results["ad_length"] = req.data["founder_data"].get("ad_length", 30)
        results["funnel_stage"] = req.data["founder_data"].get("funnel_stage", "cold")
        results["primary_emotions"] = req.data["founder_data"].get("primary_emotions", [])
        
        # Additional fields for Recreation
        results["category"] = req.data["founder_data"].get("category", "")
        results["root_product"] = req.data["founder_data"].get("root_product", "")
        results["price_range"] = req.data["founder_data"].get("price_range", "")
        results["product_url"] = req.data["founder_data"].get("product_url", "")
        results["description"] = req.data["founder_data"].get("description", "")
        results["features"] = req.data["founder_data"].get("features", [])
        
        # Save brands for recreation skip-logic
        results["curated_brands"] = [
            (comp.get("brand") if isinstance(comp, dict) else comp) 
            for comp in req.data.get("competitor_results", []) if comp
        ]
        
        results["timestamp"] = datetime.now().isoformat()
        results["user_id"] = user_id
        
        # Use the frontend's campaign_id if available so we don't lose the link to uploaded assets!
        frontend_cam_id = req.data["founder_data"].get("campaign_id")
        campaign_id = frontend_cam_id or f"camp_{int(datetime.now().timestamp())}"
        
        # Load existing campaign to merge
        campaign = await get_document("campaigns", campaign_id)
        if not campaign:
            campaign = {"_id": campaign_id, "campaign_id": campaign_id, "user_id": user_id}
            
        # Merge new psychology results
        campaign.update(results)
        campaign["_id"] = campaign_id # Ensure ID parity
        
        await save_document("campaigns", campaign)
        
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
        logger.error(f"❌ Psychology endpoint crash: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal processing error: {str(e)}")

@router.post("/step/script")
async def run_step_script(req: StepRequest, current_user: dict = Depends(get_current_user)):
    """Step 5: Script"""
    user_id = str(current_user["_id"])
    company_id = current_user.get("company_id") or "default_company"
    
    from agents.graph import creative_graph
    
    campaign_req_id = req.data.get("campaign_psychology", {}).get("campaign_id", f"camp_{int(datetime.now().timestamp())}")
    
    # Construct modular AdGenState for the production graph
    platform = req.data.get("platform") or req.data.get("campaign_psychology", {}).get("platform", "Instagram Reels")
    ad_length = req.data.get("ad_length") or req.data.get("campaign_psychology", {}).get("ad_length") or 30
    language = req.data.get("language", "English")

    state_in = {
        "strategy": {
            "pattern_blueprint": req.data["pattern_blueprint"],
            "campaign_psychology": req.data["campaign_psychology"]
        },
        "language": language,
        "platform": platform,
        "ad_length": ad_length,
        "creative": {
            "avatar_config": req.data.get("avatar_config", {})
        },
        "user_id": user_id,
        "company_id": company_id
    }


    config = {"configurable": {"thread_id": campaign_req_id}}
    state_out = await creative_graph.ainvoke(state_in, config)
    results = state_out.get("creative", {}).get("script_output", {})
    logger.info(f"📝 Script generation completed. Results keys: {list(results.keys()) if results else 'NONE'}")
    # Keep individual scripts for now but focus on campaign unification
    script_data = {"content": results, "user_id": user_id, "campaign_id": campaign_req_id}
    script_id = await save_document("scripts", script_data)

    # NEW: Sync results back to the campaign document if campaign_id is provided
    campaign_id = req.data.get("campaign_id") or req.data.get("campaign_psychology", {}).get("campaign_id")
    logger.debug(f"Syncing script results to campaign_id: {campaign_id}")
    if campaign_id:
        campaign = await get_document("campaigns", campaign_id)
        if not campaign:
            campaign = {"_id": campaign_id, "campaign_id": campaign_id, "user_id": user_id}
            
        logger.info(f"🔄 Syncing script data to Campaign: {campaign_id}")
        campaign["final_storyboard"] = results
        campaign["platform"] = state_in["platform"]
        campaign["ad_length"] = state_in["ad_length"]
        campaign["avatar_config"] = req.data.get("avatar_config", {})
        
        await save_document("campaigns", campaign)
        logger.info(f"✅ Campaign {campaign_id} synced with new script data.")
    else:
        logger.warning("⚠️ No campaign_id found to sync script data.")

    return {"script_id": script_id, "results": results}

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
        company_id = current_user.get("company_id") or "default_company"
        
        from agents.graph import production_graph
        
        campaign_req_id = req.data.get("campaign_psychology", {}).get("campaign_id", f"camp_{int(datetime.now().timestamp())}")
        
        # Construct modular AdGenState for the production graph
        state_in = {
            "creative": {
                "script_output": req.data["script_output"],
                "avatar_config": req.data["avatar_config"],
                "storyboard_output": req.data.get("storyboard_output") or req.data["script_output"]
            },
            "strategy": {
                "campaign_psychology": req.data["campaign_psychology"]
            },
            "campaign_id": campaign_req_id,
            "user_id": user_id,
            "company_id": company_id,
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
        logger.debug(f"Render step syncing to campaign_id: {campaign_id}")
        if campaign_id:
            campaign = await get_document("campaigns", campaign_id)
            if campaign:
                logger.info(f"🔄 Syncing render data to Campaign: {campaign_id}")
                campaign["final_storyboard"] = req.data["script_output"]
                campaign["avatar_config"] = req.data["avatar_config"]
                campaign["asset_id"] = asset_id
                campaign["user_id"] = user_id
                video_url = None
                if "render_results" in results and results["render_results"]:
                    first_variant = results["render_results"][0]
                    if "local_path" in first_variant and os.path.exists(first_variant['local_path']):
                        try:
                            from api.services.r2_service import upload_file_to_r2
                            import uuid
                            filename = os.path.basename(first_variant['local_path'])
                            r2_filename = f"renders/{campaign_id}/{uuid.uuid4()}_{filename}"
                            logger.info(f"📤 Uploading {filename} to R2 as {r2_filename}...")
                            
                            with open(first_variant['local_path'], 'rb') as f:
                                video_bytes = f.read()
                                
                            video_url = await upload_file_to_r2(r2_filename, video_bytes, "video/mp4")
                            logger.info(f"✅ Successfully uploaded video to R2 at {video_url}")
                        except Exception as e:
                            logger.error(f"❌ Error uploading video to R2: {e}")
                            filename = os.path.basename(first_variant['local_path'])
                            video_url = f"http://localhost:8000/videos/{filename}"
                            
                campaign["video_url"] = video_url # Set video_url here
                await save_document("campaigns", campaign)
                logger.info(f"✅ Campaign {campaign_id} synced with video render result.")
            else:
                logger.warning(f"⚠️ Campaign document NOT FOUND for {campaign_id}")

        return clean_objectids({"asset_id": asset_id, "results": results})
    except Exception as e:
        import traceback
        with open("render_error.txt", "w") as f:
            f.write(traceback.format_exc())
        logger.error(f"❌ Render endpoint crash: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Render error: {str(e)}")


# ── Video Feedback ──────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    rating: int  # 1-5 stars
    feedback_text: str = ""
    campaign_id: str = ""
    video_url: str = ""


@router.post("/feedback")
async def submit_feedback(req: FeedbackRequest, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    """Submit feedback for a generated video ad."""
    from api.services.db_mongo_service import save_feedback

    user_id = str(current_user["_id"])
    company_id = current_user.get("company_id") or "default_company"

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
    logger.info(f"📝 Feedback saved: rating={req.rating}, id={feedback_id}")

    # 2. Trigger LTM processing if rating is high or feedback is detailed
    if req.rating >= 4 or len(req.feedback_text) > 10:
        background_tasks.add_task(process_feedback_for_ltm, feedback_data)

    return {
        "status": "ok",
        "feedback_id": feedback_id
    }

async def process_feedback_for_ltm(feedback_data: dict):
    """Background task to structure feedback and update LTM."""
    try:
        from api.services.memory_service import process_structured_feedback
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        import json

        # Fetch campaign to get context
        campaign_id = feedback_data.get("campaign_id")
        campaign = await get_document("campaigns", campaign_id)
        if not campaign:
            return

        company_id = campaign.get("company_id") or "default_company"
        
        # 1. Use LLM to structure the feedback
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0,
        )

        system_prompt = """You are a feedback analyst. Structure the user's feedback into actionable 'learned preferences' for different agents.
Return a JSON with:
- "research_feedback": preferred competitors, niches, or data sources
- "strategy_feedback": psychological triggers, emotional tones, or angles
- "creative_feedback": script style, visual tropes, hook preferences
- "production_feedback": resolution, branding, or overlay preferences
- "confidence": 0-1 score based on how clear the preference is
"""

        prompt = f"""Campaign: {campaign.get('product_name')}
Feedback Rating: {feedback_data.get('rating')}/5
Feedback Text: "{feedback_data.get('feedback_text')}"

Extract learning preferences for the AI agents."""

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ])
        
        content = response.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        
        structured = json.loads(content)
        confidence = structured.pop("confidence", 0.5)

        # 2. Update LTM
        await process_structured_feedback(company_id, structured, confidence)
        logger.info(f"🧠 [LTM] Feedback processed for {company_id}")
    except Exception as e:
        logger.error(f"❌ [LTM] Feedback processing failed: {e}")


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
