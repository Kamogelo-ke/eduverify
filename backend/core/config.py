"""
Application settings loaded from environment variables / .env file.
All modules import `settings` from here — never read os.environ directly.
"""

import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # App
    APP_NAME: str = "EduVerify"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

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


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()