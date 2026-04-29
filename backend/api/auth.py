
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from api.dependencies import get_current_user
from api.auth_utils import create_access_token

from services.auth_service import (
    register_user,
    login_user,
    create_invigilator,
    update_password
)

router = APIRouter(prefix="/auth", tags=["Auth"])



@router.post("/register")
async def register(
    email: str,
    password: str,
    role: str = "invigilator",
    db: AsyncSession = Depends(get_db)
):
    user = await register_user(db, email, password, role)

    if user == "invalid_domain":
        raise HTTPException(status_code=400, detail="Invalid email domain")

    if not user:
        raise HTTPException(status_code=400, detail="User exists")

    return {"message": f"{role} created"}



@router.post("/login")
async def login(email: str, password: str, db: AsyncSession = Depends(get_db)):
    token = await login_user(db, email, password)

    if not token:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"access_token": token}



@router.post("/create-invigilator")
async def create_invigilator_api(
    email: str,
    full_name: str,
    staff_number: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can create invigilator")

    result = await create_invigilator(db, email, full_name, staff_number)

    return {
        "message": "Invigilator created",
        "credentials": result
    }



@router.post("/set-password")
async def set_password(
    new_password: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    updated = await update_password(db, user["sub"], new_password)

    if not updated:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "Password updated"}



@router.get("/me")
async def get_me(user=Depends(get_current_user)):
    return {
        "email": user["sub"],
        "role": user["role"],
        "temp_password": user.get("temp", False)
    }



@router.post("/logout")
async def logout():
    return {"message": "Logged out"}


# 🔹 REFRESH TOKEN
@router.post("/refresh-token")
async def refresh_token(user=Depends(get_current_user)):
    token = create_access_token({
        "sub": user["sub"],
        "role": user["role"],
        "temp": user.get("temp", False)
    })
    return {"access_token": token}