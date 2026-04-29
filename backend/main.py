"""
EduVerify — FastAPI application entry point.

Starts the async ASGI server. All routers are registered here.
Run with:
    uvicorn main:app --reload --host 0.0.0.0 --port 8008
Swagger UI:
    http://localhost:8008/docs
"""

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.cors import CORSMiddleware

from core.config import settings
from database import engine, init_db, get_db

# Routers
from endpoints.auth import router as auth_router
from endpoints.face import router as face_router
from endpoints.students import router as students_router
from endpoints.admin import router as admin_router

# Pre-load the face service so models warm up at startup
from services.face_service import get_face_service

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """
    Application lifespan — runs once at startup and once at shutdown.
      Startup : create all DB tables, warm up AI models.
      Shutdown: dispose of the async engine connection pool.
    """
    logger.info("EduVerify starting up...")
    await init_db()
    logger.info("Database tables verified")

    # Warm up AI models (stubs gracefully if weights not installed)
    try:
        svc = get_face_service()
        svc._load_models()
        logger.info("AI models ready")
    except Exception as exc:
        logger.warning("AI model pre-load skipped (dev mode): %s", exc)

    yield

    await engine.dispose()
    logger.info("EduVerify shut down cleanly")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AI-powered exam verification system for Tshwane University of Technology. "
        "Face recognition · Liveness detection · SIS eligibility · POPIA compliant."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
origins = [
    "http://localhost:3000",   # React dev server
    "http://localhost:5173",   # Vite dev server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
PREFIX = "/api/v1"
app.include_router(auth_router,     prefix=PREFIX)
app.include_router(face_router,     prefix=PREFIX)
app.include_router(students_router, prefix=PREFIX)
app.include_router(admin_router,    prefix=PREFIX)


# ── Health endpoints ──────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def root(db: AsyncSession = Depends(get_db)):
    """Health check — confirms the server and database are reachable."""
    return {"message": "EduVerify backend is running", "version": settings.APP_VERSION}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}


@app.get("/health/ai-models", tags=["Health"])
async def health_ai():
    svc = get_face_service()
    return {
        "status": "ready" if svc._initialized else "not_loaded",
        "models": ["YOLOv8-Face", "ArcFace-R100", "MediaPipe-FaceMesh", "DINOv2-PAD"],
    }


# ── Global error handler ──────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8008)