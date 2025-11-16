"""Schemas module."""

from app.schemas.movie import (
    MovieCreate,
    MovieDetailResponse,
    MovieListResponse,
    MovieResponse,
    MovieUpdate,
)

__all__ = [
    "MovieCreate",
    "MovieUpdate",
    "MovieResponse",
    "MovieDetailResponse",
    "MovieListResponse",
]
