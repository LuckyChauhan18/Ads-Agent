import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from api.models.user import TokenData
from api.services.db_mongo_service import find_user_by_username

# Secret keys and algorithms
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "b3984d7f8d6f5e4c3b2a1a09876543210fedcba9876543210fedcba987654321") # Use a real secret in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 # 1 hour

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    print(f"🔑 [AUTH DEBUG] Token received: {token[:20] if token else 'NONE'}...")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        print(f"🔑 [AUTH DEBUG] Decoded username: {username}")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError as e:
        print(f"🔑 [AUTH DEBUG] JWT Error: {e}")
        raise credentials_exception
        
    user = await find_user_by_username(token_data.username)
    print(f"🔑 [AUTH DEBUG] User found in DB: {user is not None}")
    if user is None:
        raise credentials_exception
    return user

async def authenticate_user(username: str, password: str):
    user = await find_user_by_username(username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user
