from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db

from services.attendance_service import (
    get_all_attendance,
    get_attendance_by_session,
    get_student_attendance,
    create_attendance
)

router = APIRouter(prefix="/attendance", tags=["Attendance"])

# ✅ GET ALL
@router.get("/")
async def get_register(db: AsyncSession = Depends(get_db)):
    return await get_all_attendance(db)

# ✅ GET BY SESSION
@router.get("/session/{session_id}")
async def get_by_session(session_id: int, db: AsyncSession = Depends(get_db)):
    return await get_attendance_by_session(db, session_id)

# ✅ GET BY STUDENT
@router.get("/student/{student_id}")
async def get_by_student(student_id: int, db: AsyncSession = Depends(get_db)):
    return await get_student_attendance(db, student_id)

# ✅ CREATE ATTENDANCE
@router.post("/create")
async def add_attendance(
    student_id: int,
    session_id: int,
    status: str,
    notes: str = None,
    db: AsyncSession = Depends(get_db)
):
    return await create_attendance(
        db,
        student_id,
        session_id,
        status,
        notes
    )

