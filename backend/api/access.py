from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from api.dependencies import get_current_user

from services.access_service import create_access_record
from services.attendance_service import get_student_status

router = APIRouter(prefix="/access", tags=["Access control"])


def validate_student_email(email: str):
    if not email.endswith("@tut4life.ac.za"):
        raise HTTPException(status_code=400, detail="Invalid student email")


@router.post("/grant")
async def grant_access(
    student_email: str,
    venue: str,
    exam: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    if user["role"] not in ["admin", "system"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    validate_student_email(student_email)

    await create_access_record(db, student_email, "present", venue, exam)

    return {"message": "Granted"}


@router.post("/deny")
async def deny_access(
    student_email: str,
    venue: str,
    exam: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    validate_student_email(student_email)

    await create_access_record(db, student_email, "denied", venue, exam)

    return {"message": "Denied"}


@router.post("/override")
async def override_access(
    student_email: str,
    venue: str,
    exam: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    if user["role"] != "invigilator":
        raise HTTPException(status_code=403, detail="Only invigilator")

    validate_student_email(student_email)

    await create_access_record(db, student_email, "override", venue, exam)

    return {"message": "Override Granted"}


@router.get("/status/{email}")
async def check_status(email: str, db: AsyncSession = Depends(get_db)):
    records = await get_student_status(db, email)
    return {"records": records}