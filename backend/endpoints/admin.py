"""
Admin dashboard endpoints.

GET  /admin/stats                          — live system metrics
GET  /admin/venues                         — active exam venues
POST /admin/exam-session                   — create exam session
GET  /admin/exam-sessions                  — list exam sessions
GET  /admin/reports/attempts               — paginated audit log
GET  /admin/reports/attendance/{id}        — digital attendance register
POST /admin/users                          — create user account (admin only)
GET  /admin/users                          — list all system users (admin only)
"""

import logging
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.security import hash_password, generate_temp_password
from core.email import send_temporary_password_email
from database import get_db
from endpoints.deps import require_admin, require_invigilator_or_admin
from models.biometric_profile import BiometricProfile
from models.exam_session import ExamSession, SessionStatus
from models.student import Student
from models.system_user import SystemUser, UserRole
from models.verification_attempt import VerificationAttempt, VerificationOutcome
from schemas.schemas import (
    AttendanceRegister, AttendanceRegisterEntry,
    ExamSessionCreate, ExamSessionResponse,
    SystemStats, UserCreate, UserResponse,
)

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])

logger = logging.getLogger(__name__)


def _exam_session_to_response(s: ExamSession, total_attempts: int = 0, granted_count: int = 0) -> ExamSessionResponse:
    """Map ExamSession ORM object to ExamSessionResponse schema."""
    scheduled_start = datetime.combine(s.ExamDate, s.StartTime) if s.ExamDate and s.StartTime else None
    scheduled_end = datetime.combine(s.ExamDate, s.EndTime) if s.ExamDate and s.EndTime else None
    return ExamSessionResponse(
        id=s.id,
        module_code=s.ModuleCode,
        module_name=s.ModuleName,
        venue=s.VenueLocation,
        campus="",
        scheduled_start=scheduled_start,
        scheduled_end=scheduled_end,
        created_at=s.CreatedAt,
        total_attempts=total_attempts,
        granted_count=granted_count,
    )


def _user_to_response(u: SystemUser) -> UserResponse:
    return UserResponse(
        id=u.id,
        email=u.Email,
        full_name=u.FullName,
        role=u.Role.value,
        is_active=u.IsActive,
        created_at=u.CreatedAt,
        last_login=u.LastLoginAt,
    )


def _split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split(" ", 1)
    return parts[0], parts[1] if len(parts) > 1 else ""


# ── GET /admin/stats ──────────────────────────────────────────────────────────

@router.get("/stats", response_model=SystemStats, summary="Live dashboard metrics")
async def get_system_stats(
    _: SystemUser = Depends(require_invigilator_or_admin),
    db: AsyncSession = Depends(get_db),
):
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    total_students = (await db.execute(
        select(func.count(Student.id)).where(Student.EnrollmentStatus == "Active")
    )).scalar_one()

    enrolled_students = (await db.execute(
        select(func.count(BiometricProfile.id))
    )).scalar_one()

    todays_res = await db.execute(
        select(VerificationAttempt).where(VerificationAttempt.attempted_at >= today_start)
    )
    todays = todays_res.scalars().all()

    granted_today = sum(1 for a in todays if a.outcome == VerificationOutcome.granted)
    denied_today = sum(1 for a in todays if a.outcome not in (
        VerificationOutcome.granted, VerificationOutcome.overridden))
    overrides_today = sum(1 for a in todays if a.was_overridden)

    total_today = len(todays)
    false_acceptances = sum(
        1 for a in todays
        if a.face_similarity_score and a.face_similarity_score >= 0.65
        and a.outcome == VerificationOutcome.denied_eligibility
    )
    false_rejections = sum(
        1 for a in todays
        if a.outcome == VerificationOutcome.denied_identity and a.was_overridden
    )
    far = round(false_acceptances / total_today, 5) if total_today else 0.0
    frr = round(false_rejections / total_today, 5) if total_today else 0.0

    times = [a.processing_time_ms for a in todays if a.processing_time_ms]
    avg_ms = round(sum(times) / len(times)) if times else 0

    active_sessions = (await db.execute(
        select(func.count(ExamSession.id)).where(ExamSession.Status == SessionStatus.ACTIVE)
    )).scalar_one()

    return SystemStats(
        total_students=total_students,
        enrolled_students=enrolled_students,
        total_attempts_today=total_today,
        granted_today=granted_today,
        denied_today=denied_today,
        overrides_today=overrides_today,
        avg_processing_time_ms=avg_ms,
        false_acceptance_rate=far,
        false_rejection_rate=frr,
        active_exam_sessions=active_sessions,
    )


# ── GET /admin/venues ─────────────────────────────────────────────────────────

@router.get("/venues", summary="List exam venues with upcoming sessions")
async def list_venues(
    _: SystemUser = Depends(require_invigilator_or_admin),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    result = await db.execute(
        select(ExamSession)
        .where(ExamSession.ExamDate >= today)
        .order_by(ExamSession.ExamDate, ExamSession.StartTime)
    )
    sessions = result.scalars().all()
    venues: dict = {}
    for s in sessions:
        key = s.VenueLocation
        if key not in venues:
            venues[key] = {"venue": s.VenueLocation, "campus": "", "upcoming_sessions": []}
        venues[key]["upcoming_sessions"].append({
            "session_id": str(s.id),
            "module_code": s.ModuleCode,
            "module_name": s.ModuleName,
            "scheduled_start": datetime.combine(s.ExamDate, s.StartTime).isoformat() if s.ExamDate and s.StartTime else None,
            "scheduled_end": datetime.combine(s.ExamDate, s.EndTime).isoformat() if s.ExamDate and s.EndTime else None,
        })
    return list(venues.values())


# ── POST /admin/exam-session ──────────────────────────────────────────────────

@router.post("/exam-session", response_model=ExamSessionResponse, status_code=201,
             summary="Create a new exam session")
async def create_exam_session(
    body: ExamSessionCreate,
    current_user: SystemUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    exam_date = body.scheduled_start.date()
    start_time = body.scheduled_start.time()
    end_time = body.scheduled_end.time()

    # Check for venue/time clash on same date
    clash_res = await db.execute(
        select(ExamSession).where(
            ExamSession.VenueLocation == body.venue,
            ExamSession.ExamDate == exam_date,
            ExamSession.StartTime < end_time,
            ExamSession.EndTime > start_time,
        )
    )
    clash = clash_res.scalar_one_or_none()
    if clash:
        raise HTTPException(
            status_code=409,
            detail=f"Venue '{body.venue}' is already booked for {clash.ModuleCode} during that time",
        )

    session = ExamSession(
        ModuleCode=body.module_code.upper(),
        ModuleName=body.module_name,
        VenueLocation=body.venue,
        ExamDate=exam_date,
        StartTime=start_time,
        EndTime=end_time,
        CreatedBy=current_user.id,
        Status=SessionStatus.SCHEDULED,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return _exam_session_to_response(session)


# ── GET /admin/exam-sessions ──────────────────────────────────────────────────

@router.get("/exam-sessions", response_model=list[ExamSessionResponse],
            summary="List exam sessions")
async def list_exam_sessions(
    upcoming_only: bool = Query(True),
    venue: Optional[str] = Query(None),
    module_code: Optional[str] = Query(None),
    _: SystemUser = Depends(require_invigilator_or_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ExamSession).options(selectinload(ExamSession.attempts))
    if upcoming_only:
        stmt = stmt.where(ExamSession.ExamDate >= date.today())
    if venue:
        stmt = stmt.where(ExamSession.VenueLocation.ilike(f"%{venue}%"))
    if module_code:
        stmt = stmt.where(ExamSession.ModuleCode.ilike(f"%{module_code}%"))

    result = await db.execute(stmt.order_by(ExamSession.ExamDate, ExamSession.StartTime))
    sessions = result.scalars().all()

    output = []
    for s in sessions:
        granted = sum(1 for a in s.attempts if a.outcome in (
            VerificationOutcome.granted, VerificationOutcome.overridden))
        output.append(_exam_session_to_response(s, total_attempts=len(s.attempts), granted_count=granted))
    return output


# ── GET /admin/reports/attempts ───────────────────────────────────────────────

@router.get("/reports/attempts", summary="Paginated audit log of all verification attempts")
async def get_attempt_log(
    outcome: Optional[str] = Query(None),
    exam_session_id: Optional[int] = Query(None),
    student_number: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _: SystemUser = Depends(require_invigilator_or_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(VerificationAttempt)
        .options(selectinload(VerificationAttempt.student), selectinload(VerificationAttempt.exam_session))
        .outerjoin(Student, VerificationAttempt.student_id == Student.id)
        .outerjoin(ExamSession, VerificationAttempt.exam_session_id == ExamSession.id)
    )
    if outcome:
        stmt = stmt.where(VerificationAttempt.outcome == outcome)
    if exam_session_id:
        stmt = stmt.where(VerificationAttempt.exam_session_id == exam_session_id)
    if student_number:
        stmt = stmt.where(Student.StudentNumber == student_number.upper())

    count_res = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count_res.scalar_one()

    stmt = stmt.order_by(VerificationAttempt.attempted_at.desc()).offset(
        (page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    attempts = result.scalars().all()

    entries = [{
        "attempt_id": str(a.id),
        "student_number": a.student.StudentNumber if a.student else None,
        "student_name": a.student.FullName if a.student else None,
        "exam_session": a.exam_session.ModuleCode if a.exam_session else None,
        "venue": a.exam_session.VenueLocation if a.exam_session else None,
        "outcome": a.outcome.value,
        "face_similarity_score": a.face_similarity_score,
        "liveness_score": a.liveness_score,
        "processing_time_ms": a.processing_time_ms,
        "was_overridden": a.was_overridden,
        "attempted_at": a.attempted_at.isoformat(),
    } for a in attempts]

    return {"total": total, "page": page, "page_size": page_size, "attempts": entries}


# ── GET /admin/reports/attendance/{session_id} ────────────────────────────────

@router.get("/reports/attendance/{session_id}", response_model=AttendanceRegister,
            summary="Digital attendance register for an exam session")
async def get_attendance_register(
    session_id: int,
    _: SystemUser = Depends(require_invigilator_or_admin),
    db: AsyncSession = Depends(get_db),
):
    sess_res = await db.execute(select(ExamSession).where(ExamSession.id == session_id))
    session = sess_res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Exam session not found")

    att_res = await db.execute(
        select(VerificationAttempt)
        .options(selectinload(VerificationAttempt.student))
        .where(VerificationAttempt.exam_session_id == session_id)
        .order_by(VerificationAttempt.attempted_at)
    )
    attempts = att_res.scalars().all()

    attended_outcomes = {VerificationOutcome.granted, VerificationOutcome.overridden}
    attended = [a for a in attempts if a.outcome in attended_outcomes]

    entries = [
        AttendanceRegisterEntry(
            student_number=a.student.StudentNumber if a.student else "UNKNOWN",
            student_name=a.student.FullName if a.student else "Unknown",
            outcome=a.outcome.value,
            attempted_at=a.attempted_at,
            was_overridden=a.was_overridden,
        )
        for a in attended
    ]

    scheduled_start = datetime.combine(session.ExamDate, session.StartTime) if session.ExamDate and session.StartTime else None

    return AttendanceRegister(
        exam_session_id=session.id,
        module_code=session.ModuleCode,
        module_name=session.ModuleName,
        venue=session.VenueLocation,
        scheduled_start=scheduled_start,
        total_registered=len(attempts),
        attended=len(attended),
        entries=entries,
    )


# ── POST /admin/users ─────────────────────────────────────────────────────────

@router.post("/users", response_model=UserResponse, status_code=201,
             summary="Create an admin or invigilator account")
async def create_user(
    body: UserCreate,
    current_user: SystemUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    dup = await db.execute(select(SystemUser).where(SystemUser.Email == body.email))
    if dup.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    valid_roles = [r.value for r in UserRole]
    if body.role not in valid_roles:
        raise HTTPException(status_code=422,
                            detail=f"Invalid role. Must be one of: {valid_roles}")

    first_name, last_name = _split_name(body.full_name)
    temp_password = generate_temp_password()

    user = SystemUser(
        Username=body.email,
        Email=body.email,
        FirstName=first_name,
        LastName=last_name,
        PasswordHash=hash_password(temp_password),
        Role=UserRole(body.role),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    email_sent = await send_temporary_password_email(
        full_name=user.FullName,
        email=user.Email,
        temp_password=temp_password,
    )
    if not email_sent:
        logger.warning("Account created for %s but email delivery failed", user.Email)

    return _user_to_response(user)


# ── GET /admin/users ──────────────────────────────────────────────────────────

@router.get("/users", response_model=list[UserResponse], summary="List all system users")
async def list_users(
    role: Optional[str] = Query(None),
    _: SystemUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(SystemUser)
    if role:
        stmt = stmt.where(SystemUser.Role == role)
    result = await db.execute(stmt.order_by(SystemUser.FirstName, SystemUser.LastName))
    users = result.scalars().all()
    return [_user_to_response(u) for u in users]
