"""
FastAPI async dependencies for JWT authentication and role-based access control.

Usage in endpoints:
    current_user = Depends(get_current_user)
    admin_only   = Depends(require_admin)
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import decode_token
from database import get_db
from models.system_user import SystemUser, UserRole

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> SystemUser:
    token = credentials.credentials
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type — use an access token",
            )
        user_id: str = payload.get("sub")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    result = await db.execute(
        select(SystemUser).where(SystemUser.id == user_id, SystemUser.is_active == True)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


async def require_admin(
    current_user: SystemUser = Depends(get_current_user),
) -> SystemUser:
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def require_invigilator_or_admin(
    current_user: SystemUser = Depends(get_current_user),
) -> SystemUser:
    if current_user.role not in (UserRole.admin, UserRole.invigilator):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invigilator or admin access required",
        )
    return current_user