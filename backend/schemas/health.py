# schemas/health.py
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Optional, List

class ModelHealth(BaseModel):
    status: str
    version: Optional[str] = None
    gpu_available: Optional[bool] = None
    anti_spoof_enabled: Optional[bool] = None

class AIHealthResponse(BaseModel):
    status: str
    models: Dict[str, ModelHealth]
    gpu_memory_used_mb: float = 0
    inference_queue_size: int = 0
    avg_inference_time_ms: float = 0

class SISHealthResponse(BaseModel):
    status: str
    response_time_ms: float
    sis_version: Optional[str] = None
    last_sync: Optional[datetime] = None
    endpoint: str
    error: Optional[str] = None

class CacheSyncResponse(BaseModel):
    status: str
    students_synced: int
    active_sessions_synced: int
    duration_seconds: float
    cache_size_mb: float
    force_sync_performed: bool
    message: Optional[str] = None

class SystemMetrics(BaseModel):
    timestamp: datetime
    database: Dict
    system_resources: Dict
    application: Dict
    cache: Dict
    sla_status: Dict