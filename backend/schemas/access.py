# schemas/access.py
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List
from enum import Enum

class AccessAction(str, Enum):
    GRANT = "grant"
    DENY = "deny"
    OVERRIDE = "override"

class AccessStatus(str, Enum):
    ELIGIBLE = "eligible"
    NOT_ELIGIBLE = "not_eligible"
    PENDING_REVIEW = "pending_review"
    ALREADY_ATTENDED = "already_attended"
    SESSION_CLOSED = "session_closed"

class AccessGrantRequest(BaseModel):
    student_id: int = Field(..., gt=0, description="Student ID to grant access")
    session_id: int = Field(..., gt=0, description="Exam session ID")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for grant/deny/override")
    
    @validator('reason')
    def validate_reason(cls, v, values):
        if values.get('action') == 'override' and not v:
            raise ValueError('Override requires a reason')
        return v

class AccessResponse(BaseModel):
    status: str
    student_id: int
    session_id: int
    timestamp: datetime
    tts_feedback: str
    transaction_id: str
    reason: Optional[str] = None
    override_id: Optional[int] = None

class AccessStatusResponse(BaseModel):
    student_id: int
    session_id: int
    status: AccessStatus
    is_eligible: bool
    reason: Optional[str] = None
    holds: List[str] = []
    academic_standing: Optional[str] = None
    already_attended: bool = False
    session_active: bool = False
    remaining_attempts: int = 3
    last_attempt_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True

class AccessLogResponse(BaseModel):
    access_log_id: int
    user_id: int
    username: str
    student_id: int
    session_id: int
    action: AccessAction
    timestamp: datetime
    tts_feedback_sent: bool
    reason: Optional[str]
    
    class Config:
        from_attributes = True

class AccessStatistics(BaseModel):
    total_grants: int
    total_denials: int
    total_overrides: int
    success_rate: float
    average_response_time_ms: float
    top_denial_reasons: List[dict]
    overrides_by_invigilator: List[dict]
    period_days: int
    
class BulkAccessRequest(BaseModel):
    """For batch access operations"""
    student_ids: List[int] = Field(..., min_items=1, max_items=100)
    session_id: int
    action: AccessAction
    reason: Optional[str] = None
    
    @validator('student_ids')
    def validate_student_ids(cls, v):
        if len(set(v)) != len(v):
            raise ValueError('Duplicate student IDs found')
        return v

class BulkAccessResponse(BaseModel):
    total_processed: int
    successful: int
    failed: int
    results: List[dict]
    timestamp: datetime