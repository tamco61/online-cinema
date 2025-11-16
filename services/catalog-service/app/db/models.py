"""Database models for Catalog Service."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .session import Base


class PersonRole(str, enum.Enum):
    """Person role in movie."""

    ACTOR = "actor"
    DIRECTOR = "director"
    PRODUCER = "producer"
    WRITER = "writer"


# Association tables for many-to-many relationships

movie_genres = Table(
    "movie_genres",
    Base.metadata,
    mapped_column("movie_id", UUID(as_uuid=True), ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    mapped_column("genre_id", UUID(as_uuid=True), ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
)


class MoviePerson(Base):
    """Association table for movie-person with role."""

    __tablename__ = "movie_persons"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    movie_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("movies.id", ondelete="CASCADE"),
        nullable=False,
    )

    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("persons.id", ondelete="CASCADE"),
        nullable=False,
    )

    role: Mapped[PersonRole] = mapped_column(
        String(20),
        nullable=False,
    )

    character_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Character name for actors",
    )

    # Relationships
    movie: Mapped["Movie"] = relationship("Movie", back_populates="person_associations")
    person: Mapped["Person"] = relationship("Person", back_populates="movie_associations")


class Genre(Base):
    """Genre model."""

    __tablename__ = "genres"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    movies: Mapped[list["Movie"]] = relationship(
        "Movie",
        secondary=movie_genres,
        back_populates="genres",
    )

    def __repr__(self) -> str:
        return f"<Genre(id={self.id}, name='{self.name}')>"


class Person(Base):
    """Person model (actors, directors, etc.)."""

    __tablename__ = "persons"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    birth_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    biography: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    photo_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    movie_associations: Mapped[list["MoviePerson"]] = relationship(
        "MoviePerson",
        back_populates="person",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Person(id={self.id}, name='{self.full_name}')>"


class Movie(Base):
    """Movie model."""

    __tablename__ = "movies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Basic info
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
    )

    original_title: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    # Media info
    duration: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Duration in minutes",
    )

    poster_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    trailer_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Ratings
    rating: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Average rating (e.g., IMDb)",
    )

    age_rating: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="Age rating (e.g., PG-13, R)",
    )

    # Publication status
    is_published: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    # Metadata
    imdb_id: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        unique=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    genres: Mapped[list["Genre"]] = relationship(
        "Genre",
        secondary=movie_genres,
        back_populates="movies",
    )

    person_associations: Mapped[list["MoviePerson"]] = relationship(
        "MoviePerson",
        back_populates="movie",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Movie(id={self.id}, title='{self.title}', year={self.year})>"
