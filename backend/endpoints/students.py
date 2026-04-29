"""
Student profile endpoints (admin only unless noted).

POST   /students/register            — create student record
GET    /students/                    — paginated list with search filters
GET    /students/by-number/{number}  — lookup by student number
GET    /students/{id}                — fetch single student
PUT    /students/{id}                — update student details
POST   /students/{id}/consent        — record / withdraw biometric consent
DELETE /students/{id}/face           — erase biometric data (POPIA right to erasure)
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from endpoints.deps import require_admin, require_invigilator_or_admin
from models.models import BiometricProfile, Student, User
from schemas.schemas import (
    StudentCreate, StudentListResponse, StudentResponse, StudentUpdate,
)

router = APIRouter(prefix="/students", tags=["Student Profiles"])


# ── Helper ────────────────────────────────────────────────────────────────────

def _to_response(student: Student) -> StudentResponse:
    return StudentResponse(
        id=student.id,
        student_number=student.student_number,
        full_name=student.full_name,
        email=student.email,
        programme=student.programme,
        year_of_study=student.year_of_study,
        gender=student.gender.value if student.gender else None,
        biometric_consent=student.biometric_consent,
        consent_date=student.consent_date,
        is_active=student.is_active,
        has_biometric_profile=student.biometric_profile is not None,
        created_at=student.created_at,
    )


# ── POST /students/register ───────────────────────────────────────────────────

@router.post("/register", response_model=StudentResponse, status_code=status.HTTP_201_CREATED,
             summary="Register a new student record")
async def register_student(
    body: StudentCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    # Uniqueness checks
    dup_num = await db.execute(select(Student).where(Student.student_number == body.student_number))
    if dup_num.scalar_one_or_none():
        raise HTTPException(status_code=409,
                            detail=f"Student number {body.student_number} already registered")

    dup_email = await db.execute(select(Student).where(Student.email == body.email))
    if dup_email.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email address already in use")

    student = Student(
        student_number=body.student_number,
        full_name=body.full_name,
        email=body.email,
        programme=body.programme,
        year_of_study=body.year_of_study,
        gender=body.gender,
        biometric_consent=body.biometric_consent,
        consent_date=datetime.now(timezone.utc) if body.biometric_consent else None,
    )
    db.add(student)
    await db.commit()
    await db.refresh(student)
    return _to_response(student)


# ── GET /students/ ────────────────────────────────────────────────────────────

@router.get("/", response_model=StudentListResponse, summary="List students with optional filters")
async def list_students(
    search: Optional[str] = Query(None, description="Search name, student number, or email"),
    programme: Optional[str] = Query(None),
    has_biometric: Optional[bool] = Query(None),
    is_active: Optional[bool] = Query(True),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: User = Depends(require_invigilator_or_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Student)

    if is_active is not None:
        stmt = stmt.where(Student.is_active == is_active)
    if programme:
        stmt = stmt.where(Student.programme.ilike(f"%{programme}%"))
    if search:
        term = f"%{search}%"
        stmt = stmt.where(or_(
            Student.full_name.ilike(term),
            Student.student_number.ilike(term),
            Student.email.ilike(term),
        ))
    if has_biometric is True:
        stmt = stmt.join(BiometricProfile)
    elif has_biometric is False:
        stmt = stmt.where(~Student.biometric_profile.has())

    # Count
    count_result = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count_result.scalar_one()

    # Paginate
    stmt = stmt.order_by(Student.full_name).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    students = result.scalars().all()

    return StudentListResponse(
        total=total, page=page, page_size=page_size,
        students=[_to_response(s) for s in students],
    )


# ── GET /students/by-number/{student_number} ─────────────────────────────────

@router.get("/by-number/{student_number}", response_model=StudentResponse,
            summary="Look up student by student number")
async def get_student_by_number(
    student_number: str,
    _: User = Depends(require_invigilator_or_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Student).where(Student.student_number == student_number.upper())
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail=f"Student {student_number} not found")
    return _to_response(student)


# ── GET /students/{id} ────────────────────────────────────────────────────────

@router.get("/{student_id}", response_model=StudentResponse, summary="Get a single student record")
async def get_student(
    student_id: UUID,
    _: User = Depends(require_invigilator_or_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return _to_response(student)


# ── PUT /students/{id} ────────────────────────────────────────────────────────

@router.put("/{student_id}", response_model=StudentResponse, summary="Update student details")
async def update_student(
    student_id: UUID,
    body: StudentUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(student, field, value)
    student.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(student)
    return _to_response(student)


# ── POST /students/{id}/consent ───────────────────────────────────────────────

@router.post("/{student_id}/consent", response_model=StudentResponse,
             summary="Record or withdraw biometric consent (POPIA)")
async def record_consent(
    student_id: UUID,
    consented: bool = Query(..., description="True = consent given, False = consent withdrawn"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    POPIA Section 11: explicit informed consent is required before
    any biometric data may be collected. Withdrawing consent automatically
    deletes the student's biometric profile.
    """
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    student.biometric_consent = consented
    student.consent_date = datetime.now(timezone.utc) if consented else None

    if not consented and student.biometric_profile:
        await db.delete(student.biometric_profile)

    await db.commit()
    await db.refresh(student)
    return _to_response(student)


# ── DELETE /students/{id}/face ────────────────────────────────────────────────

@router.delete("/{student_id}/face", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete biometric data — POPIA right to erasure")
async def delete_biometric(
    student_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Permanently deletes the encrypted embedding.
    The student's academic record is retained.
    """
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if not student.biometric_profile:
        raise HTTPException(status_code=404, detail="No biometric profile found for this student")

    await db.delete(student.biometric_profile)
    student.biometric_consent = False
    student.consent_date = None
    await db.commit()