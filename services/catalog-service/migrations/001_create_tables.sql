-- Catalog Service Database Migration

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Genres
CREATE TABLE genres (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_genres_slug ON genres(slug);

-- Persons (actors, directors, etc.)
CREATE TABLE persons (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(255) NOT NULL,
    birth_date TIMESTAMP,
    biography TEXT,
    photo_url VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_persons_full_name ON persons(full_name);

-- Movies
CREATE TABLE movies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    original_title VARCHAR(500),
    description TEXT,
    year INTEGER NOT NULL,
    duration INTEGER,
    poster_url VARCHAR(500),
    trailer_url VARCHAR(500),
    rating FLOAT,
    age_rating VARCHAR(10),
    is_published BOOLEAN NOT NULL DEFAULT FALSE,
    published_at TIMESTAMP,
    imdb_id VARCHAR(20) UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_movies_title ON movies(title);
CREATE INDEX idx_movies_year ON movies(year);
CREATE INDEX idx_movies_is_published ON movies(is_published);

-- Movie-Genre (many-to-many)
CREATE TABLE movie_genres (
    movie_id UUID NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
    genre_id UUID NOT NULL REFERENCES genres(id) ON DELETE CASCADE,
    PRIMARY KEY (movie_id, genre_id)
);

-- Movie-Person (many-to-many with role)
CREATE TABLE movie_persons (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    movie_id UUID NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
    person_id UUID NOT NULL REFERENCES persons(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    character_name VARCHAR(255)
);

CREATE INDEX idx_movie_persons_movie_id ON movie_persons(movie_id);
CREATE INDEX idx_movie_persons_person_id ON movie_persons(person_id);

-- Sample data
INSERT INTO genres (name, slug, description) VALUES
('Action', 'action', 'Action movies with thrilling sequences'),
('Comedy', 'comedy', 'Funny and humorous movies'),
('Drama', 'drama', 'Serious and emotional storytelling'),
('Sci-Fi', 'sci-fi', 'Science fiction and futuristic themes'),
('Horror', 'horror', 'Scary and suspenseful movies');
