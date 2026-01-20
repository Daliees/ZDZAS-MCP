"""Authentication utilities for admin dashboard."""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from jose import JWTError, jwt

logger = logging.getLogger(__name__)

# Simple authentication config
SECRET_KEY = "zas-admin-dashboard-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

# Default admin credentials (SHA256 hashed)
# admin:admin = 8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918
# ryan:ryan123 = 5090a56c78719e08107bb37aa776f30b25b842234afad59401ecd422ba63db75
ADMIN_USERS = {
    "admin": "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918",
    "ryan": "5090a56c78719e08107bb37aa776f30b25b842234afad59401ecd422ba63db75",
}

security = HTTPBasic()


def hash_password(password: str) -> str:
    """Hash a password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return hash_password(plain_password) == hashed_password


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(username: str, password: str) -> Optional[str]:
    """Authenticate a user and return username if valid."""
    if username not in ADMIN_USERS:
        return None
    hashed_password = ADMIN_USERS[username]
    if not verify_password(password, hashed_password):
        return None
    return username


async def get_current_user(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """Dependency to get current authenticated user."""
    username = authenticate_user(credentials.username, credentials.password)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return username
