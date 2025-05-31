# PostgreSQL Setup Guide

This guide will help you migrate from SQLite to PostgreSQL for the Telugu Corpus Collections application.

## Prerequisites

1. **PostgreSQL Server**: Make sure PostgreSQL is installed and running
2. **Python Dependencies**: The required dependencies are already in `pyproject.toml`

## Step 1: Install PostgreSQL (if not already installed)

### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### macOS (using Homebrew):
```bash
brew install postgresql
brew services start postgresql
```

### Create a PostgreSQL user and database:
```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL shell:
CREATE USER postgres WITH PASSWORD 'your_password_here';
CREATE DATABASE corpus_te OWNER postgres;
GRANT ALL PRIVILEGES ON DATABASE corpus_te TO postgres;
\q
```

## Step 2: Update Environment Variables

The `.env` file has been updated with PostgreSQL configuration. Update the password:

```env
# PostgreSQL Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=corpus_te
DB_USER=postgres
DB_PASSWORD=your_actual_password_here  # 👈 Update this

# This URL is constructed automatically
DATABASE_URL="postgresql://postgres:your_actual_password_here@localhost:5432/corpus_te"
```

## Step 3: Test Connection and Setup Database

Use the provided setup script:

```bash
# Test PostgreSQL connection
python setup_postgresql.py --test-connection

# Create database if it doesn't exist
python setup_postgresql.py --create-db

# Run all setup steps at once
python setup_postgresql.py --all
```

## Step 4: Run Migrations

The migration system has been updated to handle the user-role many-to-many relationship:

```bash
# Run migrations to create tables
alembic upgrade head
```

## Step 5: Start the Application

```bash
uvicorn app.main:app --reload
```

## What Changed

### 1. Database Schema Changes
- **Users table**: Removed `role_id` column
- **New table**: `user_roles` for many-to-many relationship between users and roles
- **Records table**: Added `reviewed`, `reviewed_by`, `reviewed_at` columns
- **Roles enum**: Added `reviewer` role

### 2. Configuration Updates
- **Environment variables**: Added PostgreSQL connection parameters
- **Config class**: Updated to use environment variables
- **Alembic**: Updated to use PostgreSQL URLs

### 3. Migration Benefits
- **Data preservation**: Existing user-role relationships are migrated automatically
- **Foreign key support**: PostgreSQL handles constraints properly
- **Scalability**: Better performance for larger datasets
- **Relationships**: True many-to-many relationships between users and roles

## Troubleshooting

### Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check if PostgreSQL is listening
sudo netstat -plntu | grep :5432
```

### Permission Issues
```bash
# Grant permissions to user
sudo -u postgres psql
GRANT ALL PRIVILEGES ON DATABASE corpus_te TO postgres;
GRANT ALL ON SCHEMA public TO postgres;
```

### Migration Issues
```bash
# Check current migration status
alembic current

# Reset to specific migration
alembic downgrade base
alembic upgrade head
```

## API Changes

The API now supports multiple roles per user:

### User Model (Updated)
```json
{
  "id": "uuid",
  "name": "string",
  "email": "string",
  "roles": [
    {
      "id": 1,
      "name": "admin",
      "description": "Administrator role"
    }
  ]
}
```

### User-Role Management
- Users can have multiple roles
- Roles are managed through the many-to-many relationship
- Role assignment/removal requires separate endpoints (to be implemented)

## Next Steps

1. **Test the API endpoints** to ensure everything works correctly
2. **Implement role management endpoints** for assigning/removing roles
3. **Add authentication middleware** that supports multiple roles
4. **Update frontend** to handle multiple roles per user

## Files Modified

- `.env` - PostgreSQL configuration
- `app/core/config.py` - Configuration class updates
- `app/models/user.py` - Many-to-many relationship
- `app/models/role.py` - Updated relationships
- `app/models/associations.py` - Association table
- `alembic/env.py` - PostgreSQL support
- `alembic/versions/edb2014fe78f_*.py` - Migration for schema changes
