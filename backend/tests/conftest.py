"""
Test configuration.

Sets DATABASE_URL to SQLite+aiosqlite *before* any app module is imported,
and patches create_async_engine to strip PostgreSQL-only pool params so SQLite
works without modification to production code.
"""
import os

# Override DB before any import touches database.py
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_eduverify.db"
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-tests-only-32chars")
os.environ.setdefault("BIOMETRIC_ENCRYPTION_KEY", "dGhpcy1pcy1hLTMyLWJ5dGUta2V5LWZvci1hZXMyNTY=")
os.environ.setdefault("ENVIRONMENT", "test")

import sqlalchemy.ext.asyncio as _sa_async

_orig_create_engine = _sa_async.create_async_engine

def _sqlite_safe_engine(url, **kwargs):
    for k in ("pool_size", "max_overflow", "pool_timeout", "pool_recycle"):
        kwargs.pop(k, None)
    return _orig_create_engine(url, **kwargs)

_sa_async.create_async_engine = _sqlite_safe_engine

# Safe to import app modules now
import pytest
import pytest_asyncio
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from database import Base, engine, session_local, get_db
from main import app


async def _override_get_db():
    async with session_local() as session:
        yield session

app.dependency_overrides[get_db] = _override_get_db


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """Create all tables once per test session using the patched SQLite engine."""
    from models import (
        student, system_user, biometric_profile, exam_session,
        verification_attempt, access_log, ai_metrics, attendence_register,
        venue, verification_log,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def clean_tables():
    """Wipe all rows between tests to keep isolation."""
    yield
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest_asyncio.fixture
async def db() -> AsyncSession:
    async with session_local() as session:
        yield session


@pytest_asyncio.fixture
async def client():
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=True)
    ac = httpx.AsyncClient(transport=transport, base_url="http://test")
    yield ac
    await ac.aclose()
