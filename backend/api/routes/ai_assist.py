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
        
        # Handle existing file URLs
        if file_ids:
            import httpx
            urls = [fid.strip() for fid in file_ids.split(",") if fid.strip()]
            async with httpx.AsyncClient() as client:
                for url in urls:
                    try:
                        if url.startswith("http"):
                            resp = await client.get(url)
                            resp.raise_for_status()
                            image_bytes.append(resp.content)
                    except Exception as e:
                        print(f"Error fetching image {url}: {e}")

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
        log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "..", "extra", "error_log.txt")
        with open(log_path, "w") as f:
            f.write(traceback.format_exc())
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-avatar")
async def upload_avatar(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Uploads a manual avatar image to R2."""
    try:
        from api.services.r2_service import upload_file_to_r2
        import uuid
        content = await file.read()
        extension = os.path.splitext(file.filename)[1]
        unique_filename = f"avatars/{current_user['_id']}/{uuid.uuid4()}{extension}"
        
        url = await upload_file_to_r2(unique_filename, content, file.content_type)
            
        # Index in MongoDB so it shows up in history/gallery
        from api.services.db_mongo_service import mongo
        from bson import ObjectId
        if mongo.db is not None:
            await mongo.db.user_assets.insert_one({
                "user_id": current_user["_id"],
                "file_id": ObjectId(), # Generate a unique ID for this asset
                "filename": file.filename,
                "metadata": {
                    "asset_type": "avatar",
                    "type": "avatar",
                    "url": url,
                    "style": "Manual Upload",
                    "gender": "Unknown",
                    "storage": "r2"
                }
            })

        return {
            "results": {
                "id": unique_filename,
                "url": url,
                "style": "Manual Upload",
                "gender": "Unknown"
            }
        }
    except Exception as e:
        print(f"Upload Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
