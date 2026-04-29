"""
Authentication endpoints.

POST /auth/login          — email + password → JWT pair
POST /auth/refresh-token  — refresh token → new access token
POST /auth/logout         — client-side token discard (stateless)
GET  /auth/me             — current user profile
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import (
    create_access_token, create_refresh_token,
    decode_token, verify_password,
)
from database import get_db
from endpoints.deps import get_current_user
from models.models import User
from schemas.schemas import LoginRequest, RefreshRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate with email and password. Returns JWT access + refresh tokens."""
    result = await db.execute(
        select(User).where(User.email == body.email, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    user.last_login = datetime.now(timezone.utc)
    await db.commit()

    return TokenResponse(
        access_token=create_access_token(str(user.id), user.role.value),
        refresh_token=create_refresh_token(str(user.id), user.role.value),
        role=user.role.value,
    )


@router.post("/refresh-token", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a refresh token for a new access token."""
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type — use a refresh token",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    result = await db.execute(
        select(User).where(User.id == payload["sub"], User.is_active == True)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return TokenResponse(
        access_token=create_access_token(str(user.id), user.role.value),
        refresh_token=create_refresh_token(str(user.id), user.role.value),
        role=user.role.value,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(_: User = Depends(get_current_user)):
    """
    Stateless logout — the client discards the token.
    For production, add the token jti to a Redis deny-list.
    """
    return


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Return the profile of the currently authenticated user."""
    return current_user