# services/access_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import uuid
import asyncio

from models.system_user import SystemUser
# from models.student import Student
from models.exam_session import ExamSession, SessionStatus
from models.access_log import AccessLog, AccessAction
from models.verification_log import VerificationLog, VerificationOutcome
from repositories.access_log_repo import AccessLogRepository
from repositories.student_repo import StudentRepository
from services.sis_service import SISService
# from services.ai_pipeline import AIPipelineService
from utils.logging import audit_logger
from utils.tts import TTSService

class AccessService:
    """Service for managing exam access control"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.access_repo = AccessLogRepository(db)
        self.student_repo = StudentRepository(db)
        self.sis_service = SISService()
        # self.ai_service = AIPipelineService()
        self.tts_service = TTSService()
    
    async def grant_access(
        self,
        student_id: int,
        session_id: int,
        granted_by: int,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Grant access to exam for a student
        Triggers TTS feedback: "Granted"
        """
        # Check if session is active
        session = await self._get_session(session_id)
        if not session or session.Status != SessionStatus.ACTIVE:
            raise ValueError("Exam session is not active")
        
        # Check if student already attended
        already_attended = await self._check_already_attended(student_id, session_id)
        if already_attended:
            raise ValueError("Student already marked as attended")
        
        # Create access log
        transaction_id = str(uuid.uuid4())
        log_data = {
            "id": granted_by,
            "id": student_id,
            "id": session_id,
            "Action": AccessAction.GRANT,
            "TTSFeedbackSent": 1,
            "Reason": reason
        }
        
        access_log = await self.access_repo.create(log_data)
        
        # Mark attendance
        await self._mark_attendance(student_id, session_id, granted_by)
        
        # Trigger TTS feedback
        await self.tts_service.speak("Granted", venue=session.VenueLocation)
        
        # Audit log
        audit_logger.log(
            event="Access granted",
            user_id=granted_by,
            action="GRANT",
            details={
                "student_id": student_id,
                "session_id": session_id,
                "transaction_id": transaction_id,
                "reason": reason
            }
        )
        
        return {
            "status": "granted",
            "transaction_id": transaction_id,
            "access_log_id": access_log.id,
            "timestamp": datetime.now()
        }
    
    async def deny_access(
        self,
        student_id: int,
        session_id: int,
        denied_by: int,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Deny access to exam for a student
        Triggers TTS feedback: "Denied"
        """
        # Create access log
        transaction_id = str(uuid.uuid4())
        log_data = {
            "id": denied_by,
            "id": student_id,
            "id": session_id,
            "Action": AccessAction.DENY,
            "TTSFeedbackSent": 1,
            "Reason": reason
        }
        
        access_log = await self.access_repo.create(log_data)
        
        # Create verification log entry
        verification_log = VerificationLog(
            id=student_id,
            session_id=session_id,
            DeviceID="ACCESS_CONTROL",
            VerificationOutcome=VerificationOutcome.DENIED_BIOMETRIC_FAIL,
            DigitalSignature=f"DENY_{transaction_id}",
            VenueLocation=(await self._get_session(session_id)).VenueLocation,
            AttemptNumber=1
        )
        self.db.add(verification_log)
        await self.db.commit()
        
        # Trigger TTS feedback
        session = await self._get_session(session_id)
        await self.tts_service.speak("Denied", venue=session.VenueLocation)
        
        # Audit log
        audit_logger.log(
            event="Access denied",
            user_id=denied_by,
            action="DENY",
            details={
                "student_id": student_id,
                "session_id": session_id,
                "transaction_id": transaction_id,
                "reason": reason
            }
        )
        
        return {
            "status": "denied",
            "transaction_id": transaction_id,
            "access_log_id": access_log.id,
            "timestamp": datetime.now()
        }
    
    async def manual_override(
        self,
        student_id: int,
        session_id: int,
        overridden_by: int,
        reason: str
    ) -> Dict[str, Any]:
        """
        Manual override for special cases (facial trauma, scanner offline)
        Requires invigilator authorization and reason
        """
        if not reason:
            raise ValueError("Override requires a reason")
        
        # Check if session is active
        session = await self._get_session(session_id)
        if not session or session.Status != SessionStatus.ACTIVE:
            raise ValueError("Exam session is not active")
        
        # Check if manual override is allowed for this session
        if not session.AllowManualOverride:
            raise ValueError("Manual override is disabled for this session")
        
        # Create access log with override action
        transaction_id = str(uuid.uuid4())
        log_data = {
            "id": overridden_by,
            "id": student_id,
            "id": session_id,
            "Action": AccessAction.OVERRIDE,
            "TTSFeedbackSent": 1,
            "Reason": reason
        }
        
        access_log = await self.access_repo.create(log_data)
        
        # Create verification log with manual override outcome
        verification_log = VerificationLog(
            id=student_id,
            session_id=session_id,
            DeviceID="MANUAL_OVERRIDE",
            VerificationOutcome=VerificationOutcome.MANUAL_OVERRIDE,
            DigitalSignature=f"OVERRIDE_{transaction_id}",
            VenueLocation=session.VenueLocation,
            AttemptNumber=1
        )
        self.db.add(verification_log)
        await self.db.commit()
        await self.db.refresh(verification_log)
        
        # Mark attendance
        await self._mark_attendance(student_id, session_id, overridden_by)
        
        # Trigger TTS feedback
        await self.tts_service.speak("Access granted via override", venue=session.VenueLocation)
        
        # Audit log (sensitive - includes override reason)
        audit_logger.log(
            event="Manual override granted",
            user_id=overridden_by,
            action="OVERRIDE",
            details={
                "student_id": student_id,
                "session_id": session_id,
                "transaction_id": transaction_id,
                "override_reason": reason
            },
            sensitive=True
        )
        
        return {
            "status": "overridden",
            "transaction_id": transaction_id,
            "access_log_id": access_log.id,
            "override_id": verification_log.LogID,
            "timestamp": datetime.now()
        }
    
    async def get_access_status(
        self,
        student_id: int,
        session_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get current access status for a student
        Returns eligibility and any holds
        """
        # Get student info
        student = await self.student_repo.get_by_id(student_id)
        if not student:
            return {
                "student_id": student_id,
                "status": "not_eligible",
                "is_eligible": False,
                "reason": "Student not found"
            }
        
        # If session_id provided, check specific session
        if session_id:
            session = await self._get_session(session_id)
            if not session:
                return {
                    "student_id": student_id,
                    "session_id": session_id,
                    "status": "not_eligible",
                    "is_eligible": False,
                    "reason": "Exam session not found"
                }
            
            # Check if session is active
            session_active = session.Status == SessionStatus.ACTIVE
            
            # Check if already attended
            already_attended = await self._check_already_attended(student_id, session_id)
            
            # Check SIS eligibility
            sis_eligibility = await self.sis_service.check_eligibility(
                student_id, session_id, self.db
            )
            
            # Get remaining attempts
            remaining_attempts = await self._get_remaining_attempts(student_id, session_id)
            
            # Get last attempt
            last_attempt = await self._get_last_attempt(student_id, session_id)
            
            return {
                "student_id": student_id,
                "session_id": session_id,
                "status": "eligible" if sis_eligibility["eligible"] and not already_attended else "not_eligible",
                "is_eligible": sis_eligibility["eligible"] and not already_attended and session_active,
                "reason": sis_eligibility["reason"] if not sis_eligibility["eligible"] else "Already attended" if already_attended else None,
                "holds": sis_eligibility["holds"],
                "academic_standing": sis_eligibility["academic_standing"],
                "already_attended": already_attended,
                "session_active": session_active,
                "remaining_attempts": remaining_attempts,
                "last_attempt_at": last_attempt
            }
        
        # Return basic student status
        return {
            "student_id": student_id,
            "status": "eligible" if student.is_eligible_for_exam() else "not_eligible",
            "is_eligible": student.is_eligible_for_exam(),
            "reason": "Student consent not given" if not student.ConsentGiven else "Academic standing not eligible" if student.AcademicStanding == "Suspended" else None,
            "holds": [],
            "academic_standing": student.AcademicStanding,
            "already_attended": False,
            "session_active": False,
            "remaining_attempts": 3,
            "last_attempt_at": None
        }
    
    async def verify_and_access(
        self,
        student_id: int,
        session_id: int,
        face_image: bytes,
        device_id: str
    ) -> Dict[str, Any]:
        """
        Complete verification flow: Check eligibility -> Face recognition -> Grant/Deny
        """
        # Step 1: Check eligibility
        eligibility = await self.sis_service.check_eligibility(student_id, session_id, self.db)
        
        if not eligibility["eligible"]:
            # Log failed attempt
            await self._log_verification_attempt(
                student_id, session_id, device_id,
                VerificationOutcome.DENIED_NOT_REGISTERED,
                eligibility["reason"]
            )
            return {
                "granted": False,
                "reason": eligibility["reason"],
                "holds": eligibility["holds"],
                "step": "eligibility_check"
            }
        
        # Step 2: Get student biometric hash
        student = await self.student_repo.get_by_id(student_id)
        if not student or not student.BiometricHash:
            return {
                "granted": False,
                "reason": "Student biometric data not found",
                "step": "biometric_check"
            }
        
        # Step 3: Process face through AI pipeline
        face_result = await self.ai_service.process_face(face_image, student.BiometricHash)
        
        if not face_result["success"]:
            await self._log_verification_attempt(
                student_id, session_id, device_id,
                VerificationOutcome.DENIED_BIOMETRIC_FAIL,
                face_result.get("error", "Face processing failed")
            )
            return {
                "granted": False,
                "reason": face_result.get("error", "Face verification failed"),
                "face_detected": face_result.get("face_detected", False),
                "liveness_score": face_result.get("liveness_score"),
                "step": "face_processing"
            }
        
        # Step 4: Check liveness
        if not face_result["is_live"]:
            await self._log_verification_attempt(
                student_id, session_id, device_id,
                VerificationOutcome.DENIED_BIOMETRIC_FAIL,
                "Liveness detection failed"
            )
            return {
                "granted": False,
                "reason": "Liveness check failed - possible spoofing attempt",
                "liveness_score": face_result["liveness_score"],
                "step": "liveness_check"
            }
        
        # Step 5: Check face match
        if not face_result["is_match"]:
            await self._log_verification_attempt(
                student_id, session_id, device_id,
                VerificationOutcome.DENIED_BIOMETRIC_FAIL,
                "Face does not match"
            )
            return {
                "granted": False,
                "reason": "Face does not match registered student",
                "match_score": face_result["match_score"],
                "threshold": face_result.get("threshold"),
                "step": "face_matching"
            }
        
        # Step 6: Grant access
        grant_result = await self.grant_access(
            student_id, session_id, 1,  # System user ID 1 for auto-grant
            "Face verification successful"
        )
        
        # Log successful verification
        await self._log_verification_attempt(
            student_id, session_id, device_id,
            VerificationOutcome.SUCCESS,
            "Verification successful",
            face_result["match_score"],
            face_result["liveness_score"]
        )
        
        return {
            "granted": True,
            "reason": "Verification successful",
            "match_score": face_result["match_score"],
            "liveness_score": face_result["liveness_score"],
            "processing_time_ms": face_result["processing_time_ms"],
            "transaction_id": grant_result["transaction_id"],
            "step": "completed"
        }
    
    async def bulk_access(
        self,
        student_ids: List[int],
        session_id: int,
        action: AccessAction,
        user_id: int,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Bulk access operations for multiple students
        """
        results = []
        successful = 0
        failed = 0
        
        for student_id in student_ids:
            try:
                if action == AccessAction.GRANT:
                    result = await self.grant_access(student_id, session_id, user_id, reason)
                elif action == AccessAction.DENY:
                    result = await self.deny_access(student_id, session_id, user_id, reason)
                else:
                    result = await self.manual_override(student_id, session_id, user_id, reason or "Bulk operation")
                
                results.append({
                    "student_id": student_id,
                    "success": True,
                    "status": result["status"],
                    "transaction_id": result["transaction_id"]
                })
                successful += 1
                
            except Exception as e:
                results.append({
                    "student_id": student_id,
                    "success": False,
                    "error": str(e)
                })
                failed += 1
        
        return {
            "total_processed": len(student_ids),
            "successful": successful,
            "failed": failed,
            "results": results,
            "timestamp": datetime.now()
        }
    
    async def get_access_statistics(
        self,
        days: int = 30,
        session_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get access control statistics
        """
        # Get counts
        query = select(
            func.count().filter(AccessLog.Action == AccessAction.GRANT).label("grants"),
            func.count().filter(AccessLog.Action == AccessAction.DENY).label("denials"),
            func.count().filter(AccessLog.Action == AccessAction.OVERRIDE).label("overrides")
        ).where(AccessLog.Timestamp >= datetime.now() - timedelta(days=days))
        
        if session_id:
            query = query.where(AccessLog.id == session_id)
        
        result = await self.db.execute(query)
        counts = result.one()
        
        total = counts.grants + counts.denials + counts.overrides
        success_rate = (counts.grants / total * 100) if total > 0 else 0
        
        # Top denial reasons
        denial_reasons = await self.db.execute(
            select(AccessLog.Reason, func.count())
            .where(
                AccessLog.Action == AccessAction.DENY,
                AccessLog.Reason.isnot(None),
                AccessLog.Timestamp >= datetime.now() - timedelta(days=days)
            )
            .group_by(AccessLog.Reason)
            .order_by(func.count().desc())
            .limit(5)
        )
        
        # Overrides by invigilator
        overrides_by_invigilator = await self.db.execute(
            select(SystemUser.Username, func.count())
            .join(AccessLog, AccessLog.id == SystemUser.id)
            .where(
                AccessLog.Action == AccessAction.OVERRIDE,
                AccessLog.Timestamp >= datetime.now() - timedelta(days=days)
            )
            .group_by(SystemUser.Username)
            .order_by(func.count().desc())
        )
        
        return {
            "total_grants": counts.grants or 0,
            "total_denials": counts.denials or 0,
            "total_overrides": counts.overrides or 0,
            "success_rate": round(success_rate, 2),
            "average_response_time_ms": await self._get_average_response_time(days),
            "top_denial_reasons": [
                {"reason": r[0], "count": r[1]} for r in denial_reasons
            ],
            "overrides_by_invigilator": [
                {"username": r[0], "count": r[1]} for r in overrides_by_invigilator
            ],
            "period_days": days
        }
    
    async def _get_session(self, session_id: int) -> Optional[ExamSession]:
        """Get exam session by ID"""
        query = select(ExamSession).where(ExamSession.id == session_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    # async def _check_already_attended(self, student_id: int, session_id: int) -> bool:
    #     """Check if student already marked as attended"""
    #     query = select(func.count()).where(
    #         and_(
    #             AttendanceRegister.id == student_id,
    #             AttendanceRegister.id == session_id
    #         )
    #     )
    #     result = await self.db.execute(query)
    #     return result.scalar() > 0
    
    # async def _mark_attendance(self, student_id: int, session_id: int, marked_by: int):
    #     """Mark student attendance"""
    #     from models.attendance_register import AttendanceRegister, AttendanceStatus
        
    #     attendance = AttendanceRegister(
    #         id=student_id,
    #         session_id=session_id,
    #         MarkedBy=marked_by,
    #         Status=AttendanceStatus.PRESENT
    #     )
    #     self.db.add(attendance)
    #     await self.db.commit()
    
    async def _get_remaining_attempts(self, student_id: int, session_id: int) -> int:
        """Get remaining verification attempts for student"""
        query = select(func.count()).where(
            and_(
                VerificationLog.id == student_id,
                VerificationLog.id == session_id,
                VerificationLog.Timestamp >= datetime.now() - timedelta(hours=1)
            )
        )
        result = await self.db.execute(query)
        attempts = result.scalar() or 0
        return max(0, 3 - attempts)  # Max 3 attempts
    
    async def _get_last_attempt(self, student_id: int, session_id: int) -> Optional[datetime]:
        """Get last verification attempt timestamp"""
        query = select(VerificationLog.Timestamp).where(
            and_(
                VerificationLog.id == student_id,
                VerificationLog.id == session_id
            )
        ).order_by(VerificationLog.Timestamp.desc()).limit(1)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _log_verification_attempt(
        self,
        student_id: int,
        session_id: int,
        device_id: str,
        outcome: VerificationOutcome,
        reason: str,
        match_score: Optional[float] = None,
        liveness_score: Optional[float] = None
    ):
        """Log verification attempt"""
        session = await self._get_session(session_id)
        verification_log = VerificationLog(
            id=student_id,
            session_id=session_id,
            DeviceID=device_id,
            VerificationOutcome=outcome,
            DigitalSignature=f"{outcome.value}_{datetime.now().timestamp()}",
            VenueLocation=session.VenueLocation if session else "Unknown",
            AttemptNumber=await self._get_attempt_number(student_id, session_id),
            FaceMatchScore=match_score,
            LivenessScore=liveness_score
        )
        self.db.add(verification_log)
        await self.db.commit()
    
    async def _get_attempt_number(self, student_id: int, session_id: int) -> int:
        """Get current attempt number for student"""
        query = select(func.count()).where(
            and_(
                VerificationLog.id == student_id,
                VerificationLog.id == session_id
            )
        )
        result = await self.db.execute(query)
        return (result.scalar() or 0) + 1
    
    async def _get_average_response_time(self, days: int) -> float:
        """Get average response time for access decisions"""
        query = select(func.avg(VerificationLog.FaceMatchScore)).where(
            VerificationLog.Timestamp >= datetime.now() - timedelta(days=days)
        )
        result = await self.db.execute(query)
        avg_time = result.scalar()
        return float(avg_time) if avg_time else 0.0

