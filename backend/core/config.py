# core/config.py
from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # App
    APP_NAME: str = "EduVerify API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://user:pass@localhost/edverify"
    )
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "20"))
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # AES-256 key for biometric embeddings (32 bytes, base64-encoded)
    BIOMETRIC_ENCRYPTION_KEY: str = os.getenv(
        "BIOMETRIC_ENCRYPTION_KEY",
        "dGhpcy1pcy1hLTMyLWJ5dGUta2V5LWZvci1hZXMyNTY=",
    )

    # Face recognition thresholds
    FACE_SIMILARITY_THRESHOLD: float = float(os.getenv("FACE_SIMILARITY_THRESHOLD", "0.65"))
    LIVENESS_CONFIDENCE_THRESHOLD: float = float(os.getenv("LIVENESS_CONFIDENCE_THRESHOLD", "0.80"))

    # Performance
    MAX_VERIFICATION_TIME: float = 15.0
    MAX_IMAGE_SIZE_MB: int = int(os.getenv("MAX_IMAGE_SIZE_MB", "5"))

    # Email (SMTP)
    MAIL_USERNAME: str = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD", "")
    MAIL_FROM: str = os.getenv("MAIL_FROM", "")
    MAIL_SERVER: str = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", "587"))
    MAIL_ENABLED: bool = os.getenv("MAIL_USERNAME", "") != ""
    
    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-me")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_ENABLED: bool = True
    
    # SIS Integration
    SIS_API_URL: str = os.getenv("SIS_API_URL", "http://localhost:8080/api")
    SIS_API_KEY: str = os.getenv("SIS_API_KEY", "")
    SIS_TIMEOUT_SECONDS: int = 5
    
    # CORS
    # CORS_ORIGINS: List[str] = os.getenv(
    #     "CORS_ORIGINS", 
    #     "http://localhost:3000,http://localhost:8080"
    # ).split(",")
    
    # AI Models
    AI_MODELS_PATH: str = os.getenv("AI_MODELS_PATH", "./models")
    FACE_MATCH_THRESHOLD: float = 0.68
    LIVENESS_THRESHOLD: float = 0.75
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    AUDIT_LOG_RETENTION_DAYS: int = 90
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
