# repositories/access_log_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from models.access_log import AccessLog, AccessAction

class AccessLogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, log_data: dict) -> AccessLog:
        """Create access log entry"""
        access_log = AccessLog(**log_data)
        self.db.add(access_log)
        await self.db.commit()
        await self.db.refresh(access_log)
        return access_log
    
    async def count_overrides(self, days: int = 30) -> int:
        """Count manual overrides in last N days"""
        start_date = datetime.now() - timedelta(days=days)
        query = select(func.count()).where(
            
                AccessLog.Timestamp >= start_date,
                AccessLog.Action == AccessAction.OVERRIDE
            
        )
        return await self.db.scalar(query) or 0