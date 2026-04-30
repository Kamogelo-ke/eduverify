from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from models.attendence_register import AttendanceRegister

# ✅ CREATE ATTENDANCE
async def create_attendance(
    db: AsyncSession,
    student_id: int,
    session_id: int,
    status: str,
    notes: str = None
):
    record = AttendanceRegister(
        student_id=student_id,
        session_id=session_id,
        Status=status,
        MarkedAt=datetime.utcnow(),
        Notes=notes
    )

    db.add(record)
    await db.commit()
    await db.refresh(record)

    return record

# ✅ GET ALL ATTENDANCE
async def get_all_attendance(db: AsyncSession):
    result = await db.execute(select(AttendanceRegister))
    return result.scalars().all()

# ✅ GET BY SESSION
async def get_attendance_by_session(db: AsyncSession, session_id: int):
    result = await db.execute(
        select(AttendanceRegister).where(
            AttendanceRegister.session_id == session_id
        )
    )
    return result.scalars().all()

# ✅ GET BY STUDENT
async def get_student_attendance(db: AsyncSession, student_id: int):
    result = await db.execute(
        select(AttendanceRegister).where(
            AttendanceRegister.student_id == student_id
        )
    )
    return result.scalars().all()



async def get_student_status(db, student_id: int):
    result = await db.execute(
        select(AttendanceRegister).where(
            AttendanceRegister.student_id == student_id
        )
    )
    return result.scalars().all()

