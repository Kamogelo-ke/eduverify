# api/v1/endpoints/sis.py
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import and_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
import logging

from models.exam_session import ExamSession
from models.student import Student
from utils.logging import audit_logger
from schemas.audit import VerificationLogCreate
from database import get_db
from core.dependencies import get_current_user, require_role
from schemas.sis import SISEligibilityRequest, SISEligibilityResponse
from services.sis_service import SISService
from services.audit_service import AuditService
from models.system_user import SystemUser
from models.verification_log import VerificationOutcome

# Use standard logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sis", tags=["SIS Integration"])

# @router.post("/check-eligibility", response_model=SISEligibilityResponse)
# async def check_student_eligibility(
#     request: SISEligibilityRequest,
#     db: AsyncSession = Depends(get_db),
#     current_user: SystemUser = Depends(require_role(["admin", "invigilator", "system"]))
# ) -> SISEligibilityResponse:
#     """
#     Check if student is eligible to write exam
#     """
#     sis_service = SISService()
#     try:
#         result = await sis_service.check_eligibility(
#             request.student_id,
#             request.session_id,
#             db
#         )
        
#         # Ensure holds and registered_modules are lists
#         if "holds" in result and isinstance(result["holds"], set):
#             result["holds"] = list(result["holds"])
#         if "registered_modules" in result and isinstance(result["registered_modules"], set):
#             result["registered_modules"] = list(result["registered_modules"])
        
#         # Generate proper digital signature
#         import hashlib
#         import uuid
#         signature_data = f"{request.student_id}_{request.session_id}_{datetime.now().timestamp()}_{uuid.uuid4().hex}"
#         digital_signature = hashlib.sha256(signature_data.encode()).hexdigest()
        
#         # Log eligibility check for audit
#         audit_service = AuditService(db)
#         await audit_service.log_verification_attempt(
#             log_data=VerificationLogCreate(
#                 student_id=request.student_id,
#                 session_id=request.session_id,
#                 device_id="SIS_CHECK",
#                 outcome=VerificationOutcome.SUCCESS if result["eligible"] else VerificationOutcome.DENIED_NOT_REGISTERED,
#                 digital_signature=digital_signature,
#                 venue_location="SIS_API",
#                 attempt_number=1
#             ),
#             user_id=current_user.id
#         )
        
#         return SISEligibilityResponse(**result)
        
#     except Exception as e:
#         logger.error(f"Error checking eligibility: {str(e)}")
#         # Return a proper error response
#         raise HTTPException(
#             status_code=500, 
#             detail=f"Error checking eligibility: {str(e)}"
#         )
#     finally:
#         await sis_service.close()
        
#         # Generate a proper digital signature (at least 32 chars)
#         import hashlib
#         import uuid
#         signature_data = f"{request.student_id}_{request.session_id}_{datetime.now().timestamp()}_{uuid.uuid4().hex}"
#         digital_signature = hashlib.sha256(signature_data.encode()).hexdigest()
        
#         # Log eligibility check for audit
#         audit_service = AuditService(db)
#         await audit_service.log_verification_attempt(
#             log_data=VerificationLogCreate(
#                 student_id=request.student_id,
#                 session_id=request.session_id,
#                 device_id="SIS_CHECK",
#                 outcome=VerificationOutcome.SUCCESS if result["eligible"] else VerificationOutcome.DENIED_NOT_REGISTERED,
#                 digital_signature=digital_signature,  # Now it's 64 chars
#                 venue_location="SIS_API",
#                 attempt_number=1
#             ),
#             user_id=current_user.id
#         )
        
#         return SISEligibilityResponse(**result)


# @router.post("/sync-students")
# async def sync_students_from_sis(
#     background_tasks: BackgroundTasks,
#     db: AsyncSession = Depends(get_db),
#     current_user: SystemUser = Depends(require_role(["admin"]))
# ) -> Dict[str, Any]:
#     """
#     Sync student data from SIS to local database
#     """
#     # Run sync directly (not in background for testing)
#     try:
#         sis_service = SISService()
#         students = await sis_service.fetch_all_students()
        
