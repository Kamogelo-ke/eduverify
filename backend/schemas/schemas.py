"""
Pydantic v2 schemas for request validation and API response serialisation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str


class RefreshRequest(BaseModel):
    refresh_token: str


# ── Student ───────────────────────────────────────────────────────────────────

class StudentCreate(BaseModel):
    student_number: str = Field(..., min_length=8, max_length=20)
    full_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    programme: Optional[str] = None
    year_of_study: Optional[int] = Field(None, ge=1, le=7)
    gender: Optional[str] = None
    biometric_consent: bool = False

    @field_validator("student_number")
    @classmethod
    def student_number_alphanumeric(cls, v: str) -> str:
        if not v.replace(" ", "").isalnum():
            raise ValueError("Student number must be alphanumeric")
        return v.upper()


class StudentUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    programme: Optional[str] = None
    year_of_study: Optional[int] = Field(None, ge=1, le=7)
    gender: Optional[str] = None
    is_active: Optional[bool] = None


class StudentResponse(BaseModel):
    id: UUID
    student_number: str
    full_name: str
    email: str
    programme: Optional[str]
    year_of_study: Optional[int]
    gender: Optional[str]
    biometric_consent: bool
    consent_date: Optional[datetime]
    is_active: bool
    has_biometric_profile: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class StudentListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    students: list[StudentResponse]


# ── Face Recognition ──────────────────────────────────────────────────────────

class EnrollmentResponse(BaseModel):
    student_id: UUID
    student_number: str
    enrolled: bool
    face_quality_score: float
    message: str


class FaceCaptureResponse(BaseModel):
    face_detected: bool
    face_count: int
    quality_score: Optional[float]
    message: str


class LivenessResult(BaseModel):
    is_live: bool
    confidence: float
    method: str = "DINOv2-PAD"


class VerificationResult(BaseModel):
    student_id: Optional[UUID]
    student_number: Optional[str]
    student_name: Optional[str]
    face_detected: bool
    face_similarity_score: Optional[float]
    liveness: Optional[LivenessResult]
    sis_eligible: Optional[bool]
    predicate_met: Optional[bool]
    registered_for_exam: Optional[bool]
    correct_venue: Optional[bool]
    outcome: str
    outcome_reason: str
    processing_time_ms: int
    attempt_id: UUID


# ── Override ──────────────────────────────────────────────────────────────────

class OverrideRequest(BaseModel):
    attempt_id: UUID
    reason: str = Field(..., min_length=10, max_length=500)


class OverrideResponse(BaseModel):
    attempt_id: UUID
    overridden: bool
    overridden_by: str
    overridden_at: datetime


# ── Exam Session ──────────────────────────────────────────────────────────────

class ExamSessionCreate(BaseModel):
    module_code: str = Field(..., min_length=3, max_length=20)
    module_name: str = Field(..., min_length=3, max_length=255)
    venue: str = Field(..., min_length=2, max_length=100)
    campus: str = "TUT Pretoria"
    scheduled_start: datetime
    scheduled_end: datetime

    @field_validator("scheduled_end")
    @classmethod
    def end_after_start(cls, v, info):
        if "scheduled_start" in info.data and v <= info.data["scheduled_start"]:
            raise ValueError("scheduled_end must be after scheduled_start")
        return v


class ExamSessionResponse(BaseModel):
    id: UUID
    module_code: str
    module_name: str
    venue: str
    campus: str
    scheduled_start: datetime
    scheduled_end: datetime
    created_at: datetime
    total_attempts: int = 0
    granted_count: int = 0

    model_config = {"from_attributes": True}


# ── Admin Dashboard ───────────────────────────────────────────────────────────

class SystemStats(BaseModel):
    total_students: int
    enrolled_students: int
    total_attempts_today: int
    granted_today: int
    denied_today: int
    overrides_today: int
    avg_processing_time_ms: float
    false_acceptance_rate: float
    false_rejection_rate: float
    active_exam_sessions: int


class AttendanceRegisterEntry(BaseModel):
    student_number: str
    student_name: str
    outcome: str
    attempted_at: datetime
    was_overridden: bool


class AttendanceRegister(BaseModel):
    exam_session_id: UUID
    module_code: str
    module_name: str
    venue: str
    scheduled_start: datetime
    total_registered: int
    attended: int
    entries: list[AttendanceRegisterEntry]


# ── User management ───────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    role: str = "invigilator"
    # password is intentionally omitted — the system generates a secure
    # temporary password and emails it to the new user automatically


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

    model_config = {"from_attributes": True}