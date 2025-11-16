"""
Database session management.

This module provides:
- Async SQLAlchemy engine and session factory
- Database dependency for FastAPI
- Connection lifecycle management
"""

from collections.abc import AsyncGenerator
from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.core.config import settings

# Create async engine
engine: Optional[AsyncEngine] = None

# Create async session factory
async_session_maker: Optional[async_sessionmaker[AsyncSession]] = None

# Base class for SQLAlchemy models
Base = declarative_base()


def get_engine() -> AsyncEngine:
    """
    Get or create database engine.

    Returns:
        AsyncEngine instance
    """
    global engine

    if engine is None:
        engine = create_async_engine(
            settings.database_url,
            echo=settings.is_development,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
        )

    return engine


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """
    Get or create session maker.

    Returns:
        Async session maker
    """
    global async_session_maker

    if async_session_maker is None:
        async_session_maker = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

    return async_session_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database session.

    Yields:
        Database session

    Example:
        ```python
        from fastapi import Depends
        from app.db.session import get_db

        @app.get("/users")
        async def list_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
        ```
    """
    session_maker = get_session_maker()

    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database (create tables).

    Note: In production, use Alembic migrations instead.
    """
    engine = get_engine()

    async with engine.begin() as conn:
        # Import all models here to ensure they are registered
        from app.db import models  # noqa: F401

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Close database connections.

    Should be called on application shutdown.
    """
    global engine

    if engine is not None:
        await engine.dispose()
        engine = None