#         for student in students:
#             # Insert or update student
#             await db.execute(
#                 text("""
#                     INSERT INTO students ("StudentNumber", "FirstName", "LastName", "Email", "AcademicStanding", "ConsentGiven", "CreatedAt")
#                     VALUES (:num, :first, :last, :email, :standing, :consent, NOW())
#                     ON CONFLICT ("StudentNumber") DO UPDATE SET
#                         "FirstName" = EXCLUDED."FirstName",
#                         "LastName" = EXCLUDED."LastName",
#                         "AcademicStanding" = EXCLUDED."AcademicStanding"
#                 """),
#                 {
#                     "num": student.get("student_number", f"STU_{student['id']}"),
#                     "first": student["first_name"],
#                     "last": student["last_name"],
#                     "email": student.get("email", f"student{student['id']}@test.com"),
#                     "standing": student["academic_standing"],
#                     "consent": student.get("consent_given", True)
#                 }
#             )
        
#         await db.commit()
#         await sis_service.close()
        
#         return {
#             "message": f"Successfully synced {len(students)} students",
#             "status": "completed",
#             "students_synced": len(students)
#         }
        
#     except Exception as e:
#         logger.error(f"Sync failed: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

# @router.get("/modules/{student_id}")
# async def get_student_modules(
#     student_id: int,
#     db: AsyncSession = Depends(get_db),
#     current_user: SystemUser = Depends(require_role(["admin", "invigilator"]))
# ) -> Dict[str, Any]:
#     """Get registered modules for a student from SIS"""
#     sis_service = SISService()
#     try:
#         result = await sis_service.get_student_modules(student_id)
#         return result
#     except Exception as e:
#         logger.error(f"Error getting student modules: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))
#     finally:
#         await sis_service.close()

# @router.get("/exam-timetable/{student_id}")
# async def get_exam_timetable(
#     student_id: int,
#     db: AsyncSession = Depends(get_db),
#     current_user: SystemUser = Depends(require_role(["admin", "invigilator", "student"]))
# ) -> Dict[str, Any]:
#     """Get exam timetable for a student from SIS"""
#     sis_service = SISService()
#     try:
#         result = await sis_service.get_exam_timetable(student_id)
#         return result
#     except Exception as e:
#         logger.error(f"Error getting exam timetable: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))
#     finally:
#         await sis_service.close()


# async def sync_students_task(db: AsyncSession, user_id: int):
#     """
#     Background task to sync students from SIS
#     Note: This runs in a background task, so we need to create a new session
#     """
#     sis_service = None
#     try:
#         # Create a new SIS service instance
#         sis_service = SISService()
        
#         # Fetch students from SIS
#         students = await sis_service.fetch_all_students()
        
#         if not students:
#             logger.warning("No students returned from SIS")
#             return
        
#         # Update local database
#         for student in students:
#             try:
#                 # Check if student exists
#                 check_query = text("""
#                     SELECT "id" FROM students WHERE "StudentNumber" = :student_number
#                 """)
#                 result = await db.execute(check_query, {"student_number": student.get("student_number", f"SIS_{student['id']}")})
#                 existing = result.fetchone()
                
#                 if existing:
#                     # Update existing student
#                     update_query = text("""
#                         UPDATE students 
#                         SET "FirstName" = :first,
#                             "LastName" = :last,
#                             "AcademicStanding" = :standing,
#                             "Email" = :email,
#                             "UpdatedAt" = NOW()
#                         WHERE "StudentNumber" = :student_number
#                     """)
#                     await db.execute(update_query, {
#                         "first": student["first_name"],
#                         "last": student["last_name"],
#                         "standing": student["academic_standing"],
#                         "email": student.get("email", f"student{student['id']}@university.edu"),
#                         "student_number": student.get("student_number", f"SIS_{student['id']}")
#                     })
#                 else:
#                     # Insert new student
#                     insert_query = text("""
#                         INSERT INTO students (
#                             "StudentNumber", "FirstName", "LastName", "Email", 
#                             "AcademicStanding", "EnrollmentStatus", "ConsentGiven", 
#                             "ConsentDate", "CreatedAt"
#                         ) VALUES (
#                             :student_number, :first, :last, :email,
#                             :standing, 'Active', :consent, NOW(), NOW()
#                         )
#                     """)
#                     await db.execute(insert_query, {
#                         "student_number": student.get("student_number", f"SIS_{student['id']}"),
#                         "first": student["first_name"],
#                         "last": student["last_name"],
#                         "email": student.get("email", f"student{student['id']}@university.edu"),
#                         "standing": student["academic_standing"],
#                         "consent": student.get("consent_given", False)
#                     })
                
#             except Exception as e:
#                 logger.error(f"Error syncing student {student.get('id')}: {str(e)}")
#                 continue
        
#         # Commit all changes
#         await db.commit()
        
#         logger.info(f"SIS sync completed by user {user_id}, synced {len(students)} students")
        
