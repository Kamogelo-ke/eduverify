"""
One-time admin seed script.
Creates the first admin user so you can log in to Swagger UI.

Run from inside the backend/ folder:
    python seed_admin.py
"""

import asyncio
import sys
import os

# Ensure the backend folder is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uuid
from sqlalchemy import select
from database import session_local, init_db
from models.system_user import SystemUser, UserRole
from core.security import hash_password


async def seed():
    # Create tables if they don't exist yet
    await init_db()

    async with session_local() as db:
        # Check if admin already exists
        result = await db.execute(
            select(SystemUser).where(SystemUser.email == "admin@tut.ac.za")
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"Admin already exists: {existing.email}")
            return

        user = SystemUser(
            id=uuid.uuid4(),
            email="admin@tut.ac.za",
            full_name="Admin User",
            hashed_password=hash_password("Admin123!"),
            role=UserRole.admin,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        print(f"Admin created successfully: {user.email}")
        print("Login credentials:")
        print("  Email   : admin@tut.ac.za")
        print("  Password: Admin123!")


if __name__ == "__main__":
    asyncio.run(seed())