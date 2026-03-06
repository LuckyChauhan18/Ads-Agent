import os
import json
from fastapi import APIRouter, HTTPException
from api.models.inputs import ProductInput, FounderInput, AvatarInput

router = APIRouter(prefix="/inputs", tags=["Inputs"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_DIR = os.path.join(BASE_DIR, "input")


def get_json_file(filename: str):
    path = os.path.join(INPUT_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"{filename} not found")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json_file(filename: str, data: dict):
    os.makedirs(INPUT_DIR, exist_ok=True)
    path = os.path.join(INPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

@router.get("/product")
def get_product_input():
    return get_json_file("product_input.json")

@router.put("/product")
def update_product_input(data: ProductInput):
    save_json_file("product_input.json", data.model_dump())
    return {"message": "Product input updated successfully"}

@router.get("/founder")
def get_founder_input():
    return get_json_file("founder_input.json")

@router.put("/founder")
def update_founder_input(data: FounderInput):
    save_json_file("founder_input.json", data.model_dump())
    return {"message": "Founder input updated successfully"}

@router.get("/avatar")
def get_avatar_input():
    return get_json_file("avatar_input.json")

@router.put("/avatar")
def update_avatar_input(data: AvatarInput):
    save_json_file("avatar_input.json", data.model_dump())
    return {"message": "Avatar input updated successfully"}