#         # Log to audit
#         from backend.utils.logging import audit_logger
#         audit_logger.log(
#             event="SIS student sync completed",
#             user_id=user_id,
#             action="SYNC",
#             details={"students_synced": len(students)}
#         )
        
#     except Exception as e:
#         logger.error(f"SIS sync failed: {str(e)}")
#         await db.rollback()
        
#         # Log failure to audit
#         from backend.utils.logging import audit_logger
#         audit_logger.log(
#             event="SIS student sync failed",
#             user_id=user_id,
#             action="SYNC_ERROR",
#             details={"error": str(e)}
#         )
#     finally:
#         if sis_service:
#             await sis_service.close()


@router.get("/student/{student_id}")
async def get_student_info(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: SystemUser = Depends(require_role(["admin", "invigilator", "system"]))
) -> Dict[str, Any]:
    """
    Get detailed student information from SIS
    Returns: Student profile, academic record, enrollment status
    """
    sis_service = SISService()
    try:
        # First check local database
        student_query = select(Student).where(Student.id == student_id)
        student_result = await db.execute(student_query)
        student = student_result.scalar_one_or_none()
        
        # Get additional data from SIS
        sis_data = await sis_service.get_student_details(student_id)
        
        if not student and not sis_data:
            raise HTTPException(status_code=404, detail="Student not found")
        
        return {
            "student_id": student_id,
            "local_data": {
                "first_name": student.FirstName if student else None,
                "last_name": student.LastName if student else None,
                "email": student.Email if student else None,
                "student_number": student.StudentNumber if student else None,
                "academic_standing": student.AcademicStanding if student else None,
                "consent_given": student.ConsentGiven if student else False
            },
            "sis_data": sis_data,
            "sync_status": "synced" if student else "not_in_local_db"
        }
    finally:
        await sis_service.close()

@router.get("/eligibility/{student_id}")
async def check_eligibility_status(
    student_id: int,
    module_code: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: SystemUser = Depends(require_role(["admin", "invigilator", "system"]))
) -> Dict[str, Any]:
    """
    Check comprehensive eligibility status for a student
    Returns: Registration status, financial holds, academic standing, disciplinary status
    """
    sis_service = SISService()
    try:
        # Get student info
        student_query = select(Student).where(Student.id == student_id)
        student_result = await db.execute(student_query)
        student = student_result.scalar_one_or_none()
        
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Get eligibility from SIS
        eligibility = await sis_service.get_comprehensive_eligibility(student_id, module_code)
        
        return {
            "student_id": student_id,
            "student_name": f"{student.FirstName} {student.LastName}",
            "student_number": student.StudentNumber,
            "module_code": module_code,
            "eligibility_status": "Eligible" if eligibility.get("eligible") else "Not Eligible",
            "checks": {
                "registration": {
                    "status": "passed" if eligibility.get("is_registered") else "failed",
                    "message": eligibility.get("registration_message", "Not registered for this module")
                },
                "academic_standing": {
                    "status": "passed" if eligibility.get("academic_standing") != "Suspended" else "failed",
                    "standing": eligibility.get("academic_standing", "Good"),
                    "message": eligibility.get("academic_message")
                },
                "financial_holds": {
                    "status": "passed" if not eligibility.get("has_financial_hold") else "failed",
                    "has_hold": eligibility.get("has_financial_hold", False),
                    "message": eligibility.get("financial_message")
                },
                "disciplinary_holds": {
                    "status": "passed" if not eligibility.get("has_disciplinary_hold") else "failed",
                    "has_hold": eligibility.get("has_disciplinary_hold", False),
                    "message": eligibility.get("disciplinary_message")
                }
            },
            "overall_reason": eligibility.get("reason", "Eligible to write exam"),
            "holds": eligibility.get("holds", []),
            "timestamp": datetime.now().isoformat()
        }
    finally:
        await sis_service.close()

