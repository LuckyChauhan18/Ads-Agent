import re
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from pydantic import BaseModel, validator, EmailStr
from typing import Optional
from api.models.user import Token
from api.auth_utils import authenticate_user, create_access_token, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user
from api.services.db_mongo_service import find_user_by_username, find_user_by_email, create_user

router = APIRouter(prefix="/auth", tags=["Auth"])


class SignupRequest(BaseModel):
    username: str
    password: str
    email: Optional[EmailStr] = None   # EmailStr auto-validates email format
    full_name: Optional[str] = None
    company_id: Optional[str] = None

    # --- VALIDATION V1: Username format ---
    # Must be 3–30 characters, only letters/numbers/underscores.
    # Prevents usernames like "", "  ", "<script>", etc.
    @validator("username")
    def username_valid(cls, v):
        v = v.strip()
        if not re.match(r"^[a-zA-Z0-9_]{3,30}$", v):
            raise ValueError(
                "Username must be 3–30 characters and contain only letters, numbers, or underscores"
            )
        return v

    # --- VALIDATION V2: Password strength ---
    # Minimum 6 characters. Prevents passwords like "a", "123", "".
    @validator("password")
    def password_strong(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        if len(v) > 128:
            raise ValueError("Password must be under 128 characters")
        return v

    # --- VALIDATION V3: Full name length guard ---
    @validator("full_name")
    def full_name_length(cls, v):
        if v and len(v.strip()) > 50:
            raise ValueError("Full name must be under 50 characters")
        return v.strip() if v else v


@router.post("/signup")
async def signup(req: SignupRequest):
    # --- CHECK 1: Username must not already exist ---
    existing_user = await find_user_by_username(req.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # --- CHECK 2: Email uniqueness ---
    # Without this check, a duplicate email causes an unhandled MongoDB
    # DuplicateKeyError that leaks internal error details to the frontend.
    if req.email:
        existing_email = await find_user_by_email(req.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    # --- CHECK 3: Company ID uniqueness ---
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
        "email": req.email,
        "full_name": req.full_name,
        "company_id": req.company_id,
        "disabled": False,
        "hashed_password": hashed_password,
    }

    uid = await create_user(user_dict)
    return {
        "message": "Account created successfully",
        "username": req.username,
        "email": req.email,
        "full_name": req.full_name,
        "company_id": req.company_id,
        "id": uid,
    }


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # --- VALIDATION: Reject obviously invalid inputs before hitting DB ---
    # Prevents long-string attacks and empty-string lookups.
    if not form_data.username or len(form_data.username.strip()) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid username"
        )
    if not form_data.password or len(form_data.password) > 128:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password"
        )

    user = await authenticate_user(form_data.username.strip(), form_data.password)
    if not user:
        # Use a generic message — don't reveal whether username or password was wrong
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


