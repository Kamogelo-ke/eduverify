from models.attendance import Attendance
from sqlalchemy.future import select


async def create_attendance(db, student_email, status, venue, exam):
    record = Attendance(
        student_email=student_email,
        status=status,
        venue=venue,
        exam=exam
    )
    db.add(record)
    await db.commit()


async def get_all_attendance(db):
    result = await db.execute(select(Attendance))
    return result.scalars().all()


async def get_attendance_by_exam(db, exam):
    result = await db.execute(
        select(Attendance).where(Attendance.exam == exam)
    )
    return result.scalars().all()


async def get_student_status(db, email):
    result = await db.execute(
        select(Attendance).where(Attendance.student_email == email)
    )
    return result.scalars().all()