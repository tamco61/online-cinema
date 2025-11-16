"""
API dependencies.

Common dependencies used across multiple endpoints.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.auth_service import AuthService, get_auth_service
from app.services.jwt_service import JWTService, get_jwt_service
from app.services.redis_service import RedisService, get_redis_service


async def get_auth_service_dep(
    db: AsyncSession = Depends(get_db),
    jwt_service: JWTService = Depends(get_jwt_service),
    redis_service: RedisService = Depends(get_redis_service),
) -> AuthService:
    """
    Dependency for getting auth service with all dependencies injected.

    Args:
        db: Database session
        jwt_service: JWT service
        redis_service: Redis service

    Returns:
        AuthService instance
    """
    return await get_auth_service(
        db=db,
        jwt_service=jwt_service,
        redis_service=redis_service,
    )
