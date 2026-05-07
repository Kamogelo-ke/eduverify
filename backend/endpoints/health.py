# api/v1/endpoints/health.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from datetime import datetime

from database import get_db
from core.dependencies import get_current_user, require_role
from utils.cache import RedisCache
from models.exam_session import ExamSession, SessionStatus
from models.student import Student
from schemas.health import (
    AIHealthResponse,
    SISHealthResponse,
    CacheSyncResponse,
    SystemMetrics
)
from services.health_service import HealthService
from services.sis_service import SISService
from models.system_user import SystemUser

router = APIRouter(prefix="/health", tags=["Health & System"])

@router.get("")
async def basic_health_check() -> Dict[str, Any]:
    """Basic health check endpoint for load balancers"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "environment": "production"
    }

@router.get("/ai-models", response_model=AIHealthResponse)
async def ai_models_health(
    db: AsyncSession = Depends(get_db),
    current_user: SystemUser = Depends(require_role(["admin", "system"]))
) -> AIHealthResponse:
    """
    Check health of all AI models (YOLOv8, MediaPipe, ArcFace, DINOv2)
    Returns detailed status of each model in the pipeline
    """
    service = HealthService(db)
    result = await service.check_ai_models()
    return AIHealthResponse(**result)

@router.get("/sis-connection", response_model=SISHealthResponse)
async def sis_connection_health(
    db: AsyncSession = Depends(get_db),
    current_user: SystemUser = Depends(require_role(["admin", "system"]))
) -> SISHealthResponse:
    """
    Check connection to Student Information System (SIS)
    Tests API connectivity, authentication, and response time
    """
    sis_service = SISService()
    try:
        result = await sis_service.check_connection()
        return SISHealthResponse(**result)
    finally:
        await sis_service.close()

# @router.get("/database")
# async def database_health(
#     db: AsyncSession = Depends(get_db),
#     current_user: SystemUser = Depends(require_role(["admin", "system"]))
# ) -> Dict[str, Any]:
#     """Check database connectivity and performance"""
#     service = HealthService(db)
    
#     # Check read/write capability
#     try:
#         # Test write
#         await db.execute(text("SELECT 1"))
        
#         # Get database size
#         size_query = await db.execute(text("""
#             SELECT pg_database_size(current_database()) / 1024 / 1024 as size_mb
#         """))
#         db_size = size_query.scalar()
        
#         # Get active connections
#         conn_query = await db.execute(text("""
#             SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()
#         """))
#         active_connections = conn_query.scalar()
        
#         return {
#             "status": "healthy",
#             "size_mb": db_size,
#             "active_connections": active_connections,
#             "pool_size": 20,
#             "latency_ms": 0
#         }
#     except Exception as e:
#         return {
#             "status": "unhealthy",
#             "error": str(e),
#             "size_mb": None,
#             "active_connections": None
#         }

# @router.get("/redis")
# async def redis_health(
#     current_user: SystemUser = Depends(require_role(["admin", "system"]))
# ) -> Dict[str, Any]:
#     """Check Redis cache health"""
#     if not RedisCache:
#         return {
#             "status": "not_configured",
#             "message": "Redis is not configured"
#         }
    
#     try:
#         # Test connection
#         await RedisCache.ping()
        
#         # Get info
#         info = await RedisCache.info("stats")
        
#         return {
#             "status": "healthy",
#             "total_commands_processed": info.get("total_commands_processed", 0),
#             "keyspace_hits": info.get("keyspace_hits", 0),
#             "keyspace_misses": info.get("keyspace_misses", 0),
#             "hit_rate": info.get("keyspace_hits", 0) / (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1)) * 100
#         }
#     except Exception as e:
#         return {
#             "status": "unhealthy",
#             "error": str(e)
#         }

