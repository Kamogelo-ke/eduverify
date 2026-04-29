# backend/services/audit_service.py
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case
from sqlalchemy.sql import expression

from repositories.verification_log_repo import VerificationLogRepository
from repositories.access_log_repo import AccessLogRepository
from schemas.audit import VerificationLogCreate
from models.student import Student
from models.verification_log import VerificationLog, VerificationOutcome
from models.access_log import AccessLog, AccessAction
from utils.logging import audit_logger, get_logger

logger = get_logger(__name__)

class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.verification_repo = VerificationLogRepository(db)
        self.access_repo = AccessLogRepository(db)
    
    async def log_verification_attempt(
        self, 
        log_data: VerificationLogCreate,
        user_id: int
    ) -> Dict[str, Any]:
        """Log verification attempt with audit trail"""
        
        # Create log entry
        log_dict = {
            "StudentID": log_data.student_id,
            "SessionID": log_data.session_id,
            "DeviceID": log_data.device_id,
            "VerificationOutcome": log_data.outcome.value,
            "DigitalSignature": log_data.digital_signature,
            "VenueLocation": log_data.venue_location,
            "AttemptNumber": log_data.attempt_number,
            "FaceMatchScore": log_data.face_match_score,
            "LivenessScore": log_data.liveness_score
        }
        
        verification_log = await self.verification_repo.create(log_dict)
        
        # Audit log for compliance
        audit_logger.log(
            event="Verification attempt logged",
            user_id=user_id,
            action="VERIFICATION",
            details={
                "student_id": log_data.student_id,
                "session_id": log_data.session_id,
                "outcome": log_data.outcome.value,
                "log_id": verification_log.LogID
            }
        )
        
        return {
            "message": "Attempt logged", 
            "log_id": verification_log.LogID,
            "timestamp": verification_log.Timestamp
        }
    
    async def get_session_logs(
        self,
        venue: str,
        start_date: Optional[date],
        end_date: Optional[date],
        outcome: Optional[str],
        limit: int
    ) -> Dict[str, Any]:
        """Get logs for a venue with student names"""
        
        query = select(VerificationLog, Student).join(
            Student, VerificationLog.StudentID == Student.StudentID
        ).where(
            VerificationLog.VenueLocation.ilike(f"%{venue}%")
        )
        
        if start_date:
            query = query.where(func.date(VerificationLog.Timestamp) >= start_date)
        if end_date:
            query = query.where(func.date(VerificationLog.Timestamp) <= end_date)
        if outcome:
            query = query.where(VerificationLog.VerificationOutcome == outcome)
        
        query = query.order_by(VerificationLog.Timestamp.desc()).limit(limit)
        result = await self.db.execute(query)
        rows = result.all()
        
        logs = []
        for verification_log, student in rows:
            logs.append({
                "log_id": verification_log.LogID,
                "student_name": f"{student.FirstName} {student.LastName}",
                "student_id": verification_log.StudentID,
                "timestamp": verification_log.Timestamp,
                "outcome": verification_log.VerificationOutcome.value,
                "device_id": verification_log.DeviceID,
                "face_match_score": verification_log.FaceMatchScore,
                "liveness_score": verification_log.LivenessScore
            })
        
        return {
            "venue": venue,
            "total_logs": len(logs),
            "logs": logs
        }
    
    async def get_student_logs(
        self,
        student_id: int,
        limit: int
    ) -> Dict[str, Any]:
        """Get all logs for a student with statistics"""
        
        # Get student info
        student_query = select(Student).where(Student.StudentID == student_id)
        student_result = await self.db.execute(student_query)
        student = student_result.scalar_one_or_none()
        
        if not student:
            return {
                "student_id": student_id,
                "student_name": "Unknown",
                "total_attempts": 0,
                "successful_attempts": 0,
                "failed_attempts": 0,
                "logs": []
            }
        
        # Get logs
        logs_query = select(VerificationLog).where(
            VerificationLog.StudentID == student_id
        ).order_by(VerificationLog.Timestamp.desc()).limit(limit)
        
        logs_result = await self.db.execute(logs_query)
        logs = logs_result.scalars().all()
        
        successful = sum(1 for l in logs if l.VerificationOutcome == VerificationOutcome.SUCCESS)
        
        return {
            "student_id": student_id,
            "student_name": f"{student.FirstName} {student.LastName}",
            "total_attempts": len(logs),
            "successful_attempts": successful,
            "failed_attempts": len(logs) - successful,
            "logs": [
                {
                    "timestamp": log.Timestamp,
                    "session_id": log.SessionID,
                    "outcome": log.VerificationOutcome.value,
                    "device_id": log.DeviceID,
                    "attempt_number": log.AttemptNumber
                }
                for log in logs
            ]
        }
    
    async def get_audit_statistics(self, days: int) -> Dict[str, Any]:
        """Get audit statistics for compliance reporting"""
        
        start_date = datetime.now() - timedelta(days=days)
        
        # Total attempts
        total_query = select(func.count()).where(
            VerificationLog.Timestamp >= start_date
        )
        total_attempts = await self.db.scalar(total_query) or 0
        
        # Successful attempts
        success_query = select(func.count()).where(
            and_(
                VerificationLog.Timestamp >= start_date,
                VerificationLog.VerificationOutcome == VerificationOutcome.SUCCESS
            )
        )
        successful = await self.db.scalar(success_query) or 0
        
        # Daily breakdown - FIXED: Use proper case syntax
        daily_query = select(
            func.date(VerificationLog.Timestamp).label("date"),
            func.count().label("total"),
            func.sum(
                case(
                    (VerificationLog.VerificationOutcome == VerificationOutcome.SUCCESS, 1),
                    else_=0
                )
            ).label("successful")
        ).where(
            VerificationLog.Timestamp >= start_date
        ).group_by(func.date(VerificationLog.Timestamp))
        
        daily_result = await self.db.execute(daily_query)
        daily_breakdown = [
            {"date": str(row.date), "total": row.total, "successful": row.successful or 0}
            for row in daily_result
        ]
        
        # Manual overrides
        overrides_query = select(func.count()).where(
            and_(
                AccessLog.Timestamp >= start_date,
                AccessLog.Action == AccessAction.OVERRIDE
            )
        )
        manual_overrides = await self.db.scalar(overrides_query) or 0
        
        success_rate = round((successful / total_attempts * 100), 2) if total_attempts > 0 else 0
        
        return {
            "period_days": days,
            "total_verification_attempts": total_attempts,
            "success_rate": success_rate,
            "manual_overrides": manual_overrides,
            "daily_breakdown": daily_breakdown,
            "compliance_ready": True,
            "export_available": True
        }
    
    async def export_logs(
        self,
        start_date: date,
        end_date: date,
        venue: Optional[str] = None
    ) -> List[tuple]:
        """Export logs for compliance reporting"""
        
        query = select(
            VerificationLog,
            Student.FirstName,
            Student.LastName,
        ).join(
            Student, VerificationLog.StudentID == Student.StudentID
        ).where(
            and_(
                func.date(VerificationLog.Timestamp) >= start_date,
                func.date(VerificationLog.Timestamp) <= end_date
            )
        )
        
        if venue:
            query = query.where(VerificationLog.VenueLocation.ilike(f"%{venue}%"))
        
        query = query.order_by(VerificationLog.Timestamp)
        result = await self.db.execute(query)
        return result.all()