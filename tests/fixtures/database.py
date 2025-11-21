"""
Database fixtures for testing.

Provides isolated test databases and session management.
"""

import asyncio
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

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
async def db_session() -> AsyncGenerator[AsyncSession]:
    """
    Provide a clean database session for each test.

    Uses the main database so that services can see the test data.
    Cleans all tables after each test to ensure isolation.
    """
    from app.database.models import Base
    from app.database.session import get_session

    async for session in get_session():
        yield session

        # Clean up after test - delete all data from all tables
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(text(f"DELETE FROM {table.name}"))
        await session.commit()
        break  # Exit after yielding the session


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
    # Token secret must be exactly 35 characters
    monkeypatch.setenv("BOT_TOKEN", "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz123456789")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./data/test_db_temp.db")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    # Cleanup happens automatically with monkeypatch
