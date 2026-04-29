# models/verification_log.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, Float, ForeignKey
from sqlalchemy.orm import Mapped, relationship
import enum
from database import Base

class VerificationOutcome(str, enum.Enum):
    SUCCESS = "Success"
    DENIED_BIOMETRIC_FAIL = "Denied_Biometric_Fail"
    DENIED_NOT_REGISTERED = "Denied_Not_Registered"
    MANUAL_OVERRIDE = "Manual_Override"

class VerificationLog(Base):
    __tablename__ = "verification_logs"
    
    LogID = Column(Integer, primary_key=True, index=True)
    StudentID = Column(Integer, ForeignKey("students.StudentID"), nullable=False)
    SessionID = Column(Integer, ForeignKey("exam_sessions.SessionID"), nullable=False)
    Timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    DeviceID = Column(String(255), nullable=False)
    VerificationOutcome = Column(Enum(VerificationOutcome), nullable=False)
    DigitalSignature = Column(String(512), nullable=False)
    VenueLocation = Column(String(255), nullable=False)
    AttemptNumber = Column(Integer, default=1)
    FaceMatchScore = Column(Float, nullable=True)
    LivenessScore = Column(Float, nullable=True)
    
    # Relationships
    # student : Mapped["Student"] = relationship("Student", back_populates="verification_logs")
    # exam_session : Mapped["ExamSession"] = relationship("ExamSession", back_populates="verification_logs")
