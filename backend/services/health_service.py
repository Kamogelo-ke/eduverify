# services/health_service.py
# import psutil
# import torch
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from core.config import settings
from utils.cache import RedisCache
# from services.ai_pipeline import AIPipelineService

class HealthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        # self.ai_service = AIPipelineService()
        self.start_time = datetime.now()
    
    async def check_database(self) -> Dict[str, Any]:
        """Check database connectivity"""
        try:
            start = datetime.now()
            await self.db.execute(text("SELECT 1"))
            latency_ms = (datetime.now() - start).total_seconds() * 1000
            
            return {
                "status": "connected",
                "latency_ms": round(latency_ms, 2),
                "pool_size": getattr(settings, 'DB_POOL_SIZE', 10)
            }
        except Exception as e:
            return {
                "status": "disconnected",
                "error": str(e),
                "latency_ms": None
            }
    
    async def check_ai_models(self) -> Dict[str, Any]:
        """Check health of all AI models"""
        return {
            "status": "not_loaded",
            "models": {
                "yolov8_face": {"status": "not_loaded"},
                "mediapipe_landmark": {"status": "not_loaded"},
                "arcface_matcher": {"status": "not_loaded"},
                "dinov2_pad": {"status": "not_loaded"},
            },
            "inference_queue_size": 0,
            "avg_inference_time_ms": 0
        }
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get detailed system metrics"""
        
        # Database health
        db_health = await self.check_database()
        
        # System resources
        # cpu_percent = psutil.cpu_percent(interval=1)
        # memory = psutil.virtual_memory()
        # disk = psutil.disk_usage('/')
        
        # Application metrics
        uptime_seconds = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "database": db_health,
            "system_resources": {
                # "cpu_usage_percent": cpu_percent,
                # "memory_usage_percent": memory.percent,
                # "memory_available_gb": round(memory.available / (1024**3), 2),
                # "disk_usage_percent": disk.percent,
                # "disk_free_gb": round(disk.free / (1024**3), 2)
            },
            "application": {
                "uptime_seconds": uptime_seconds,
                "uptime_human": str(timedelta(seconds=uptime_seconds)),
                "version": settings.APP_VERSION,
                "environment": settings.ENVIRONMENT
            },
            "cache": {
                "redis_url": settings.REDIS_URL if settings.ENVIRONMENT == "development" else "***hidden***"
            }
        }
