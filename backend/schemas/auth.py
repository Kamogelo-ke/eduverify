# schemas/auth.py
from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, List
from datetime import datetime

class LoginRequest(BaseModel):
    username: str = Field(..., description="Username or email")
    password: str = Field(..., min_length=6, description="User password")
    
    @validator('username')
    def username_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Username cannot be empty')
        return v.strip()

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserInfoResponse"

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token")

class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class LogoutResponse(BaseModel):
    message: str
    user_id: int

class UserInfoResponse(BaseModel):
    user_id: int
    username: str
    email: str
    first_name: str
    last_name: str
    role: str
    is_active: bool
    last_login: Optional[datetime] = None
    permissions: Optional[List[str]] = []

class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('new_password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

# Update forward references
LoginResponse.model_rebuild()