# repositories/student_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import Optional, List, Dict, Any
from models.student import Student

class StudentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, student_id: int) -> Optional[Student]:
        """Get student by ID"""
        query = select(Student).where(Student.StudentID == student_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_student_number(self, student_number: str) -> Optional[Student]:
        """Get student by student number"""
        query = select(Student).where(Student.StudentNumber == student_number)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Student]:
        """Get all students with pagination"""
        query = select(Student).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def create(self, student_data: Dict[str, Any]) -> Student:
        """Create a new student"""
        student = Student(**student_data)
        self.db.add(student)
        await self.db.commit()
        await self.db.refresh(student)
        return student
    
    async def update(self, student_id: int, update_data: Dict[str, Any]) -> Optional[Student]:
        """Update student information"""
        query = update(Student).where(Student.StudentID == student_id).values(**update_data).returning(Student)
        result = await self.db.execute(query)
        await self.db.commit()
        return result.scalar_one_or_none()
    
    async def delete_face_data(self, student_id: int) -> bool:
        """Delete face biometric data (POPIA compliance)"""
        query = update(Student).where(Student.StudentID == student_id).values(
            BiometricHash=None,
            FaceImageHash=None
        )
        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount > 0
    
    async def update_biometric_hash(self, student_id: int, biometric_hash: str) -> bool:
        """Update student's biometric hash"""
        query = update(Student).where(Student.StudentID == student_id).values(
            BiometricHash=biometric_hash
        )
        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount > 0
    
    async def get_eligible_students(self) -> List[Student]:
        """Get all students eligible for exams"""
        query = select(Student).where(
            Student.ConsentGiven == True,
            Student.AcademicStanding != "Suspended",
            Student.EnrollmentStatus == "Active"
        )
        result = await self.db.execute(query)
        return result.scalars().all()