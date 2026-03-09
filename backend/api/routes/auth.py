from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from api.models.user import User, UserInDB, Token
from api.auth_utils import authenticate_user, create_access_token, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES
from api.services.db_mongo_service import find_user_by_username, create_user
from typing import Optional

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/signup", response_model=User)
async def signup(user_data: User, password: str):
    # Check if user exists
    existing_user = await find_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if company_id is unique (if provided)
    if user_data.company_id:
        from api.services.db_mongo_service import mongo
        existing_company = await mongo.db.users.find_one({"company_id": user_data.company_id})
        if existing_company:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company ID already registered"
            )
    
    hashed_password = get_password_hash(password)
    user_dict = user_data.dict()
    user_dict["hashed_password"] = hashed_password
    
    uid = await create_user(user_dict)
    user_dict["_id"] = uid
    return user_dict

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
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
