# api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt

from database import get_db
from core.config import settings
from core.dependencies import get_current_user, require_role
from schemas.auth import (
    LoginRequest, 
    LoginResponse, 
    RefreshTokenRequest,
    RefreshTokenResponse,
    LogoutResponse,
    UserInfoResponse,
    ChangePasswordRequest,
    PasswordResetRequest,
    PasswordResetConfirmRequest
)
from services.auth import AuthService
from models.system_user import SystemUser

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()

@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    request_obj: Request,
    db: AsyncSession = Depends(get_db)
) -> LoginResponse:
    """
    Authenticate user and return JWT tokens
    - username: Username or email
    - password: User password
    """
    service = AuthService(db)
    
    # Get client IP
    client_ip = request_obj.client.host if request_obj.client else None
    
    result = await service.authenticate_user(
        username=request.username,
        password=request.password,
        client_ip=client_ip
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["message"],
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return LoginResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserInfoResponse(
            user_id=result["user"].id,
            username=result["user"].Username,
            email=result["user"].Email,
            first_name=result["user"].FirstName,
            last_name=result["user"].LastName,
            role=result["user"].Role.value,
            is_active=result["user"].IsActive
        )
    )

# @router.post("/logout", response_model=LogoutResponse)
# async def logout(
#     current_user: SystemUser = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db)
# ) -> LogoutResponse:
#     """
#     Logout user by invalidating refresh token
#     """
#     service = AuthService(db)
#     await service.logout_user(current_user.id)
    
#     return LogoutResponse(
#         message="Successfully logged out",
#         user_id=current_user.id
#     )

# @router.post("/refresh-token", response_model=RefreshTokenResponse)
# async def refresh_token(
#     request: RefreshTokenRequest,
#     db: AsyncSession = Depends(get_db)
# ) -> RefreshTokenResponse:
#     """
#     Refresh access token using refresh token
#     """
#     service = AuthService(db)
#     result = await service.refresh_access_token(request.refresh_token)
    
#     if not result["success"]:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail=result["message"],
#             headers={"WWW-Authenticate": "Bearer"}
#         )
    
#     return RefreshTokenResponse(
#         access_token=result["access_token"],
#         token_type="bearer",
#         expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
#     )

# @router.get("/me", response_model=UserInfoResponse)
# async def get_current_user_info(
#     current_user: SystemUser = Depends(get_current_user)
# ) -> UserInfoResponse:
#     """
#     Get current authenticated user information
#     """
#     return UserInfoResponse(
#         user_id=current_user.id,
#         username=current_user.Username,
#         email=current_user.Email,
#         first_name=current_user.FirstName,
#         last_name=current_user.LastName,
#         role=current_user.Role.value,
#         is_active=current_user.IsActive,
#         last_login=current_user.LastLoginAt,
#         permissions=_get_user_permissions(current_user.Role.value)
#     )

# @router.post("/change-password")
# async def change_password(
#     request: ChangePasswordRequest,
#     current_user: SystemUser = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db)
# ) -> Dict[str, str]:
#     """
#     Change user password (requires current password)
#     """
#     service = AuthService(db)
#     result = await service.change_password(
#         user_id=current_user.id,
#         current_password=request.current_password,
#         new_password=request.new_password
#     )
    
#     if not result["success"]:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=result["message"]
#         )
    
#     return {"message": "Password changed successfully"}

# @router.post("/forgot-password")
# async def forgot_password(
#     request: PasswordResetRequest,
#     db: AsyncSession = Depends(get_db)
# ) -> Dict[str, str]:
#     """
#     Request password reset (sends email with reset link)
#     """
#     service = AuthService(db)
#     result = await service.initiate_password_reset(request.email)
    
#     # Always return success even if email doesn't exist (security)
#     return {"message": "If email exists, reset instructions have been sent"}

# @router.post("/reset-password")
# async def reset_password(
#     request: PasswordResetConfirmRequest,
#     db: AsyncSession = Depends(get_db)
# ) -> Dict[str, str]:
#     """
#     Confirm password reset with token
#     """
#     service = AuthService(db)
#     result = await service.confirm_password_reset(
#         token=request.token,
#         new_password=request.new_password
#     )
    
#     if not result["success"]:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=result["message"]
#         )
    
#     return {"message": "Password reset successfully"}

# @router.post("/verify-2fa")
# async def verify_2fa(
#     request: dict,
#     current_user: SystemUser = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db)
# ) -> Dict[str, Any]:
#     """
#     Verify 2FA code (if enabled)
#     """
#     service = AuthService(db)
#     result = await service.verify_2fa(
#         user_id=current_user.id,
#         code=request.get("code")
#     )
    
#     if not result["success"]:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail=result["message"]
#         )
    
#     return {
#         "verified": True,
#         "message": "2FA verification successful"
#     }

# def _get_user_permissions(role: str) -> list:
#     """Get permissions based on user role"""
#     permissions = {
#         "admin": [
#             "view_dashboard",
#             "manage_users",
#             "manage_students",
#             "manage_exams",
#             "view_reports",
#             "export_logs",
#             "manage_venues",
#             "view_audit_logs",
#             "system_settings"
#         ],
#         "invigilator": [
#             "view_session",
#             "grant_access",
#             "deny_access",
#             "manual_override",
#             "view_student",
#             "view_attendance",
#             "mark_attendance"
#         ],
#         "system": [
#             "health_check",
#             "sync_cache",
#             "view_metrics",
#             "system_logs"
#         ]
#     }
#     return permissions.get(role, [])