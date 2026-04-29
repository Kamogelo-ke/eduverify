# models/attendance_register.py (Make sure this exists)
from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Enum, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, relationship
import enum
from database import Base

class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"

class AttendanceRegister(Base):
    __tablename__ = "attendance_registers"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("exam_sessions.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    
    MarkedAt = Column(DateTime, server_default=func.now(), nullable=False)
    log_id = Column(Integer, ForeignKey("verification_logs.LogID"), nullable=True)
    
    Status = Column(Enum(AttendanceStatus), default=AttendanceStatus.PRESENT)
    Notes = Column(String(500), nullable=True)
    
    # Relationships - use string references
    # exam_session :Mapped["ExamSession"] = relationship("ExamSession", back_populates="attendance_records")
    # student: Mapped["Student"] = relationship("Student", back_populates="attendance_records")
   
    __table_args__ = (
        Index('idx_unique_student_session', 'id', 'id', unique=True),
    )