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

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import hash_password, generate_temp_password
from core.email import send_temporary_password_email
from database import get_db
from endpoints.deps import require_admin, require_invigilator_or_admin
from models.models import (
    BiometricProfile, ExamSession, Student, User, UserRole,
    VerificationAttempt, VerificationOutcome,
)
from schemas.schemas import (
    AttendanceRegister, AttendanceRegisterEntry,
    ExamSessionCreate, ExamSessionResponse,
    SystemStats, UserCreate, UserResponse,
)

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


# ── GET /admin/stats ──────────────────────────────────────────────────────────

@router.get("/stats", response_model=SystemStats,
            summary="Live dashboard metrics")
async def get_system_stats(
    _: User = Depends(require_invigilator_or_admin),
    db: AsyncSession = Depends(get_db),
):
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    total_students = (await db.execute(
        select(func.count(Student.id)).where(Student.is_active == True)
    )).scalar_one()

    enrolled_students = (await db.execute(
        select(func.count(BiometricProfile.id))
    )).scalar_one()

    todays_res = await db.execute(
        select(VerificationAttempt).where(
            VerificationAttempt.attempted_at >= today_start
        )
    )
    todays = todays_res.scalars().all()

    granted_today = sum(1 for a in todays if a.outcome == VerificationOutcome.granted)
    denied_today = sum(1 for a in todays if a.outcome not in (
        VerificationOutcome.granted, VerificationOutcome.overridden))
    overrides_today = sum(1 for a in todays if a.was_overridden)

    false_acceptances = sum(
        1 for a in todays
        if a.face_similarity_score and a.face_similarity_score >= 0.65
        and a.outcome == VerificationOutcome.denied_eligibility
    )
    false_rejections = sum(
        1 for a in todays
        if a.outcome == VerificationOutcome.denied_identity and a.was_overridden
    )

    total_today = len(todays)
    far = round(false_acceptances / total_today, 5) if total_today else 0.0
    frr = round(false_rejections / total_today, 5) if total_today else 0.0

    times = [a.processing_time_ms for a in todays if a.processing_time_ms]
    avg_ms = round(sum(times) / len(times)) if times else 0

    now = datetime.now(timezone.utc)
    active_sessions = (await db.execute(
        select(func.count(ExamSession.id)).where(
            ExamSession.scheduled_start <= now,
            ExamSession.scheduled_end >= now,
        )
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
    _: User = Depends(require_invigilator_or_admin),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(ExamSession)
        .where(ExamSession.scheduled_end >= now)
        .order_by(ExamSession.scheduled_start)
    )
    sessions = result.scalars().all()
    venues: dict = {}
    for s in sessions:
        if s.venue not in venues:
            venues[s.venue] = {"venue": s.venue, "campus": s.campus, "upcoming_sessions": []}
        venues[s.venue]["upcoming_sessions"].append({
            "session_id": str(s.id),
            "module_code": s.module_code,
            "module_name": s.module_name,
            "scheduled_start": s.scheduled_start.isoformat(),
            "scheduled_end": s.scheduled_end.isoformat(),
        })
    return list(venues.values())


# ── POST /admin/exam-session ──────────────────────────────────────────────────

@router.post("/exam-session", response_model=ExamSessionResponse, status_code=201,
             summary="Create a new exam session")
async def create_exam_session(
    body: ExamSessionCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    # Check for venue/time clash
    clash_res = await db.execute(
        select(ExamSession).where(
            ExamSession.venue == body.venue,
            ExamSession.scheduled_start < body.scheduled_end,
            ExamSession.scheduled_end > body.scheduled_start,
        )
    )
    clash = clash_res.scalar_one_or_none()
    if clash:
        raise HTTPException(
            status_code=409,
            detail=f"Venue {body.venue} is already booked for {clash.module_code} during that time",
        )

    session = ExamSession(
        module_code=body.module_code.upper(),
        module_name=body.module_name,
        venue=body.venue,
        campus=body.campus,
        scheduled_start=body.scheduled_start,
        scheduled_end=body.scheduled_end,
        created_by=current_user.id,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return ExamSessionResponse(
        id=session.id,
        module_code=session.module_code,
        module_name=session.module_name,
        venue=session.venue,
        campus=session.campus,
        scheduled_start=session.scheduled_start,
        scheduled_end=session.scheduled_end,
        created_at=session.created_at,
    )


# ── GET /admin/exam-sessions ──────────────────────────────────────────────────

@router.get("/exam-sessions", response_model=list[ExamSessionResponse],
            summary="List exam sessions")
async def list_exam_sessions(
    upcoming_only: bool = Query(True),
    venue: Optional[str] = Query(None),
    module_code: Optional[str] = Query(None),
    _: User = Depends(require_invigilator_or_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ExamSession)
    if upcoming_only:
        stmt = stmt.where(ExamSession.scheduled_end >= datetime.now(timezone.utc))
    if venue:
        stmt = stmt.where(ExamSession.venue.ilike(f"%{venue}%"))
    if module_code:
        stmt = stmt.where(ExamSession.module_code.ilike(f"%{module_code}%"))

    result = await db.execute(stmt.order_by(ExamSession.scheduled_start))
    sessions = result.scalars().all()

    output = []
    for s in sessions:
        granted = sum(1 for a in s.attempts if a.outcome in (
            VerificationOutcome.granted, VerificationOutcome.overridden))
        output.append(ExamSessionResponse(
            id=s.id,
            module_code=s.module_code,
            module_name=s.module_name,
            venue=s.venue,
            campus=s.campus,
            scheduled_start=s.scheduled_start,
            scheduled_end=s.scheduled_end,
            created_at=s.created_at,
            total_attempts=len(s.attempts),
            granted_count=granted,
        ))
    return output


# ── GET /admin/reports/attempts ───────────────────────────────────────────────

@router.get("/reports/attempts", summary="Paginated audit log of all verification attempts")
async def get_attempt_log(
    outcome: Optional[str] = Query(None),
    exam_session_id: Optional[UUID] = Query(None),
    student_number: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _: User = Depends(require_invigilator_or_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(VerificationAttempt)
        .outerjoin(Student)
        .outerjoin(ExamSession)
    )
    if outcome:
        stmt = stmt.where(VerificationAttempt.outcome == outcome)
    if exam_session_id:
        stmt = stmt.where(VerificationAttempt.exam_session_id == exam_session_id)
    if student_number:
        stmt = stmt.where(Student.student_number == student_number.upper())

    count_res = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count_res.scalar_one()

    stmt = stmt.order_by(VerificationAttempt.attempted_at.desc()).offset(
        (page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    attempts = result.scalars().all()

    entries = [{
        "attempt_id": str(a.id),
        "student_number": a.student.student_number if a.student else None,
        "student_name": a.student.full_name if a.student else None,
        "exam_session": a.exam_session.module_code if a.exam_session else None,
        "venue": a.exam_session.venue if a.exam_session else None,
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
    session_id: UUID,
    _: User = Depends(require_invigilator_or_admin),
    db: AsyncSession = Depends(get_db),
):
    sess_res = await db.execute(
        select(ExamSession).where(ExamSession.id == session_id)
    )
    session = sess_res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Exam session not found")

    att_res = await db.execute(
        select(VerificationAttempt)
        .where(VerificationAttempt.exam_session_id == session_id)
        .order_by(VerificationAttempt.attempted_at)
    )
    attempts = att_res.scalars().all()

    attended_outcomes = {VerificationOutcome.granted, VerificationOutcome.overridden}
    attended = [a for a in attempts if a.outcome in attended_outcomes]

    entries = [
        AttendanceRegisterEntry(
            student_number=a.student.student_number if a.student else "UNKNOWN",
            student_name=a.student.full_name if a.student else "Unknown",
            outcome=a.outcome.value,
            attempted_at=a.attempted_at,
            was_overridden=a.was_overridden,
        )
        for a in attended
    ]

    return AttendanceRegister(
        exam_session_id=session.id,
        module_code=session.module_code,
        module_name=session.module_name,
        venue=session.venue,
        scheduled_start=session.scheduled_start,
        total_registered=len(attempts),
        attended=len(attended),
        entries=entries,
    )


# ── POST /admin/users ─────────────────────────────────────────────────────────

@router.post("/users", response_model=UserResponse, status_code=201,
             summary="Create an admin or invigilator account")
async def create_user(
    body: UserCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    dup = await db.execute(select(User).where(User.email == body.email))
    if dup.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")
    if body.role not in [r.value for r in UserRole]:
        raise HTTPException(status_code=422,
                            detail=f"Invalid role. Must be one of: {[r.value for r in UserRole]}")

    # Generate a secure temporary password — ignore whatever the admin typed
    temp_password = generate_temp_password()

    user = User(
        email=body.email,
        full_name=body.full_name,
        hashed_password=hash_password(temp_password),
        role=UserRole(body.role),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Send the temporary password to the new user's email address
    email_sent = await send_temporary_password_email(
        full_name=user.full_name,
        email=user.email,
        temp_password=temp_password,
    )

    if not email_sent:
        # Log a warning but do not fail the request — account is created
        import logging
        logging.getLogger(__name__).warning(
            "Account created for %s but email delivery failed", user.email
        )

    return user


# ── GET /admin/users ──────────────────────────────────────────────────────────

@router.get("/users", response_model=list[UserResponse],
            summary="List all system users")
async def list_users(
    role: Optional[str] = Query(None),
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(User)
    if role:
        stmt = stmt.where(User.role == role)
    result = await db.execute(stmt.order_by(User.full_name))
    return result.scalars().all()