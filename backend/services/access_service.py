from services.attendance_service import create_attendance


async def create_access_record(db, student_email, status, venue, exam):
  
    await create_attendance(db, student_email, status, venue, exam)