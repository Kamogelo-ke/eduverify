# models/student.py
import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Index, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class Gender(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"
    prefer_not_to_say = "prefer_not_to_say"


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    FirstName = Column(String(100), nullable=False)
    LastName = Column(String(100), nullable=False)
    Email = Column(String(255), unique=True, nullable=False, index=True)
    StudentNumber = Column(String(50), unique=True, nullable=False, index=True)
    programme = Column(String(255), nullable=True)
    year_of_study = Column(Integer, nullable=True)
    gender = Column(Enum(Gender), nullable=True)
    BiometricHash = Column(String(512), nullable=True)
    FaceImageHash = Column(String(512), nullable=True)
    AcademicStanding = Column(String(50), default="Good")
    EnrollmentStatus = Column(String(50), default="Active")
    ConsentGiven = Column(Boolean, default=False, nullable=False)
    ConsentDate = Column(DateTime, nullable=True)
    ConsentVersion = Column(String(10), default="1.0")
    CreatedAt = Column(DateTime, server_default=func.now(), nullable=False)
    UpdatedAt = Column(DateTime, onupdate=func.now())
    LastVerificationAttempt = Column(DateTime, nullable=True)
    DeviceRegistrationID = Column(String(255), nullable=True)
    PreferredVenue = Column(String(100), nullable=True)

    # Fix: add biometric_profile relationship to match BiometricProfile.back_populates
    biometric_profile = relationship(
        "BiometricProfile",
        back_populates="student",
        uselist=False,
        cascade="all, delete-orphan",
    )
    verification_attempts = relationship(
    "VerificationAttempt",
    back_populates="student",
    )
    __table_args__ = (
        Index("idx_student_academic_standing", "AcademicStanding"),
        Index("idx_student_consent", "ConsentGiven"),
        Index("idx_student_name", "FirstName", "LastName"),
    )

    @property
    def FullName(self):
        return f"{self.FirstName} {self.LastName}"

    def is_eligible_for_exam(self):
        return (
            self.ConsentGiven and
            self.AcademicStanding != "Suspended" and
            self.EnrollmentStatus == "Active"
        )

    def __repr__(self):
        return f"<Student {self.StudentNumber}: {self.FullName}>"