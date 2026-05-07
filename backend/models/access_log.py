# models/access_log.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, relationship
import enum
from database import Base

class AccessAction(str, enum.Enum):
    GRANT = "grant"
    DENY = "deny"
    OVERRIDE = "override"

class AccessLog(Base):
    __tablename__ = "access_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("system_users.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("exam_sessions.id"), nullable=False)
    Action = Column(Enum(AccessAction), nullable=False)
    Timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    TTSFeedbackSent = Column(Integer, default=0)  # 0=False, 1=True
    Reason = Column(String(500), nullable=True)
    
    # Relationships
    # user : Mapped["SystemUser"] = relationship("SystemUser", back_populates="access_logs")
    # student : Mapped["Student"] = relationship("Student")
    # exam_session : Mapped["ExamSession"] = relationship("ExamSession")