@router.get("/exam-schedule")
async def get_exam_schedule(
    student_id: Optional[int] = None,
    module_code: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    venue: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: SystemUser = Depends(require_role(["admin", "invigilator", "system", "student"]))
) -> Dict[str, Any]:
    """
    Get exam schedule from SIS
    Can filter by student, module, date range, or venue
    """
    sis_service = SISService()
    try:
        # Get schedule from SIS
        schedule = await sis_service.get_exam_schedule(
            student_id=student_id,
            module_code=module_code,
            start_date=start_date,
            end_date=end_date,
            venue=venue
        )
        
        # Also get local exam sessions for comparison
        local_query = select(ExamSession)
        
        if module_code:
            local_query = local_query.where(ExamSession.ModuleCode == module_code)
        if venue:
            local_query = local_query.where(ExamSession.VenueLocation.ilike(f"%{venue}%"))
        if start_date:
            local_query = local_query.where(ExamSession.ExamDate >= start_date)
        if end_date:
            local_query = local_query.where(ExamSession.ExamDate <= end_date)
        
        local_result = await db.execute(local_query)
        local_sessions = local_result.scalars().all()
        
        return {
            "sis_schedule": schedule,
            "local_sessions": [
                {
                    "session_id": s.id,
                    "module_code": s.ModuleCode,
                    "module_name": s.ModuleName,
                    "venue": s.VenueLocation,
                    "date": s.ExamDate.isoformat(),
                    "start_time": s.StartTime.strftime("%H:%M"),
                    "end_time": s.EndTime.strftime("%H:%M"),
                    "status": s.Status.value
                }
                for s in local_sessions
            ],
            "total_sis_exams": len(schedule.get("exams", [])),
            "total_local_sessions": len(local_sessions),
            "filters_applied": {
                "student_id": student_id,
                "module_code": module_code,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "venue": venue
            }
        }
    finally:
        await sis_service.close()

# backend/api/v1/endpoints/sis.py - Fix the check_venue_availability endpoint

@router.get("/venue-check")
async def check_venue_availability(
    venue_name: str,
    exam_date: date,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: SystemUser = Depends(require_role(["admin", "invigilator", "system"]))
) -> Dict[str, Any]:
    """
    Check venue availability and capacity from SIS
    Returns: Current bookings, available slots, venue capacity
    """
    sis_service = SISService()
    try:
        # Get venue info from SIS
        venue_info = await sis_service.get_venue_info(venue_name)
        
        # Build query for local exam sessions - FIXED time comparison
        local_query = select(ExamSession).where(
            and_(
                ExamSession.VenueLocation.ilike(f"%{venue_name}%"),
                ExamSession.ExamDate == exam_date
            )
        )
        
        # Fix: Convert string time to time object for comparison
        if start_time:
            # Parse the time string to a time object
            from datetime import time
            start_time_obj = datetime.strptime(start_time, "%H:%M").time()
            local_query = local_query.where(ExamSession.StartTime >= start_time_obj)
        
        if end_time:
            # Parse the time string to a time object
            from datetime import time
            end_time_obj = datetime.strptime(end_time, "%H:%M").time()
            local_query = local_query.where(ExamSession.EndTime <= end_time_obj)
        
        local_result = await db.execute(local_query)
        existing_sessions = local_result.scalars().all()
        
        # Calculate availability
        total_capacity = venue_info.get("capacity", 0)
        booked_capacity = sum(s.RegisteredStudents for s in existing_sessions)
        available_capacity = total_capacity - booked_capacity
        
        return {
            "venue": venue_name,
            "exam_date": exam_date.isoformat(),
            "venue_info": venue_info,
            "availability": {
                "total_capacity": total_capacity,
                "booked_capacity": booked_capacity,
                "available_capacity": available_capacity,
                "is_available": available_capacity > 0,
                "available_percentage": round((available_capacity / total_capacity * 100), 2) if total_capacity > 0 else 0
            },
            "existing_sessions": [
                {
                    "session_id": s.id,
                    "module_code": s.ModuleCode,
                    "start_time": s.StartTime.strftime("%H:%M"),
                    "end_time": s.EndTime.strftime("%H:%M"),
                    "registered_students": s.RegisteredStudents,
                    "status": s.Status.value
                }
                for s in existing_sessions
            ],
            "recommendations": _get_venue_recommendations(available_capacity, total_capacity, existing_sessions)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid time format. Use HH:MM format. Error: {str(e)}")
    finally:
        await sis_service.close()

def _get_venue_recommendations(available: int, total: int, existing_sessions: List) -> List[str]:
    """Generate venue recommendations based on availability"""
    recommendations = []
    
    if available <= 0:
        recommendations.append("Venue is fully booked for this date")
        recommendations.append("Consider alternative venue or date")
    elif available < total * 0.2:
        recommendations.append(f"Only {available} seats available (limited capacity)")
        recommendations.append("Consider booking early or alternative venue")
    else:
        recommendations.append(f"{available} seats available for booking")
    
    if len(existing_sessions) > 0:
        recommendations.append(f"Existing {len(existing_sessions)} session(s) on this date")
    
    return recommendations