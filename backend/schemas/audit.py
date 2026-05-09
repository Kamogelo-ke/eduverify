# schemas/audit.py
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime, date
from typing import Optional, List
from enum import Enum


class VerificationOutcome(str, Enum):
    SUCCESS = "Success"
    DENIED_BIOMETRIC_FAIL = "Denied_Biometric_Fail"
    DENIED_NOT_REGISTERED = "Denied_Not_Registered"
    MANUAL_OVERRIDE = "Manual_Override"


class VerificationLogCreate(BaseModel):
    student_id: int = Field(..., gt=0)
    session_id: int = Field(..., gt=0)
    device_id: str = Field(..., max_length=255)
    outcome: VerificationOutcome
    digital_signature: str = Field(..., max_length=512)
    venue_location: str = Field(..., max_length=255)
    attempt_number: int = Field(1, ge=1, le=10)
    face_match_score: Optional[float] = Field(None, ge=0, le=1)
    liveness_score: Optional[float] = Field(None, ge=0, le=1)


class VerificationLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    log_id: int
    student_id: int
    student_name: str
    session_id: int
    timestamp: datetime
    outcome: VerificationOutcome
    device_id: str
    face_match_score: Optional[float]
    liveness_score: Optional[float]


class SessionLogsResponse(BaseModel):
    venue: str
    total_logs: int
    logs: List[VerificationLogResponse]


class StudentLogsResponse(BaseModel):
    student_id: int
    student_name: str
    total_attempts: int
    successful_attempts: int
    failed_attempts: int
    logs: List[dict]


class ExportFilters(BaseModel):
    start_date: date
    end_date: date
    venue: Optional[str] = None
    format: str = "csv"

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, info):
        if 'start_date' in info.data and v < info.data['start_date']:
            raise ValueError('end_date must be after start_date')
        return v


class AuditStatistics(BaseModel):
    period_days: int
    total_verification_attempts: int
    success_rate: float
    manual_overrides: int
    daily_breakdown: List[dict]
    compliance_ready: bool = True
