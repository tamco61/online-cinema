# Database Migrations

This directory contains SQL migrations for the Auth Service database.

## Migrations

- `001_create_users_table.sql` - Creates the users table with indexes and triggers

## Running Migrations

### Manual Execution

```bash
# Connect to PostgreSQL
psql -U auth_user -d auth_db -h localhost

# Run migration
\i migrations/001_create_users_table.sql
```

### Using psql from command line

```bash
psql -U auth_user -d auth_db -h localhost -f migrations/001_create_users_table.sql
```

### Recommended: Use Alembic (Python)

For production, it's recommended to use Alembic for database migrations:

```bash
# Install Alembic
pip install alembic

# Initialize Alembic
alembic init alembic

# Configure alembic.ini with your database URL
# Edit alembic/env.py to import your models

# Create migration
alembic revision --autogenerate -m "create users table"

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Migration Naming Convention

Migrations follow the pattern: `NNN_description.sql`

- `NNN` - Three-digit sequence number (001, 002, etc.)
- `description` - Brief description in snake_case

## Schema Changes

When modifying the database schema:

1. Create a new migration file with the next sequence number
2. Include both UP and DOWN migrations (or create separate rollback file)
3. Test the migration on a development database
4. Document any breaking changes
5. Update the application models if needed

## Database Schema

### users table

| Column          | Type         | Description                    |
|----------------|--------------|--------------------------------|
| id             | UUID         | Primary key                    |
| email          | VARCHAR(255) | Unique user email             |
| password_hash  | VARCHAR(255) | Bcrypt hashed password        |
| is_active      | BOOLEAN      | Account active status          |
| oauth_provider | VARCHAR(50)  | OAuth provider (google, etc.)  |
| oauth_id       | VARCHAR(255) | OAuth provider user ID         |
| created_at     | TIMESTAMP    | Account creation time          |
| updated_at     | TIMESTAMP    | Last update time               |

### Indexes

- `idx_users_email` - On email column (for login lookups)
- `idx_users_is_active` - On is_active column (for filtering)
- `idx_users_oauth_id` - On oauth_id column (for OAuth lookups)
- `idx_users_created_at` - On created_at column (for sorting)
