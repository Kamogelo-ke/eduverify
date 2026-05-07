# schemas/sis.py
from pydantic import BaseModel
from typing import List, Optional

class SISEligibilityRequest(BaseModel):
    student_id: int
    session_id: int

class SISEligibilityResponse(BaseModel):
    eligible: bool
    reason: str
    academic_standing: Optional[str] = None
    registered_modules: List[str] = []
    holds: List[str] = []