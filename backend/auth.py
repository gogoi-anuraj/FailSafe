"""
FAILSAFE — Auth Utilities
JWT token creation and verification.
Password hashing with bcrypt directly (no passlib).
"""

from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from config import settings
from database import get_db, User


# ── Password hashing ──────────────────────────────────────────
# Using bcrypt directly — passlib has compatibility issues
# with bcrypt 4.x on Python 3.13

def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt      = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain.encode('utf-8'),
            hashed.encode('utf-8')
        )
    except Exception:
        return False


# ── JWT ───────────────────────────────────────────────────────
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def create_token(data: dict) -> str:
    payload       = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(
        minutes=settings.JWT_EXPIRE_MINUTES
    )
    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )


def get_current_user(
    token: str    = Depends(oauth2_scheme),
    db   : Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency — decodes JWT and returns the User object.
    Raises 401 if token is invalid or user not found.
    """
    credentials_exception = HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail      = "Invalid or expired token.",
        headers     = {"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: Optional[int] = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user
