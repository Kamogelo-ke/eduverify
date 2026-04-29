from models.user import User
from sqlalchemy.future import select
from api.auth_utils import hash_password, verify_password, create_access_token
import secrets


def validate_user(email, role):
    if role == "student" and not email.endswith("@tut4life.ac.za"):
        return False
    if role in ["admin", "invigilator"] and not email.endswith("@tut.ac.za"):
        return False
    return True



async def register_user(db, email, password, role):
    if not validate_user(email, role):
        return "invalid_domain"

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user:
        return None

    new_user = User(
        email=email,
        password=hash_password(password),
        role=role
    )

    db.add(new_user)
    await db.commit()

    return new_user



async def login_user(db, email, password):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password):
        return None

    token = create_access_token({
        "sub": user.email,
        "role": user.role,
        "temp": user.is_temp_password  
    })

    return token



async def create_invigilator(db, email, full_name, staff_number):
    temp_password = secrets.token_hex(4)

    new_user = User(
        email=email,
        password=hash_password(temp_password),
        role="invigilator",
        full_name=full_name,
        staff_number=staff_number,
        is_temp_password=True
    )

    db.add(new_user)
    await db.commit()

    return {
        "email": email,
        "temp_password": temp_password
    }


# 🔥 SET PASSWORD
async def update_password(db, email, new_password):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        return None

    user.password = hash_password(new_password)
    user.is_temp_password = False

    await db.commit()

    return user