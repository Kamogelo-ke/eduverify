"""
Security utilities:
  - AES-256-GCM encryption / decryption for biometric embeddings
  - bcrypt password hashing (native bcrypt — no passlib)
  - JWT access + refresh token creation and decoding
"""

import base64
import json
import os
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from jose import jwt

from core.config import settings


# ── AES-256-GCM biometric encryption ─────────────────────────────────────────

def _get_aes_key() -> bytes:
    key = base64.b64decode(settings.BIOMETRIC_ENCRYPTION_KEY)
    if len(key) != 32:
        raise ValueError("BIOMETRIC_ENCRYPTION_KEY must decode to exactly 32 bytes")
    return key


def encrypt_embedding(embedding: list[float]) -> str:
    """
    Encrypt a 512-dim ArcFace embedding with AES-256-GCM.
    Returns base64(nonce[12] + ciphertext + tag[16]).
    The raw vector is never stored — only this ciphertext.
    """
    key = _get_aes_key()
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    plaintext = json.dumps(embedding).encode()
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    return base64.b64encode(nonce + ciphertext).decode()


def decrypt_embedding(encrypted: str) -> list[float]:
    """Decrypt and return the float embedding vector."""
    key = _get_aes_key()
    raw = base64.b64decode(encrypted)
    nonce, ciphertext = raw[:12], raw[12:]
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return json.loads(plaintext)


# ── Password hashing ──────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash a password using native bcrypt."""
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    return bcrypt.checkpw(
        plain.encode("utf-8"),
        hashed.encode("utf-8"),
    )


# ── JWT tokens ────────────────────────────────────────────────────────────────

def create_access_token(subject: str, role: str,
                        expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {"sub": subject, "role": role, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": subject, "role": role, "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    """Raises jose.JWTError on invalid or expired tokens."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


# ── Temporary password generation ─────────────────────────────────────────────

import secrets
import string

def generate_temp_password(length: int = 12) -> str:
    """
    Generate a secure temporary password containing at least one
    uppercase letter, one lowercase letter, one digit and one
    special character — satisfies most password policy requirements.
    """
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        # Enforce complexity rules
        if (
            any(c.isupper() for c in password)
            and any(c.islower() for c in password)
            and any(c.isdigit() for c in password)
            and any(c in "!@#$%" for c in password)
        ):
            return password