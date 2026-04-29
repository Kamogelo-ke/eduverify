from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="invigilator")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    
    full_name: Mapped[str] = mapped_column(String(100), nullable=True)
    staff_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=True)
    is_temp_password: Mapped[bool] = mapped_column(Boolean, default=False)