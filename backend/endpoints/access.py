# api/v1/endpoints/access.py (Additional)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from datetime import datetime

from database import get_db
from core.dependencies import get_current_user, require_role
from services.access_service import AccessService
from schemas.access import AccessGrantRequest, AccessStatusResponse
from models.system_user import SystemUser

router = APIRouter(prefix="/access", tags=["Access Control"])

@router.post("/grant")
async def grant_access(
    request: AccessGrantRequest,
    db: AsyncSession = Depends(get_db),
    current_user: SystemUser = Depends(require_role(["system", "invigilator"]))
) -> Dict[str, Any]:
    """
    Grant access to exam for a student
    Triggers TTS feedback: "Granted"
    """
    service = AccessService(db)
    result = await service.grant_access(
        student_id=request.student_id,
        session_id=request.session_id,
        granted_by=current_user.id,
        reason=request.reason
    )
    
    return {
        "status": "granted",
        "student_id": request.student_id,
        "timestamp": datetime.now().isoformat(),
        "tts_feedback": "Granted",
        "transaction_id": result["transaction_id"]
    }

@router.post("/deny")
async def deny_access(
    request: AccessGrantRequest,
    db: AsyncSession = Depends(get_db),
    current_user: SystemUser = Depends(require_role(["system", "invigilator"]))
) -> Dict[str, Any]:
    """
    Deny access to exam for a student
    Triggers TTS feedback: "Denied"
    """
    service = AccessService(db)
    result = await service.deny_access(
        student_id=request.student_id,
        session_id=request.session_id,
        denied_by=current_user.id,
        reason=request.reason
    )
    
    return {
        "status": "denied",
        "student_id": request.student_id,
        "timestamp": datetime.now().isoformat(),
        "tts_feedback": "Denied",
        "reason": request.reason,
        "transaction_id": result["transaction_id"]
    }

@router.post("/override")
async def manual_override(
    request: AccessGrantRequest,
    db: AsyncSession = Depends(get_db),
    current_user: SystemUser = Depends(require_role(["system", "invigilator"]))
) -> Dict[str, Any]:
    """
    Manual override for特殊情况 (e.g., facial trauma, scanner offline)
    Requires invigilator authorization
    """
    service = AccessService(db)
    result = await service.manual_override(
        student_id=request.student_id,
        session_id=request.session_id,
        overridden_by=current_user.id,
        reason=request.reason
    )
    
    return {
        "status": "overridden",
        "student_id": request.student_id,
        "timestamp": datetime.now().isoformat(),
        "tts_feedback": "Access granted via override",
        "override_reason": request.reason,
        "override_id": result["override_id"]
    }

@router.get("/status/{student_id}")
async def get_access_status(
    student_id: int,
    session_id: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user)
) -> AccessStatusResponse:
    """
    Get current access status for a student
    Returns eligibility and any holds
    """
    service = AccessService(db)
    status = await service.get_access_status(student_id, session_id)
    return AccessStatusResponse(**status)