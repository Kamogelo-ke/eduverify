# manage.py
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

async def create_admin():
    from database import session_local
    from models.system_user import SystemUser, UserRole
    
    async with session_local() as db:
        # Check if admin already exists
        from sqlalchemy import select
        query = select(SystemUser).where(SystemUser.Username == "admin")
        result = await db.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            print("⚠️  Admin user already exists!")
            return
        
        admin = SystemUser(
            Username="admin",
            Email="admin@edverify.com",
            FirstName="System",
            LastName="Administrator",
            Role=UserRole.ADMIN,
            IsActive=True
        )
        admin.set_password("Admin123!")
        db.add(admin)
        await db.commit()
        print("✅ Admin user created successfully!")
        print("📝 Username: admin")
        print("🔑 Password: Admin123!")
        print("⚠️  Please change this password after first login!")

async def create_invigilator():
    from database import session_local
    from models.system_user import SystemUser, UserRole
    
    async with session_local() as db:
        invigilator = SystemUser(
            Username="invigilator1",
            Email="invigilator@edverify.com",
            FirstName="John",
            LastName="Doe",
            Role=UserRole.INVIGILATOR,
            IsActive=True
        )
        invigilator.set_password("Invig123!")
        db.add(invigilator)
        await db.commit()
        print("✅ Invigilator user created successfully!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "create_admin":
            asyncio.run(create_admin())
        elif command == "create_invigilator":
            asyncio.run(create_invigilator())
        else:
            print("Usage: python manage.py [create_admin|create_invigilator]")
    else:
        print("Available commands:")
        print("  python manage.py create_admin")
        print("  python manage.py create_invigilator")