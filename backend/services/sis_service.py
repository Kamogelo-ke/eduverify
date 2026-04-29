# backend/services/sis_service.py
import httpx
from datetime import date, datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.config import settings
from models.student import Student
from models.exam_session import ExamSession
from utils.logging import get_logger

logger = get_logger(__name__)

class SISService:
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self.client = client or httpx.AsyncClient()
        self.base_url = settings.SIS_API_URL
        self.api_key = settings.SIS_API_KEY
        self.timeout = settings.SIS_TIMEOUT_SECONDS
    
    async def check_eligibility(
        self, 
        student_id: int, 
        session_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Check if student is eligible to write exam"""
        try:
            # Get exam session details
            session_query = select(ExamSession).where(ExamSession.SessionID == session_id)
            session_result = await db.execute(session_query)
            session = session_result.scalar_one_or_none()
            
            if not session:
                return {
                    "eligible": False,
                    "reason": "Invalid exam session",
                    "academic_standing": None,
                    "registered_modules": [],
                    "holds": ["Session not found"]
                }
            
            # Get student info
            student_query = select(Student).where(Student.StudentID == student_id)
            student_result = await db.execute(student_query)
            student = student_result.scalar_one_or_none()
            
            # Mock SIS check (replace with actual API call)
            sis_data = await self._mock_sis_check(student_id, session.ModuleCode)
            
            eligible = True
            reasons = []
            holds = []
            
            # Check academic standing
            if student and student.AcademicStanding == "Suspended":
                eligible = False
                reasons.append("Student is suspended")
                holds.append("Academic suspension")
            
            # Check SIS eligibility
            if not sis_data.get("is_registered", False):
                eligible = False
                reasons.append(f"Not registered for {session.ModuleCode}")
                holds.append("Module not registered")
            
            if sis_data.get("has_outstanding_fees", False):
                eligible = False
                reasons.append("Outstanding fees")
                holds.append("Financial hold")
            
            if sis_data.get("has_disciplinary_hold", False):
                eligible = False
                reasons.append("Disciplinary hold")
                holds.append("Disciplinary hold")
            
            # Check exam session timing
            current_time = datetime.now()
            if current_time < session.StartTime:
                eligible = False
                reasons.append("Exam not started yet")
            elif current_time > session.EndTime:
                eligible = False
                reasons.append("Exam has ended")
            
            return {
                "eligible": eligible,
                "reason": "; ".join(reasons) if reasons else "Eligible",
                "academic_standing": sis_data.get("academic_standing", "Good"),
                "registered_modules": list(sis_data.get("registered_modules", [])),
                "holds": list(holds)
            }
            
        except Exception as e:
            logger.error(f"SIS eligibility check failed: {str(e)}")
            return {
                "eligible": False,
                "reason": "System error checking eligibility",
                "academic_standing": None,
                "registered_modules": [],
                "holds": ["Technical error - contact invigilator"]
            }
    
    async def get_student_modules(self, student_id: int) -> Dict[str, Any]:
        """Get registered modules for a student from SIS"""
        # Mock implementation - replace with actual API call
        return {
            "student_id": student_id,
            "modules": ["SFG117V", "MAT201V", "PHY101V", "ENG301V"],
            "total": 4
        }
    
    async def get_exam_timetable(self, student_id: int) -> Dict[str, Any]:
        """Get exam timetable for a student from SIS"""
        # Mock implementation - replace with actual API call
        return {
            "student_id": student_id,
            "exams": [
                {
                    "module_code": "SFG117V",
                    "module_name": "Introduction to Programming",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "time": "09:00",
                    "venue": "Main Exam Hall A"
                },
                {
                    "module_code": "MAT201V",
                    "module_name": "Calculus II",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "time": "14:00",
                    "venue": "Main Exam Hall B"
                }
            ]
        }
    
    # Add these methods to your SISService class

    async def get_student_details(self, student_id: int) -> Dict[str, Any]:
        """Get detailed student information from SIS"""
        # Mock implementation - replace with actual SIS API call
        return {
            "sis_id": f"SIS_{student_id}",
            "enrollment_year": 2024,
            "program": "Bachelor of Science in Computer Science",
            "faculty": "Faculty of Science",
            "registration_status": "Full-time",
            "student_type": "Domestic",
            "enrollment_status": "Active",
            "credits_completed": 96,
            "credits_required": 128,
            "gpa": 3.6,
            "advisor": "Dr. Smith",
            "advisor_email": "smith@university.edu",
            "registration_date": "2024-01-15",
            "expected_graduation": "2026-06-15"
        }

    async def get_comprehensive_eligibility(self, student_id: int, module_code: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive eligibility status from SIS"""
        # Mock implementation - replace with actual SIS API call
        return {
            "eligible": True,
            "is_registered": True,
            "registration_message": "Student is registered for this module" if module_code else "Student is registered",
            "academic_standing": "Good",
            "academic_message": "Academic standing is satisfactory",
            "has_financial_hold": False,
            "financial_message": "No outstanding fees",
            "has_disciplinary_hold": False,
            "disciplinary_message": "No disciplinary actions",
            "reason": "All eligibility checks passed",
            "holds": []
        }

    async def get_exam_schedule(
        self,
        student_id: Optional[int] = None,
        module_code: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        venue: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get exam schedule from SIS with filters"""
        # Mock implementation - replace with actual SIS API call
        exams = []
        
        # Mock data
        mock_exams = [
            {
                "module_code": "SFG117V",
                "module_name": "Introduction to Programming",
                "venue": "Main Exam Hall A",
                "date": (datetime.now() + timedelta(days=7)).date(),
                "start_time": "09:00",
                "end_time": "12:00",
                "duration": 3,
                "seats_available": 50,
                "total_capacity": 200
            },
            {
                "module_code": "MAT201V",
                "module_name": "Calculus II",
                "venue": "Main Exam Hall B",
                "date": (datetime.now() + timedelta(days=14)).date(),
                "start_time": "14:00",
                "end_time": "17:00",
                "duration": 3,
                "seats_available": 30,
                "total_capacity": 150
            },
            {
                "module_code": "PHY101V",
                "module_name": "Physics Fundamentals",
                "venue": "Science Block Auditorium",
                "date": (datetime.now() + timedelta(days=21)).date(),
                "start_time": "09:00",
                "end_time": "12:00",
                "duration": 3,
                "seats_available": 20,
                "total_capacity": 100
            }
        ]
        
        for exam in mock_exams:
            # Apply filters
            if module_code and exam["module_code"] != module_code:
                continue
            if venue and venue.lower() not in exam["venue"].lower():
                continue
            if start_date and exam["date"] < start_date:
                continue
            if end_date and exam["date"] > end_date:
                continue
            if student_id:
                # In real implementation, check if student is registered for this module
                exam["is_registered"] = True
            
            exams.append(exam)
        
        return {
            "exams": exams,
            "total": len(exams),
            "student_id": student_id,
            "query_params": {
                "module_code": module_code,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "venue": venue
            }
        }

    async def get_venue_info(self, venue_name: str) -> Dict[str, Any]:
        """Get venue information from SIS"""
        # Mock implementation - replace with actual SIS API call
        mock_venues = {
            "Main Exam Hall A": {
                "capacity": 200,
                "building": "Main Building",
                "floor": "Ground",
                "has_projector": True,
                "has_smart_board": True,
                "has_ac": True,
                "accessibility": "Wheelchair accessible",
                "parking": "Nearby parking available",
                "contact_person": "John Caretaker",
                "contact_phone": "+27-11-555-0101"
            },
            "Main Exam Hall B": {
                "capacity": 150,
                "building": "Main Building",
                "floor": "First",
                "has_projector": True,
                "has_smart_board": False,
                "has_ac": True,
                "accessibility": "Elevator access",
                "parking": "Nearby parking available",
                "contact_person": "John Caretaker",
                "contact_phone": "+27-11-555-0101"
            },
            "Science Block Auditorium": {
                "capacity": 100,
                "building": "Science Block",
                "floor": "Ground",
                "has_projector": True,
                "has_smart_board": True,
                "has_ac": True,
                "accessibility": "Wheelchair accessible",
                "parking": "Dedicated parking",
                "contact_person": "Sarah Scientist",
                "contact_phone": "+27-11-555-0202"
            }
        }
        
        # Find matching venue
        for key, info in mock_venues.items():
            if venue_name.lower() in key.lower():
                return {
                    "venue_name": key,
                    **info,
                    "is_active": True,
                    "last_maintenance": "2026-03-15",
                    "next_maintenance": "2026-09-15"
                }
        
        # Default return
        return {
            "venue_name": venue_name,
            "capacity": 100,
            "building": "Unknown",
            "has_projector": False,
            "has_smart_board": False,
            "has_ac": True,
            "is_active": True
        }
    
    async def fetch_all_students(self) -> List[Dict[str, Any]]:
        """
        Fetch all students from SIS
        This method is called by the sync_students background task
        """
        # Mock implementation - replace with actual SIS API call
        # In production, you would call your SIS endpoint:
        # response = await self.client.get(f"{self.base_url}/students")
        # return response.json()
        
        logger.info("Fetching all students from SIS...")
        
        # Mock data - return a list of students
        return [
            {
                "id": 1,
                "first_name": "Alice",
                "last_name": "Johnson",
                "academic_standing": "Good",
                "consent_given": True,
                "student_number": "CS2024001",
                "email": "alice.j@university.edu"
            },
            {
                "id": 2,
                "first_name": "Bob",
                "last_name": "Smith",
                "academic_standing": "Good",
                "consent_given": True,
                "student_number": "CS2024002",
                "email": "bob.smith@university.edu"
            },
            {
                "id": 3,
                "first_name": "Carol",
                "last_name": "Davis",
                "academic_standing": "Good",
                "consent_given": True,
                "student_number": "CS2024003",
                "email": "carol.davis@university.edu"
            },
            {
                "id": 4,
                "first_name": "David",
                "last_name": "Brown",
                "academic_standing": "Probation",
                "consent_given": True,
                "student_number": "CS2024004",
                "email": "david.brown@university.edu"
            },
            {
                "id": 5,
                "first_name": "Emma",
                "last_name": "Wilson",
                "academic_standing": "Good",
                "consent_given": True,
                "student_number": "CS2024005",
                "email": "emma.wilson@university.edu"
            }
        ]
    
    async def fetch_students_by_module(self, module_code: str) -> List[Dict[str, Any]]:
        """Fetch students registered for a specific module"""
        # Mock implementation
        return [
            {"id": 1, "first_name": "Alice", "last_name": "Johnson"},
            {"id": 2, "first_name": "Bob", "last_name": "Smith"},
        ]
    
    async def check_connection(self) -> Dict[str, Any]:
        """Check connection to SIS API"""
        try:
            # Mock connection check - replace with actual API call
            return {
                "status": "connected",
                "response_time_ms": 120,
                "sis_version": "1.0.0",
                "endpoint": self.base_url
            }
        except Exception as e:
            return {
                "status": "disconnected",
                "error": str(e),
                "endpoint": self.base_url
            }
    
    async def _mock_sis_check(self, student_id: int, module_code: str) -> Dict[str, Any]:
        """Mock SIS check for testing"""
        return {
            "is_registered": True,
            "has_outstanding_fees": False,
            "has_disciplinary_hold": False,
            "academic_standing": "Good",
            "registered_modules": [module_code, "OTHER101", "MATH201"]
        }
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    