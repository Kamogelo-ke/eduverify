# repositories/verification_log_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from sqlalchemy.orm import selectinload
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from models.verification_log import VerificationLog, VerificationOutcome
from models.student import Student
from models.exam_session import ExamSession

class VerificationLogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, log_data: dict) -> VerificationLog:
        """Create a new verification log entry"""
        verification_log = VerificationLog(**log_data)
        self.db.add(verification_log)
        await self.db.commit()
        await self.db.refresh(verification_log)
        return verification_log
    
    async def get_by_venue(
        self, 
        venue: str, 
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        outcome: Optional[str] = None,
        limit: int = 100
    ) -> List[VerificationLog]:
        """Get logs filtered by venue"""
        query = select(VerificationLog).where(
            VerificationLog.VenueLocation.ilike(f"%{venue}%")
        )
        
        if start_date:
            query = query.where(func.date(VerificationLog.Timestamp) >= start_date)
        if end_date:
            query = query.where(func.date(VerificationLog.Timestamp) <= end_date)
        if outcome:
            query = query.where(VerificationLog.VerificationOutcome == outcome)
        
        query = query.order_by(VerificationLog.Timestamp.desc()).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_student(
        self, 
        student_id: int, 
        limit: int = 50
    ) -> List[VerificationLog]:
        """Get logs for a specific student"""
        query = select(VerificationLog).where(
            VerificationLog.id == student_id
        ).order_by(VerificationLog.Timestamp.desc()).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_statistics(
        self, 
        days: int
    ) -> Dict[str, Any]:
        """Get audit statistics for the last N days"""
        start_date = datetime.now() - timedelta(days=days)
        
        # Total attempts
        total_query = select(func.count()).where(
            VerificationLog.Timestamp >= start_date
        )
        total_attempts = await self.db.scalar(total_query)
        
        # Successful attempts
        success_query = select(func.count()).where(
            and_(
                VerificationLog.Timestamp >= start_date,
                VerificationLog.VerificationOutcome == VerificationOutcome.SUCCESS
            )
        )
        successful = await self.db.scalar(success_query)
        
        # Daily breakdown
        daily_query = select(
            func.date(VerificationLog.Timestamp).label("date"),
            func.count().label("total"),
            func.sum(
                func.case(
                    (VerificationLog.VerificationOutcome == VerificationOutcome.SUCCESS, 1),
                    else_=0
                )
            ).label("successful")
        ).where(
            VerificationLog.Timestamp >= start_date
        ).group_by(func.date(VerificationLog.Timestamp))
        
        daily_result = await self.db.execute(daily_query)
        daily_breakdown = [
            {"date": row.date, "total": row.total, "successful": row.successful}
            for row in daily_result
        ]
        
        return {
            "total_attempts": total_attempts or 0,
            "successful": successful or 0,
            "daily_breakdown": daily_breakdown
        }
    
    async def export_logs(
        self,
        start_date: date,
        end_date: date,
        venue: Optional[str] = None
    ) -> List[tuple]:
        """Export logs for compliance reporting"""
        query = select(
            VerificationLog,
            Student.FirstName,
            Student.LastName,
            ExamSession.ModuleCode,
            ExamSession.VenueLocation
        ).join(
            Student, VerificationLog.id == Student.id
        ).join(
            ExamSession, VerificationLog.id == ExamSession.id
        ).where(
            and_(
                func.date(VerificationLog.Timestamp) >= start_date,
                func.date(VerificationLog.Timestamp) <= end_date
            )
        )
        
        if venue:
            query = query.where(ExamSession.VenueLocation.ilike(f"%{venue}%"))
        
        result = await self.db.execute(query)
        return result.all()
