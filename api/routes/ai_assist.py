from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import List, Optional
from api.services.ai_assist_service import AIAssistService
from api.auth_utils import get_current_user
from api.services.db_mongo_service import upload_file_to_gridfs, get_file_from_gridfs
import io
import os
import time

router = APIRouter(prefix="/ai-assist", tags=["AI Assist"])
ai_service = AIAssistService()

@router.post("/generate-description")
async def generate_description(
    files: Optional[List[UploadFile]] = File(None),
    file_ids: Optional[str] = Form(None), # Comma separated IDs
    brand_name: Optional[str] = Form(None),
    product_name: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """Generates a product description by analyzing uploaded images and/or GridFS assets."""
    try:
        image_bytes = []
        
        print(f"DEBUG /generate-description: files={files}, file_ids={file_ids}")
        # Handle uploaded files
        if files:
            for file in files:
                content = await file.read()
                print(f"DEBUG: Read file {file.filename}, length={len(content)}")
                if len(content) > 0:
                    image_bytes.append(content)
        
        # Handle existing file IDs from GridFS
        if file_ids:
            ids = [fid.strip() for fid in file_ids.split(",") if fid.strip()]
            for fid in ids:
                try:
                    content, _ = await get_file_from_gridfs(fid)
                    image_bytes.append(content)
                except Exception as e:
                    print(f"Error fetching GridFS file {fid}: {e}")

        if not image_bytes:
            print("DEBUG: image_bytes is empty, raising 400")
            raise HTTPException(status_code=400, detail="No images provided for analysis.")
            
        description = await ai_service.generate_product_description(
            image_bytes, 
            brand_name=brand_name, 
            product_name=product_name
        )
        return {"description": description}
    except HTTPException:
        # Re-raise HTTP exceptions to avoid wrapping them in 500
        raise
    except Exception as e:
        import traceback
        with open("error_log.txt", "w") as f:
            f.write(traceback.format_exc())
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-avatar")
async def upload_avatar(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Uploads a manual avatar image to GridFS."""
    try:
        content = await file.read()
        file_id = await upload_file_to_gridfs(
            filename=file.filename,
            content=content,
            metadata={
                "type": "avatar", 
                "source": "manual_upload",
                "user_id": str(current_user["_id"]),
                "content_type": file.content_type
            }
        )
            
        return {
            "results": {
                "id": file_id,
                "url": f"/files/{file_id}",
                "style": "Manual Upload",
                "gender": "Unknown"
            }
        }
    except Exception as e:
        print(f"Upload Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/suggest-pain-points")
async def suggest_pain_points(
    product_name: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """Suggests structured pain points using Gemini AI analysis."""
    try:
        results = await ai_service.suggest_pain_points(
            product_name=product_name or "",
            category=category or "",
            description=description or ""
        )
        return {"results": results}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-generic")
async def upload_generic(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Uploads a generic file to GridFS to secure a durable link for UI caching."""
    try:
        content = await file.read()
        file_id = await upload_file_to_gridfs(
            filename=file.filename,
            content=content,
            metadata={
                "type": "generic_upload", 
                "user_id": str(current_user["_id"]),
                "content_type": file.content_type
            }
        )
            
        return {
            "results": {
                "id": file_id,
                "url": f"/files/{file_id}"
            }
        }
    except Exception as e:
        print(f"Generic Upload Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
