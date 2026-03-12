from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from pydantic import BaseModel
from typing import Optional
from api.models.user import Token
from api.auth_utils import authenticate_user, create_access_token, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user
from api.services.db_mongo_service import find_user_by_username, create_user

router = APIRouter(prefix="/auth", tags=["Auth"])


class SignupRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    company_id: Optional[str] = None


@router.post("/signup")
async def signup(req: SignupRequest):
    existing_user = await find_user_by_username(req.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    if req.company_id:
        from api.services.db_mongo_service import mongo
        if mongo.db is not None:
            existing_company = await mongo.db.users.find_one({"company_id": req.company_id})
            if existing_company:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Company ID already registered"
                )

    hashed_password = get_password_hash(req.password)
    user_dict = {
        "username": req.username,
        "full_name": req.full_name,
        "company_id": req.company_id,
        "disabled": False,
        "hashed_password": hashed_password,
    }
    # Only store email if provided (avoids null duplicate key issues)
    if req.email:
        user_dict["email"] = req.email

    try:
        uid = await create_user(user_dict)
    except Exception as e:
        error_msg = str(e)
        if "duplicate key" in error_msg and "email" in error_msg:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
        elif "duplicate key" in error_msg:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Signup failed: {error_msg}")

    return {
        "username": req.username,
        "email": req.email,
        "full_name": req.full_name,
        "company_id": req.company_id,
        "id": uid,
    }


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    print(f"[LOGIN] Attempt for username: {form_data.username}")
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        # Check if user exists at all (to give better feedback)
        existing = await find_user_by_username(form_data.username)
        if existing:
            print(f"[LOGIN] User '{form_data.username}' exists but password mismatch")
        else:
            print(f"[LOGIN] User '{form_data.username}' not found in DB")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "username": current_user["username"],
        "email": current_user.get("email"),
        "full_name": current_user.get("full_name"),
        "company_id": current_user.get("company_id"),
        "id": str(current_user["_id"]),
    }
