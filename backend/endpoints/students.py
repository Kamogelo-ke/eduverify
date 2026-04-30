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

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from endpoints.deps import require_admin, require_invigilator_or_admin
from models.biometric_profile import BiometricProfile
from models.student import Student
from models.system_user import SystemUser
from schemas.schemas import (
    StudentCreate, StudentListResponse, StudentResponse, StudentUpdate,
)

router = APIRouter(prefix="/students", tags=["Student Profiles"])


def _split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split(" ", 1)
    return parts[0], parts[1] if len(parts) > 1 else ""


def _to_response(student: Student) -> StudentResponse:
    return StudentResponse(
        id=student.id,
        student_number=student.StudentNumber,
        full_name=student.FullName,
        email=student.Email,
        programme=student.programme,
        year_of_study=student.year_of_study,
        gender=student.gender.value if student.gender else None,
        biometric_consent=student.ConsentGiven,
        consent_date=student.ConsentDate,
        is_active=student.EnrollmentStatus == "Active",
        has_biometric_profile=student.biometric_profile is not None,
        created_at=student.CreatedAt,
    )


# ── POST /students/register ───────────────────────────────────────────────────

@router.post("/register", response_model=StudentResponse, status_code=status.HTTP_201_CREATED,
             summary="Register a new student record")
async def register_student(
    body: StudentCreate,
    current_user: SystemUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    dup_num = await db.execute(select(Student).where(Student.StudentNumber == body.student_number))
    if dup_num.scalar_one_or_none():
        raise HTTPException(status_code=409,
                            detail=f"Student number {body.student_number} already registered")

    dup_email = await db.execute(select(Student).where(Student.Email == body.email))
    if dup_email.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email address already in use")

    first_name, last_name = _split_name(body.full_name)
    student = Student(
        StudentNumber=body.student_number,
        FirstName=first_name,
        LastName=last_name,
        Email=body.email,
        programme=body.programme,
        year_of_study=body.year_of_study,
        gender=body.gender,
        ConsentGiven=body.biometric_consent,
        ConsentDate=datetime.utcnow() if body.biometric_consent else None,
    )
    db.add(student)
    await db.commit()
    await db.refresh(student)
    # Re-fetch with eager load so biometric_profile is available without lazy IO
    result = await db.execute(
        select(Student).options(selectinload(Student.biometric_profile))
        .where(Student.id == student.id)
    )
    student = result.scalar_one()
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
    _: SystemUser = Depends(require_invigilator_or_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Student).options(selectinload(Student.biometric_profile))

    if is_active is not None:
        enrollment = "Active" if is_active else "Inactive"
        stmt = stmt.where(Student.EnrollmentStatus == enrollment)
    if programme:
        stmt = stmt.where(Student.programme.ilike(f"%{programme}%"))
    if search:
        term = f"%{search}%"
        stmt = stmt.where(or_(
            Student.FirstName.ilike(term),
            Student.LastName.ilike(term),
            Student.StudentNumber.ilike(term),
            Student.Email.ilike(term),
        ))
    if has_biometric is True:
        stmt = stmt.join(BiometricProfile)
    elif has_biometric is False:
        stmt = stmt.where(~Student.biometric_profile.has())

    count_result = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count_result.scalar_one()

    stmt = stmt.order_by(Student.FirstName, Student.LastName).offset((page - 1) * page_size).limit(page_size)
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
    _: SystemUser = Depends(require_invigilator_or_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Student).options(selectinload(Student.biometric_profile))
        .where(Student.StudentNumber == student_number.upper())
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail=f"Student {student_number} not found")
    return _to_response(student)


# ── GET /students/{id} ────────────────────────────────────────────────────────

@router.get("/{student_id}", response_model=StudentResponse, summary="Get a single student record")
async def get_student(
    student_id: int,
    _: SystemUser = Depends(require_invigilator_or_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Student).options(selectinload(Student.biometric_profile))
        .where(Student.id == student_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return _to_response(student)


# ── PUT /students/{id} ────────────────────────────────────────────────────────

@router.put("/{student_id}", response_model=StudentResponse, summary="Update student details")
async def update_student(
    student_id: int,
    body: StudentUpdate,
    current_user: SystemUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Student).options(selectinload(Student.biometric_profile))
        .where(Student.id == student_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if body.full_name is not None:
        student.FirstName, student.LastName = _split_name(body.full_name)
    if body.email is not None:
        student.Email = body.email
    if body.programme is not None:
        student.programme = body.programme
    if body.year_of_study is not None:
        student.year_of_study = body.year_of_study
    if body.gender is not None:
        student.gender = body.gender
    if body.is_active is not None:
        student.EnrollmentStatus = "Active" if body.is_active else "Inactive"
    student.UpdatedAt = datetime.utcnow()

    await db.commit()
    # Re-fetch to keep biometric_profile loaded
    result = await db.execute(
        select(Student).options(selectinload(Student.biometric_profile))
        .where(Student.id == student_id)
    )
    student = result.scalar_one()
    return _to_response(student)


# ── POST /students/{id}/consent ───────────────────────────────────────────────

@router.post("/{student_id}/consent", response_model=StudentResponse,
             summary="Record or withdraw biometric consent (POPIA)")
async def record_consent(
    student_id: int,
    consented: bool = Query(..., description="True = consent given, False = consent withdrawn"),
    current_user: SystemUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Student).options(selectinload(Student.biometric_profile))
        .where(Student.id == student_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    student.ConsentGiven = consented
    student.ConsentDate = datetime.utcnow() if consented else None

    if not consented and student.biometric_profile:
        await db.delete(student.biometric_profile)

    await db.commit()
    result = await db.execute(
        select(Student).options(selectinload(Student.biometric_profile))
        .where(Student.id == student_id)
    )
    student = result.scalar_one()
    return _to_response(student)


# ── DELETE /students/{id}/face ────────────────────────────────────────────────

@router.delete("/{student_id}/face", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete biometric data — POPIA right to erasure")
async def delete_biometric(
    student_id: int,
    current_user: SystemUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Student).options(selectinload(Student.biometric_profile))
        .where(Student.id == student_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if not student.biometric_profile:
        raise HTTPException(status_code=404, detail="No biometric profile found for this student")

    await db.delete(student.biometric_profile)
    student.ConsentGiven = False
    student.ConsentDate = None
    await db.commit()
