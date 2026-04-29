
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db

from services.attendance_service import (
    get_all_attendance,
    get_attendance_by_exam
)

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.get("/register")
async def get_register(db: AsyncSession = Depends(get_db)):
    records = await get_all_attendance(db)
    return records


@router.get("/export/{exam}")
async def export_exam(exam: str, db: AsyncSession = Depends(get_db)):
    records = await get_attendance_by_exam(db, exam)
    return records