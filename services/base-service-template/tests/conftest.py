"""
Pytest configuration and fixtures.
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.session import Base, get_db
from app.main import create_application

# Test database URL (use in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    Create event loop for async tests.

    Yields:
        Event loop
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create test database session.

    Yields:
        Test database session
    """
    # Create test engine
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
    )

    # Create session factory
    async_session = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create and yield session
    async with async_session() as session:
        yield session

    # Drop tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
def client(db_session: AsyncSession) -> Generator[TestClient, None, None]:
    """
    Create test client with mocked database session.

    Args:
        db_session: Test database session

    Yields:
        Test client
    """
    app = create_application()

    # Override database dependency
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """
    Create mock authentication headers.

    Returns:
        Headers dict with mock Bearer token
    """
    # In real tests, you would create a valid JWT token
    mock_token = "mock_jwt_token"
    return {"Authorization": f"Bearer {mock_token}"}
