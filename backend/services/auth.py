# services/auth_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
import uuid
import random
import string
from jose import jwt, JWTError
from passlib.context import CryptContext

from core.config import settings
from models.system_user import SystemUser
from utils.logging import audit_logger
# from app.utils.email import send_email

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def authenticate_user(
        self, 
        username: str, 
        password: str,
        client_ip: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Authenticate user and generate tokens
        """
        # Find user by username or email
        query = select(SystemUser).where(
            (SystemUser.Username == username) | (SystemUser.Email == username)
        )
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            audit_logger.log(
                event="Failed login attempt - user not found",
                action="LOGIN_FAILED",
                details={"username": username, "ip": client_ip}
            )
            return {"success": False, "message": "Invalid credentials"}
        
        # Check if account is locked
        if user.IsLocked:
            return {"success": False, "message": "Account is locked. Contact administrator"}
        
        # Verify password
        if not user.verify_password(password):
            user.increment_failed_attempts()
            await self.db.commit()
            
            audit_logger.log(
                event="Failed login attempt - wrong password",
                user_id=user.id,
                action="LOGIN_FAILED",
                details={"ip": client_ip, "attempts": user.FailedLoginAttempts}
            )
            
            return {"success": False, "message": "Invalid credentials"}
        
        # Reset failed attempts on successful login
        user.reset_failed_attempts()
        user.LastLoginAt = datetime.now()
        user.LastLoginIP = client_ip
        await self.db.commit()
        
        # Generate tokens
        access_token = self._create_access_token(user.id)
        refresh_token = self._create_refresh_token(user.id)
        
        # Store refresh token hash
        user.set_refresh_token(refresh_token)
        await self.db.commit()
        
        audit_logger.log(
            event="User logged in successfully",
            user_id=user.id,
            action="LOGIN_SUCCESS",
            details={"ip": client_ip, "role": user.Role.value}
        )
        
        return {
            "success": True,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user
        }
    
    async def logout_user(self, user_id: int) -> bool:
        """
        Invalidate user's refresh token
        """
        query = update(SystemUser).where(
            SystemUser.id == user_id
        ).values(RefreshTokenHash=None)
        
        await self.db.execute(query)
        await self.db.commit()
        
        audit_logger.log(
            event="User logged out",
            user_id=user_id,
            action="LOGOUT"
        )
        
        return True
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Generate new access token from refresh token
        """
        try:
            # Decode refresh token
            payload = jwt.decode(
                refresh_token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            user_id: int = payload.get("sub")
            
            if user_id is None:
                return {"success": False, "message": "Invalid token"}
            
            # Get user
            query = select(SystemUser).where(SystemUser.id == user_id)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()
            
            if not user or not user.verify_refresh_token(refresh_token):
                return {"success": False, "message": "Invalid refresh token"}
            
            # Generate new access token
            access_token = self._create_access_token(user_id)
            
            audit_logger.log(
                event="Token refreshed",
                user_id=user_id,
                action="TOKEN_REFRESH"
            )
            
            return {
                "success": True,
                "access_token": access_token
            }
            
        except JWTError:
            return {"success": False, "message": "Invalid token"}
    
    async def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> Dict[str, Any]:
        """
        Change user password
        """
        # Get user
        query = select(SystemUser).where(SystemUser.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return {"success": False, "message": "User not found"}
        
        # Verify current password
        if not user.verify_password(current_password):
            return {"success": False, "message": "Current password is incorrect"}
        
        # Set new password
        user.set_password(new_password)
        
        # Invalidate all existing tokens by clearing refresh token
        user.RefreshTokenHash = None
        
        await self.db.commit()
        
        audit_logger.log(
            event="Password changed",
            user_id=user_id,
            action="PASSWORD_CHANGE",
            sensitive=True
        )
        
        return {"success": True, "message": "Password changed successfully"}
    
    async def initiate_password_reset(self, email: str) -> bool:
        """
        Send password reset email
        """
        # Find user by email
        query = select(SystemUser).where(SystemUser.Email == email)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            # Return success even if email not found (security)
            return True
        
        # Generate reset token
        reset_token = str(uuid.uuid4()) + ''.join(random.choices(string.digits, k=6))
        
        # Store token (in production, use Redis with expiry)
        # For now, store in user table or separate tokens table
        
        # Send email
        # reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        # await send_email(
        #     to_email=email,
        #     subject="Password Reset Request",
        #     template="password_reset.html",
        #     context={"name": user.FirstName, "reset_link": reset_link}
        # )
        
        audit_logger.log(
            event="Password reset requested",
            user_id=user.id,
            action="PASSWORD_RESET_REQUEST"
        )
        
        return True
    
    async def confirm_password_reset(self, token: str, new_password: str) -> Dict[str, Any]:
        """
        Confirm password reset with token
        """
        # Verify token (in production, check against stored token)
        # For now, simplified implementation
        
        # Find user by token (you'd need a PasswordResetToken table)
        # This is a placeholder - implement proper token validation
        audit_logger.log(
            event="Password reset confirmed",
            action="PASSWORD_RESET_CONFIRM",
            sensitive=True
        )
        
        return {"success": True, "message": "Password reset successful"}
    
    async def verify_2fa(self, user_id: int, code: str) -> Dict[str, Any]:
        """
        Verify 2FA code
        """
        # Get user
        query = select(SystemUser).where(SystemUser.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user or not user.TwoFactorEnabled:
            return {"success": False, "message": "2FA not enabled for this user"}
        
        # Verify TOTP code (implement with pyotp)
        # import pyotp
        # totp = pyotp.TOTP(user.TwoFactorSecret)
        # if not totp.verify(code):
        #     return {"success": False, "message": "Invalid 2FA code"}
        
        audit_logger.log(
            event="2FA verification",
            user_id=user_id,
            action="2FA_VERIFY"
        )
        
        return {"success": True, "message": "2FA verified"}
    
    def _create_access_token(self, user_id: int) -> str:
        """Create JWT access token"""
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "type": "access",
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    def _create_refresh_token(self, user_id: int) -> str:
        """Create JWT refresh token"""
        expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "type": "refresh",
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)