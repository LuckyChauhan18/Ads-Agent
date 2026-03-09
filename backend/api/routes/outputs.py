import os
import json
from fastapi import APIRouter, HTTPException
from typing import List

router = APIRouter(prefix="/outputs", tags=["Outputs"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR = os.path.join(os.path.dirname(BASE_DIR), "extra", "output")


@router.get("/")
def list_outputs() -> List[str]:
    """List all JSON files available in the output directory."""
    if not os.path.exists(OUTPUT_DIR):
        return []
    files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".json")]
    return files

@router.get("/{filename}")
def get_output_file(filename: str):
    """Fetch the content of a specific output file."""
    if not filename.endswith(".json"):
        filename += ".json"
    
    path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Output file {filename} not found")
        
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            if not content.strip():
                return {}
            return json.loads(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading {filename}: {str(e)}")
