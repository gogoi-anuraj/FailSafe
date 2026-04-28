"""
FAILSAFE — Auth Routes
POST /auth/register  — create a new faculty account
POST /auth/login     — login and receive JWT token
GET  /auth/me        — get current logged-in user info
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db, User
from schemas  import RegisterRequest, LoginRequest, TokenResponse
from auth     import hash_password, verify_password, create_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new faculty account.
    Email must be unique.
    """
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail      = "An account with this email already exists."
        )

    user = User(
        name     = payload.name.strip(),
        email    = payload.email.lower().strip(),
        password = hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "Account created successfully.", "user_id": user.id}


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Login with email and password.
    Returns a JWT token valid for JWT_EXPIRE_MINUTES minutes.
    """
    user = db.query(User).filter(User.email == payload.email.lower()).first()

    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail      = "Incorrect email or password."
        )

    token = create_token({"sub": str(user.id)})

    return TokenResponse(
        access_token = token,
        user_name    = user.name,
        user_email   = user.email,
    )


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """Return current logged-in user info."""
    return {
        "id"        : current_user.id,
        "name"      : current_user.name,
        "email"     : current_user.email,
        "created_at": current_user.created_at,
    }
