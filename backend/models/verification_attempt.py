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


class VerificationOutcome(str, enum.Enum):
    granted = "granted"
    denied_identity = "denied_identity"
    denied_eligibility = "denied_eligibility"
    denied_liveness = "denied_liveness"
    overridden = "overridden"
    error = "error"


class VerificationAttempt(Base):
    """
    Immutable audit record of every face verification attempt.
    Written once; never updated (forensic integrity).
    """
    __tablename__ = "verification_attempts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    exam_session_id = Column(Integer, ForeignKey("exam_sessions.id"), nullable=True)

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
    overridden_by = Column(Integer, ForeignKey("system_users.id"), nullable=True)
    override_reason = Column(String(500), nullable=True)
    overridden_at = Column(DateTime(timezone=True), nullable=True)

    # Context
    terminal_id = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    attempted_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    student = relationship("Student", back_populates="verification_attempts")
    exam_session = relationship("ExamSession", back_populates="attempts")
    overriding_user = relationship(
        "SystemUser",
        back_populates="attempts_overridden",
        foreign_keys=[overridden_by],
    )