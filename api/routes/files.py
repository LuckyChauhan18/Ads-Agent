from fastapi import APIRouter, HTTPException, Response, Depends
from api.services.db_mongo_service import get_file_from_gridfs
from api.auth_utils import get_current_user
import mimetypes

router = APIRouter(prefix="/files", tags=["Files"])

# --- FIX D1: Unauthenticated File Serving ---
# Previously this endpoint had NO authentication — anyone who knew or guessed
# a file ID could download any user's uploaded images or logos.
# Now it:
#   1. Requires a valid JWT token (Depends(get_current_user))
#   2. Checks that the file's owner matches the requesting user
@router.get("/{file_id}")
async def serve_file(file_id: str, current_user: dict = Depends(get_current_user)):
    """Serves a file from GridFS by its ID. Requires authentication and ownership."""
    try:
        content, metadata = await get_file_from_gridfs(file_id)

        # Ownership check: only serve the file if it belongs to the requesting user
        file_owner = metadata.get("user_id")
        if file_owner and str(file_owner) != str(current_user["_id"]):
            # Return 403 Forbidden — don't reveal the file exists to other users
            raise HTTPException(status_code=403, detail="Access denied")

        # Determine content type from metadata, fallback to filename extension
        content_type = metadata.get("content_type")
        if not content_type:
            filename = metadata.get("filename", "")
            content_type, _ = mimetypes.guess_type(filename)
        if not content_type:
            content_type = "application/octet-stream"

        return Response(content=content, media_type=content_type)
    except HTTPException:
        raise  # Re-raise HTTP exceptions (auth errors, 403, etc.) as-is
    except Exception as e:
        print(f"Error serving file {file_id}: {e}")
        raise HTTPException(status_code=404, detail="File not found")

