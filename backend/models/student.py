 # models/student.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, relationship
from datetime import datetime
from database import Base

class Student(Base):
    __tablename__ = "students"
    
    StudentID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    FirstName = Column(String(100), nullable=False)
    LastName = Column(String(100), nullable=False)
    Email = Column(String(255), unique=True, nullable=False, index=True)
    StudentNumber = Column(String(50), unique=True, nullable=False, index=True)
    
    # Biometric data (POPIA compliant - hash only)
    BiometricHash = Column(String(512), nullable=True)  # One-way hash of face features
    FaceImageHash = Column(String(512), nullable=True)  # Separate hash for face deletion endpoint
    
    # Academic information
    AcademicStanding = Column(String(50), default="Good")  # Good, Probation, Suspended
    EnrollmentStatus = Column(String(50), default="Active")  # Active, Graduated, Withdrawn
    
    # POPIA compliance
    ConsentGiven = Column(Boolean, default=False, nullable=False)
    ConsentDate = Column(DateTime, nullable=True)
    ConsentVersion = Column(String(10), default="1.0")
    
    # Timestamps
    CreatedAt = Column(DateTime, server_default=func.now(), nullable=False)
    UpdatedAt = Column(DateTime, onupdate=func.now())
    LastVerificationAttempt = Column(DateTime, nullable=True)
    
    # Metadata
    DeviceRegistrationID = Column(String(255), nullable=True)
    PreferredVenue = Column(String(100), nullable=True)
    
    # Relationships
    # verification_logs : Mapped["VerificationLog"] = relationship("VerificationLog", back_populates="student", cascade="all, delete-orphan")
    # access_logs : Mapped["AccessLog"] = relationship("AccessLog", back_populates="student")
    # attendance_records : Mapped["AttendanceRegister"] = relationship("AttendanceRegister", back_populates="student")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_student_academic_standing', 'AcademicStanding'),
        Index('idx_student_consent', 'ConsentGiven'),
        Index('idx_student_name', 'FirstName', 'LastName'),
    )
    
    @property
    def FullName(self) -> str:
        return f"{self.FirstName} {self.LastName}"
    
    def is_eligible_for_exam(self) -> bool:
        """Check if student is eligible to write exams"""
        return (
            self.ConsentGiven and
            self.AcademicStanding != "Suspended" and
            self.EnrollmentStatus == "Active"
        )
    
    def __repr__(self):
        return f"<Student {self.StudentNumber}: {self.FullName}>"