@router.post("/cache/sync", response_model=CacheSyncResponse)
async def sync_cache(
    force: bool = False,
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    current_user: SystemUser = Depends(require_role(["admin", "system"]))
) -> CacheSyncResponse:
    """
    Sync Redis cache with database
    - Students: Biometric hashes (1 hour TTL)
    - Exam sessions: Active sessions (5 min TTL)
    - Configurations: System settings (24 hour TTL)
    """
    if not RedisCache:
        return CacheSyncResponse(
            status="error",
            students_synced=0,
            active_sessions_synced=0,
            duration_seconds=0,
            cache_size_mb=0,
            force_sync_performed=force,
            message="Redis not configured"
        )
    
    try:
        start_time = datetime.now()
        
        # Sync student biometric hashes
        student_result = await db.execute(
            select(Student.id, Student.BiometricHash).where(Student.BiometricHash.isnot(None))
        )
        students = student_result.fetchall()
        synced_count = 0

        for student in students:
            redis_key = f"student:biometric:{student[0]}"
            await RedisCache.set(
                redis_key,
                student[1],
                ex=3600  # 1 hour TTL
            )
            synced_count += 1

        # Sync active exam sessions
        session_result = await db.execute(
            select(ExamSession).where(ExamSession.Status == SessionStatus.ACTIVE)
        )
        active_sessions = session_result.scalars().all()
        
        for session in active_sessions:
            redis_key = f"session:active:{session.id}"
            session_data = {
                "session_id": session.id,
                "module_code": session.ModuleCode,
                "venue_location": session.VenueLocation,
                "start_time": str(session.StartTime),
                "end_time": str(session.EndTime),
            }
            await RedisCache.setex(
                redis_key,
                300,  # 5 minutes
                str(session_data)
            )
        
        # Clear old cache if force flag
        if force:
            await RedisCache.delete_pattern("temp:*")
        
        # Get cache size
        redis_info = await RedisCache.info("memory")
        cache_size_mb = redis_info.get("used_memory", 0) / 1024 / 1024
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return CacheSyncResponse(
            status="success",
            students_synced=synced_count,
            active_sessions_synced=len(active_sessions),
            duration_seconds=duration,
            cache_size_mb=cache_size_mb,
            force_sync_performed=force,
            message="Cache sync completed successfully"
        )
        
    except Exception as e:
        return CacheSyncResponse(
            status="error",
            students_synced=0,
            active_sessions_synced=0,
            duration_seconds=0,
            cache_size_mb=0,
            force_sync_performed=force,
            message=f"Sync failed: {str(e)}"
        )

# @router.get("/metrics", response_model=SystemMetrics)
# async def get_system_metrics(
#     db: AsyncSession = Depends(get_db),
#     current_user: SystemUser = Depends(require_role(["admin"]))
# ) -> SystemMetrics:
#     """
#     Detailed system metrics for monitoring and SLA reporting
#     Includes database, system resources, and application metrics
#     """
#     service = HealthService(db)
#     metrics = await service.get_system_metrics()
#     return SystemMetrics(**metrics)

# @router.get("/readiness")
# async def readiness_check(
#     db: AsyncSession = Depends(get_db)
# ) -> Dict[str, Any]:
#     """
#     Kubernetes readiness probe
#     Checks if the application is ready to receive traffic
#     """
#     errors = []
    
#     # Check database
#     try:
#         await db.execute(text("SELECT 1"))
#         db_ready = True
#     except Exception as e:
#         db_ready = False
#         errors.append(f"Database: {str(e)}")
    
#     # Check Redis (optional)
#     redis_ready = True
#     if RedisCache:
#         try:
#             await RedisCache.ping()
#         except Exception as e:
#             redis_ready = False
#             errors.append(f"Redis: {str(e)}")
    
#     overall_ready = db_ready and redis_ready
    
#     return {
#         "ready": overall_ready,
#         "database": db_ready,
#         "redis": redis_ready,
#         "errors": errors if not overall_ready else []
#     }

# @router.get("/liveness")
# async def liveness_check() -> Dict[str, Any]:
#     """
#     Kubernetes liveness probe
#     Checks if the application is still running
#     """
#     return {
#         "alive": True,
#         "timestamp": datetime.now().isoformat()
#     }
