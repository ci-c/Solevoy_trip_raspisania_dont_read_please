"""
Database fixtures for testing.

Provides isolated test databases and session management.
"""

import asyncio
import os
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text

from app.database.models import Base


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for the entire test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db_engine():
    """
    Create a test database engine with isolated file per test.

    Each test gets its own SQLite database file that's cleaned up after.
    """
    # Create unique test DB file
    test_db_path = Path("./data/test_db_temp.db")
    test_db_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove if exists from previous failed test
    if test_db_path.exists():
        test_db_path.unlink()

    # Create async engine
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{test_db_path}",
        echo=False,  # Set to True for SQL query debugging
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()
    if test_db_path.exists():
        test_db_path.unlink()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a clean database session for each test.

    Automatically rolls back after test to ensure isolation.
    """
    async_session_maker = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()
        await session.close()


@pytest_asyncio.fixture(scope="function")
async def clean_db(test_db_engine):
    """
    Provide a completely clean database with no data.

    Useful for testing database initialization and first-run scenarios.
    """
    # Tables are already created by test_db_engine
    # This fixture just signals intent for clean DB tests
    yield test_db_engine


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for testing."""
    monkeypatch.setenv("BOT_TOKEN", "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz12345")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./data/test_db_temp.db")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    yield
    # Cleanup happens automatically with monkeypatch
