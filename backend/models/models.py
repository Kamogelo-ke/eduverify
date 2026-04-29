"""
SQLAlchemy ORM models for EduVerify.

All models inherit from the shared Base defined in database.py.
UUID columns use a cross-dialect TypeDecorator so the same code
works on both PostgreSQL (native UUID) and SQLite (tests).
"""

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


# ── Cross-dialect UUID type ───────────────────────────────────────────────────

class UUID(TypeDecorator):
    """
    Stores UUIDs as native PostgreSQL UUID on Postgres,
    and as VARCHAR(36) on SQLite (used in tests).
    """
    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return uuid.UUID(str(value))


# ── Enums ─────────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    admin = "admin"
    invigilator = "invigilator"
    system = "system"


class VerificationOutcome(str, enum.Enum):
    granted = "granted"
    denied_identity = "denied_identity"
    denied_eligibility = "denied_eligibility"
    denied_liveness = "denied_liveness"
    overridden = "overridden"
    error = "error"


class Gender(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"
    prefer_not_to_say = "prefer_not_to_say"


# ── ORM Tables ────────────────────────────────────────────────────────────────

class User(Base):
    """System users — admins and invigilators."""
    __tablename__ = "users"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.invigilator)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)

    attempts_overridden = relationship(
        "VerificationAttempt",
        back_populates="overriding_user",
        foreign_keys="VerificationAttempt.overridden_by",
    )


class Student(Base):
    """Registered students — academic identity + POPIA consent."""
    __tablename__ = "students"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    student_number = Column(String(20), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    programme = Column(String(255), nullable=True)
    year_of_study = Column(Integer, nullable=True)
    gender = Column(Enum(Gender), nullable=True)

    # POPIA: consent must be recorded before any biometric collection
    biometric_consent = Column(Boolean, default=False, nullable=False)
    consent_date = Column(DateTime(timezone=True), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    biometric_profile = relationship(
        "BiometricProfile",
        back_populates="student",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",   # async-safe eager load
    )
    verification_attempts = relationship(
        "VerificationAttempt",
        back_populates="student",
        lazy="selectin",
    )


class BiometricProfile(Base):
    """
    Stores the AES-256-GCM encrypted ArcFace embedding.
    The raw image is NEVER persisted — only the ciphertext.
    """
    __tablename__ = "biometric_profiles"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    student_id = Column(
        UUID(), ForeignKey("students.id", ondelete="CASCADE"),
        unique=True, nullable=False,
    )
    encrypted_embedding = Column(Text, nullable=False)
    embedding_model = Column(String(64), default="arcface-r100", nullable=False)
    face_quality_score = Column(Float, nullable=True)
    enrolled_by = Column(UUID(), ForeignKey("users.id"), nullable=True)
    enrolled_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    last_updated = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    student = relationship("Student", back_populates="biometric_profile")
    enrolled_by_user = relationship("User", foreign_keys=[enrolled_by])


class ExamSession(Base):
    """A single exam sitting at a specific venue and time."""
    __tablename__ = "exam_sessions"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    module_code = Column(String(20), nullable=False, index=True)
    module_name = Column(String(255), nullable=False)
    venue = Column(String(100), nullable=False)
    campus = Column(String(100), nullable=False, default="TUT Pretoria")
    scheduled_start = Column(DateTime(timezone=True), nullable=False)
    scheduled_end = Column(DateTime(timezone=True), nullable=False)
    created_by = Column(UUID(), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    attempts = relationship(
        "VerificationAttempt",
        back_populates="exam_session",
        lazy="selectin",
    )
    created_by_user = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        UniqueConstraint("module_code", "venue", "scheduled_start", name="uq_session_slot"),
    )


class VerificationAttempt(Base):
    """
    Immutable audit record of every face verification attempt.
    Written once; never updated (forensic integrity).
    """
    __tablename__ = "verification_attempts"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(), ForeignKey("students.id"), nullable=True)
    exam_session_id = Column(UUID(), ForeignKey("exam_sessions.id"), nullable=True)

    # AI pipeline scores
    face_similarity_score = Column(Float, nullable=True)
    liveness_score = Column(Float, nullable=True)
    face_detected = Column(Boolean, nullable=True)

    # SIS eligibility results
    sis_eligible = Column(Boolean, nullable=True)
    predicate_met = Column(Boolean, nullable=True)
    registered_for_exam = Column(Boolean, nullable=True)
    correct_venue = Column(Boolean, nullable=True)

    # Decision
    outcome = Column(Enum(VerificationOutcome), nullable=False)
    outcome_reason = Column(String(255), nullable=True)
    processing_time_ms = Column(Integer, nullable=True)

    # Manual override
    was_overridden = Column(Boolean, default=False, nullable=False)
    overridden_by = Column(UUID(), ForeignKey("users.id"), nullable=True)
    override_reason = Column(String(500), nullable=True)
    overridden_at = Column(DateTime(timezone=True), nullable=True)

    # Context
    terminal_id = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    attempted_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    student = relationship("Student", back_populates="verification_attempts")
    exam_session = relationship("ExamSession", back_populates="attempts")
    overriding_user = relationship(
        "User",
        back_populates="attempts_overridden",
        foreign_keys=[overridden_by],
    )