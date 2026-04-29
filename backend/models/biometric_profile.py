import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey,
    Integer, String, Text, TypeDecorator, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class BiometricProfile(Base):
    """
    Stores the AES-256-GCM encrypted ArcFace embedding.
    The raw image is NEVER persisted — only the ciphertext.
    """
    __tablename__ = "biometric_profiles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"),
        unique=True, nullable=False,
    )
    encrypted_embedding = Column(Text, nullable=False)
    embedding_model = Column(String(64), default="arcface-r100", nullable=False)
    face_quality_score = Column(Float, nullable=True)
    enrolled_by = Column(Integer, ForeignKey("system_users.id"), nullable=True)
    enrolled_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    last_updated = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    student = relationship("Student", back_populates="biometric_profile")
    enrolled_by_user = relationship("User", foreign_keys=[enrolled_by])