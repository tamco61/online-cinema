import jwt
from datetime import datetime
from app.core.config import settings
import logging
import uuid

logger = logging.getLogger(__name__)


def verify_access_token(token: str) -> uuid.UUID | None:
    """
    Verify JWT access token and extract user_id

    Args:
        token: JWT access token

    Returns:
        User UUID if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # Check token type
        if payload.get("type") != "access":
            logger.warning("Invalid token type")
            return None

        # Check expiration
        exp = payload.get("exp")
        if exp and datetime.utcnow().timestamp() > exp:
            logger.warning("Token expired")
            return None

        # Extract user_id
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("Missing user_id in token")
            return None

        return uuid.UUID(user_id)

    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None
    except ValueError as e:
        logger.warning(f"Invalid user_id format: {e}")
        return None
