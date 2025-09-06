# Copyright (c) 2024-2025 SZGMU Bot Project
# This software is proprietary and confidential.
# See LICENSE for terms of use.

"""SQLAlchemy async session management."""

from collections.abc import AsyncGenerator
from pathlib import Path

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database.models import Base

# Database path relative to project root
DATABASE_PATH = Path(__file__).parent.parent.parent / "data" / "szgmu_bot.db"
DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_PATH}"

# Create async engine with proper settings for SQLite
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    pool_pre_ping=True,  # Enable connection health checks
)

# Session factory for consistent configuration
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a configured database session.

    Yields:
        AsyncSession: Database session.

    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database by creating all tables.
    
    This will create fresh tables, dropping any existing ones.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)  # Drop existing tables
        await conn.run_sync(Base.metadata.create_all)  # Create fresh tables
        logger.info("Database initialized with fresh tables")
