from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from database import Base

class Attendance(Base):
    __tablename__ = "attendance"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_email: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50)) 
    venue: Mapped[str] = mapped_column(String(100))
    exam: Mapped[str] = mapped_column(String(100))
    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow)