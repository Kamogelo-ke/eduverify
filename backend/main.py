"""
This module serves as the entry point for running a FastAPI application.

It creates a FastAPI instance and starts the ASGI server using Uvicorn
when the script is executed directly. Uvicorn provides high performance
for serving asynchronous Python web applications.
"""
from contextlib import asynccontextmanager
import logging
from sqlalchemy.ext.asyncio import AsyncSession
import uvicorn
from fastapi import FastAPI, Depends
from starlette.middleware.cors import CORSMiddleware
from endpoints import audit, health, sis
from database import session_local, init_db, engine, get_db
from endpoints import (
      auth, access, admin, audit, deps, face, health, sis, students
)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Application lifespan context to initialize DB and seed data."""
    await init_db()
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)
# Default root endpoint
origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")
app.include_router(sis.router, prefix="/api/v1")
app.include_router(access.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
# app.include_router(deps.router, prefix="/api/v1")
app.include_router(face.router, prefix="/api/v1")
app.include_router(students.router, prefix="/api/v1")

@app.get("/")
async def root(db: AsyncSession = Depends(get_db)):
    """Health check endpoint to verify backend is running."""
    return {"message": "Backend is running"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
