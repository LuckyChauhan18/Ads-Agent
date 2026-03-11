import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from api.models.user import TokenData
from api.services.db_mongo_service import find_user_by_username

# --- FIX A1: JWT Secret Key ---
# REMOVED the hardcoded fallback secret. If JWT_SECRET_KEY is missing from .env,
# the app crashes on startup with a clear error instead of silently using a
# compromised key that anyone reading the source code could exploit.
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "FATAL: JWT_SECRET_KEY is not set in your .env file. "
        "Please generate a secure random key and add it to your .env before starting the app."
    )

ALGORITHM = "HS256"
# Token expires in 24 hours (reduced from 1 week — shorter window limits stolen token damage)
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode("utf-8")[:72], hashed_password.encode("utf-8"))

def get_password_hash(password):
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")

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
    # --- FIX A4 (bonus): Removed 4 debug print() calls that ran on EVERY request ---
    # They were logging partial JWT values and usernames to stdout, which leaks
    # sensitive data into any log aggregation / monitoring system.
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        # Don't log the JWTError detail — it can leak token format information
        raise credentials_exception

    user = await find_user_by_username(token_data.username)
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
