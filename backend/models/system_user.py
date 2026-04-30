# models/system_user.py
import bcrypt
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, LargeBinary
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, relationship
import enum
from datetime import datetime
from database import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    INVIGILATOR = "invigilator"
    SYSTEM = "system"

class SystemUser(Base):
    __tablename__ = "system_users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    Username = Column(String(100), unique=True, nullable=False, index=True)
    Email = Column(String(255), unique=True, nullable=False, index=True)
    PasswordHash = Column(String(255), nullable=False)
    
    # User information
    FirstName = Column(String(100), nullable=False)
    LastName = Column(String(100), nullable=False)
    Role = Column(Enum(UserRole), default=UserRole.INVIGILATOR, nullable=False)
    
    # Authentication
    RefreshTokenHash = Column(String(255), nullable=True)
    IsActive = Column(Boolean, default=True, nullable=False)
    IsLocked = Column(Boolean, default=False)
    FailedLoginAttempts = Column(Integer, default=0)
    LastLoginAt = Column(DateTime, nullable=True)
    LastLoginIP = Column(String(45), nullable=True)  # IPv6 compatible
    
    # 2FA (optional for compliance)
    TwoFactorEnabled = Column(Boolean, default=False)
    TwoFactorSecret = Column(String(255), nullable=True)
    
    # Audit
    CreatedAt = Column(DateTime, server_default=func.now())
    UpdatedAt = Column(DateTime, onupdate=func.now())
    CreatedBy = Column(Integer, nullable=True)  # id who created this user
    
    # Relationships
    # access_logs : Mapped["AccessLog"]= relationship("AccessLog", back_populates="user")
    # created_sessions : Mapped["ExamSession"] = relationship("ExamSession", foreign_keys="ExamSession.CreatedBy")
    
    attempts_overridden = relationship(
    "VerificationAttempt",
    back_populates="overriding_user",
    foreign_keys="VerificationAttempt.overridden_by",
    )
    def verify_password(self, password: str) -> bool:
        """Verify user password"""
        return bcrypt.checkpw(password.encode("utf-8")[:72], self.PasswordHash.encode("utf-8"))
    
    def set_password(self, password: str):
        """Hash and set password using bcrypt"""
        # Truncate password to 72 bytes (bcrypt limitation)
        password_bytes = password.encode('utf-8')[:72]
        salt = bcrypt.gensalt()
        self.PasswordHash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
    
    def set_refresh_token(self, refresh_token: str):
        """Hash and set refresh token"""
        token_bytes = refresh_token.encode("utf-8")[:72]
        self.RefreshTokenHash = bcrypt.hashpw(token_bytes, bcrypt.gensalt()).decode("utf-8")

    def verify_refresh_token(self, refresh_token: str) -> bool:
        """Verify refresh token"""
        if not self.RefreshTokenHash:
            return False
        return bcrypt.checkpw(refresh_token.encode("utf-8")[:72], self.RefreshTokenHash.encode("utf-8"))
    
    def increment_failed_attempts(self):
        """Increment failed login attempts and lock if exceeded"""
        self.FailedLoginAttempts += 1
        if self.FailedLoginAttempts >= 5:
            self.IsLocked = True
    
    def reset_failed_attempts(self):
        """Reset failed login attempts"""
        self.FailedLoginAttempts = 0
        self.IsLocked = False
    
    @property
    def FullName(self) -> str:
        return f"{self.FirstName} {self.LastName}"
    
    def has_permission(self, required_role: UserRole) -> bool:
        """Check if user has required role permission"""
        if self.Role == UserRole.ADMIN:
            return True  # Admin has all permissions
        if self.Role == UserRole.SYSTEM:
            return required_role in [UserRole.SYSTEM, UserRole.INVIGILATOR]
        return self.Role == required_role
    
    def __repr__(self):
        return f"<SystemUser {self.Username} ({self.Role.value})>"
