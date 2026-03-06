from fastapi import APIRouter, HTTPException, Response
from api.services.db_mongo_service import get_file_from_gridfs
import mimetypes

router = APIRouter(prefix="/files", tags=["Files"])

@router.get("/{file_id}")
async def serve_file(file_id: str):
    """Serves a file from GridFS by its ID."""
    try:
        content, metadata = await get_file_from_gridfs(file_id)
        
        # Determine content type
        content_type = metadata.get("content_type")
        if not content_type:
            # Fallback to extension-based
            filename = metadata.get("filename", "")
            content_type, _ = mimetypes.guess_type(filename)
            
        if not content_type:
            content_type = "application/octet-stream"
            
        return Response(content=content, media_type=content_type)
    except Exception as e:
        print(f"Error serving file {file_id}: {e}")
        raise HTTPException(status_code=404, detail="File not found")
