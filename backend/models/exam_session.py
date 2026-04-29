# models/exam_session.py
from sqlalchemy import Column, Integer, String, DateTime, Time, Date, ForeignKey, Enum, Boolean, Float, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, relationship
import enum
from datetime import datetime
from database import Base
# from models.venue import Venue

class SessionStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ExamSession(Base):
    __tablename__ = "exam_sessions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ModuleCode = Column(String(20), nullable=False, index=True)
    ModuleName = Column(String(200), nullable=False)
    
    # Venue information
    VenueLocation = Column(String(255), nullable=False)
    VenueID = Column(Integer, ForeignKey("venues.id"), nullable=False)
    
    # Schedule
    ExamDate = Column(Date, nullable=False)
    StartTime = Column(Time, nullable=False)
    EndTime = Column(Time, nullable=False)
    
    # Session management
    Status = Column(Enum(SessionStatus), default=SessionStatus.SCHEDULED, nullable=False)
    CreatedBy = Column(Integer, ForeignKey("system_users.id"), nullable=False)
    
    # Capacity and attendance
    MaxCapacity = Column(Integer, default=100)
    RegisteredStudents = Column(Integer, default=0)
    ActualAttendance = Column(Integer, default=0)
    
    # Verification settings
    FaceThreshold = Column(Float, default=0.68)
    LivenessThreshold = Column(Float, default=0.75)
    AllowManualOverride = Column(Boolean, default=True)
    
    # Timestamps
    CreatedAt = Column(DateTime, server_default=func.now())
    UpdatedAt = Column(DateTime, onupdate=func.now())
    CompletedAt = Column(DateTime, nullable=True)
    
    # Relationships
    # creator : Mapped["SystemUser"] = relationship("SystemUser", foreign_keys=[CreatedBy])
    # venue: Mapped["Venue"] = relationship("Venue", back_populates="exam_sessions")
    # verification_logs: Mapped["VerificationLog"] = relationship("VerificationLog", back_populates="exam_session")
    # attendance_records: Mapped["AttendanceRegister"] = relationship("AttendanceRegister", back_populates="exam_session")
    # ai_metrics: Mapped["AIMeterics"] = relationship("AIMetrics", back_populates="exam_session")
    
    # Indexes
    __table_args__ = (
        Index('idx_exam_session_venue_date', 'VenueLocation', 'ExamDate'),
        Index('idx_exam_session_status', 'Status'),
        Index('idx_exam_session_module', 'ModuleCode', 'ExamDate'),
    )
    
    @property
    def is_active(self) -> bool:
        """Check if session is currently active"""
        if self.Status != SessionStatus.ACTIVE:
            return False
        
        now = datetime.now()
        session_start = datetime.combine(self.ExamDate, self.StartTime)
        session_end = datetime.combine(self.ExamDate, self.EndTime)
        
        return session_start <= now <= session_end
    
    @property
    def remaining_capacity(self) -> int:
        """Calculate remaining capacity"""
        return self.MaxCapacity - self.RegisteredStudents
    
    def __repr__(self):
        return f"<ExamSession {self.ModuleCode} at {self.VenueLocation} on {self.ExamDate}>"
