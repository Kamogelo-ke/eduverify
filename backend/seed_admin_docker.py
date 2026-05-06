import asyncio
from database import engine, init_db
from core.security import hash_password
from sqlalchemy import text


async def seed():
    await init_db()
    pwd = hash_password("Admin123!")
    async with engine.begin() as conn:
        result = await conn.execute(
            text('SELECT id FROM system_users WHERE "Email" = :email'),
            {"email": "admin@tut.ac.za"}
        )
        existing = result.fetchone()
        if existing:
            print("Admin already exists")
            return
        await conn.execute(
            text("""
                INSERT INTO system_users
                ("Username", "Email", "PasswordHash", "FirstName", "LastName", "Role", "IsActive")
                VALUES (:username, :email, :pwd, :first, :last, :role, :active)
            """),
            {
                "username": "admin",
                "email": "admin@tut.ac.za",
                "pwd": pwd,
                "first": "Admin",
                "last": "User",
                "role": "ADMIN",
                "active": True,
            }
        )
        print("Admin created: admin@tut.ac.za / Admin123!")


asyncio.run(seed())