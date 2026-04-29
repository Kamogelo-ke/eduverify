# backend/api/v1/endpoints/audit.py
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date, datetime
import csv
from io import StringIO
from fastapi.responses import StreamingResponse

from database import get_db
from core.dependencies import get_current_user, require_role
from schemas.audit import VerificationLogCreate, ExportFilters
from services.audit_service import AuditService
from models.system_user import SystemUser

router = APIRouter(prefix="/logs", tags=["Audit & Logging"])

@router.post("/attempt", status_code=201)
async def log_verification_attempt(
    log_data: VerificationLogCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user)
):
    """Log a facial recognition verification attempt"""
    service = AuditService(db)
    result = await service.log_verification_attempt(log_data, current_user.UserID)
    return result

@router.get("/session/{venue}")
async def get_session_logs(
    venue: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    outcome: Optional[str] = Query(
        None, 
        description="Filter by outcome. Valid values: 'Success', 'Denied_Biometric_Fail', 'Denied_Not_Registered', 'Manual_Override'"
    ),
    limit: int = Query(100, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: SystemUser = Depends(require_role(["admin", "invigilator"]))
):
    """Get all logs for a specific venue"""
    # Add validation for outcome parameter
    valid_outcomes = {'Success', 'Denied_Biometric_Fail', 'Denied_Not_Registered', 'Manual_Override'}
    if outcome and outcome not in valid_outcomes:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid outcome value. Must be one of: {', '.join(valid_outcomes)}"
        )
    
    service = AuditService(db)
    return await service.get_session_logs(venue, start_date, end_date, outcome, limit)

@router.get("/student/{student_id}")
async def get_student_logs(
    student_id: int,
    limit: int = Query(50, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: SystemUser = Depends(require_role(["admin", "invigilator"]))
):
    """Get all verification logs for a specific student"""
    service = AuditService(db)
    return await service.get_student_logs(student_id, limit)

@router.get("/export")
async def export_logs(
    start_date: date,
    end_date: date,
    venue: Optional[str] = None,
    format: str = Query("csv", regex="^(csv|json)$"),
    db: AsyncSession = Depends(get_db),
    current_user: SystemUser = Depends(require_role(["admin"]))
):
    """Export logs for compliance reporting (POPIA)"""
    service = AuditService(db)
    logs = await service.export_logs(start_date, end_date, venue)
    
    if format == "json":
        return {
            "export_date": datetime.now().isoformat(),
            "date_range": {"start": start_date, "end": end_date},
            "total_records": len(logs),
            "records": [
                {
                    "timestamp": log[0].Timestamp,
                    "student_name": f"{log[1]} {log[2]}",
                    "student_id": log[0].StudentID,
                    "session_id": log[0].SessionID,
                    "outcome": log[0].VerificationOutcome.value,
                    "device_id": log[0].DeviceID,
                    "digital_signature": log[0].DigitalSignature
                }
                for log in logs
            ]
        }
    
    # CSV export
    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "Timestamp", "Student Name", "Student ID", "Session ID",
        "Outcome", "Device ID", "Digital Signature"
    ])
    
    for log in logs:
        writer.writerow([
            log[0].Timestamp,
            f"{log[1]} {log[2]}",
            log[0].StudentID,
            log[0].SessionID,
            log[0].VerificationOutcome.value,
            log[0].DeviceID,
            log[0].DigitalSignature
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=audit_logs_{start_date}_to_{end_date}.csv"
        }
    )

# @router.get("/statistics")
# async def get_audit_statistics(
#     days: int = Query(30, ge=1, le=365),
#     db: AsyncSession = Depends(get_db),
#     current_user: SystemUser = Depends(require_role(["admin"]))
# ):
#     """Get audit statistics for compliance reporting"""
#     service = AuditService(db)
#     return await service.get_audit_statistics(days)