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
        health_status = {}
        
        try:
            # Check YOLOv8-Face
            yolov8_status = await self.ai_service.check_yolov8()
            health_status["yolov8_face"] = {
                "status": "loaded" if yolov8_status else "failed",
                "version": "v8.0.0",
                # "gpu_available": torch.cuda.is_available()
            }
            
            # Check MediaPipe
            mediapipe_status = await self.ai_service.check_mediapipe()
            health_status["mediapipe_landmark"] = {
                "status": "loaded" if mediapipe_status else "failed",
                "version": "2.0.0"
            }
            
            # Check ArcFace
            arcface_status = await self.ai_service.check_arcface()
            health_status["arcface_matcher"] = {
                "status": "loaded" if arcface_status else "failed",
                "feature_dimension": 512,
                "threshold": 0.68
            }
            
            # Check DINOv2 PAD
            dinov2_status = await self.ai_service.check_dinov2()
            health_status["dinov2_pad"] = {
                "status": "loaded" if dinov2_status else "failed",
                "anti_spoof_enabled": True,
                "model_size": "small"
            }
            
            all_loaded = all([
                yolov8_status, mediapipe_status, arcface_status, dinov2_status
            ])
            
            return {
                "status": "healthy" if all_loaded else "degraded",
                "models": health_status,
                # "gpu_memory_used_mb": torch.cuda.memory_allocated() / 1024**2 if torch.cuda.is_available() else 0,
                "inference_queue_size": await self.ai_service.get_queue_size(),
                "avg_inference_time_ms": await self.ai_service.get_avg_inference_time()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "models": health_status
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
                # "redis_connected": redis_client is not None,
                "redis_url": settings.REDIS_URL if settings.ENVIRONMENT == "development" else "***hidden***"
            }
        }
