import asyncio
from database import engine
from core.security import hash_password
from sqlalchemy import text

async def reset():
    pwd = hash_password("Admin123!")
    async with engine.begin() as conn:
        await conn.execute(
            text('UPDATE system_users SET "PasswordHash" = :pwd WHERE "Email" = :email'),
            {"pwd": pwd, "email": "admin@tut.ac.za"}
        )
    print("Admin password reset successfully — use Admin123! to login")

asyncio.run(reset())
