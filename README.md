# Telugu Corpus Collections API

A FastAPI-based backend service for managing Telugu corpus collections, supporting text, audio, video, and image submissions with PostgreSQL database and JWT authentication.

## Features

- **Multi-media Support**: Handle text, audio, video, and image submissions
- **User Management**: Many-to-many role-based user system (admin/user/reviewer)
- **Authentication**: JWT-based authentication and authorization
- **OTP Authentication**: SMS-based OTP verification for secure phone number authentication
- **Category Management**: Organize submissions by categories
- **Record Review System**: Support for content review workflows
- **Geolocation & PostGIS**: Advanced geographic data handling with spatial queries and indexing
- **PostgreSQL Database**: Robust database with proper foreign key constraints
- **File Storage**: Support for local and MinIO/S3 storage
- **RESTful API**: Full CRUD operations with OpenAPI documentation

## Project Structure

```
corpus-te/
├── app/
│   ├── main.py              # FastAPI application
│   ├── core/
│   │   ├── config.py        # Settings and configuration
│   │   ├── auth.py          # JWT authentication utilities
│   │   ├── exceptions.py    # Custom exceptions
│   │   ├── logging_config.py # Logging setup
│   │   └── rbac_fastapi.py  # Role-based access control utilities
│   ├── db/
│   │   └── session.py       # Database session
│   ├── models/
│   │   ├── __init__.py      # Database models
│   │   ├── associations.py  # Many-to-many association tables
│   │   ├── user.py          # User model
│   │   ├── role.py          # Role model
│   │   ├── category.py      # Category model
│   │   ├── record.py        # Record model
│   │   └── otp.py           # OTP model for authentication
│   ├── schemas/
│   │   ├── __init__.py      # Pydantic schemas
│   │   ├── geo_schemas.py   # Geographic coordinate schemas
│   │   └── otp.py           # OTP request/response schemas
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py          # Legacy auth endpoints
│   │   └── v1/
│   │       ├── api.py       # API router
│   │       ├── __init__.py
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── auth.py      # Authentication endpoints (with OTP)
│   │           ├── users.py     # User management endpoints
│   │           ├── roles.py     # Role management endpoints
│   │           ├── categories.py # Category endpoints
│   │           ├── records.py   # Record endpoints
│   │           └── system_rbac.py # RBAC system endpoints
│   ├── services/            # Business logic services
│   │   └── otp_service.py   # OTP authentication service
│   └── utils/               # Utility modules
│       ├── __init__.py
│       ├── cleanup_storage.py      # Storage cleanup utilities
│       ├── hetzner_storage.py      # Hetzner object storage integration
│       ├── postgis_utils.py        # PostGIS geographic utilities
│       └── record_file_generator.py # Record file generation utilities
├── alembic/                 # Database migrations
│   ├── versions/            # Migration files
│   ├── alembic.ini          # Alembic configuration
│   └── env.py              # Migration environment
├── docs/                    # Documentation and guides
│   ├── demo_rbac_optimization.py            # RBAC demo script
│   ├── example_hetzner_storage.py           # Hetzner storage examples
│   ├── example_record_file_generator.py     # Record generator examples
│   ├── generate_record_files.py             # File generation script
│   ├── otp_demo.py                          # OTP demo script
│   ├── HETZNER_STORAGE_GUIDE.md            # Hetzner storage setup guide
│   ├── OTP_AUTHENTICATION_GUIDE.md         # OTP authentication guide
│   ├── OTP_IMPLEMENTATION_SUMMARY.md       # OTP implementation summary
│   ├── OTP_TESTING_RESULTS.md              # OTP testing results
│   ├── Plan.md                             # Project development plan
│   ├── POSTGIS_INTEGRATION_SUMMARY.md      # PostGIS integration summary
│   ├── POSTGRESQL_SETUP.md                 # PostgreSQL setup guide
│   ├── RBAC_GUIDE.md                       # Role-based access control guide
│   ├── RBAC_OPTIMIZATION_SUMMARY.md        # RBAC optimization summary
│   ├── RECORD_FILE_GENERATOR_GUIDE.md      # Record file generator guide
│   └── RECORD_FILE_GENERATOR_COMPLETION_SUMMARY.md # Generator completion summary
├── tests/                   # Test files
│   ├── create_test_data.py              # Test data creation script
│   ├── test_hetzner_storage.py          # Hetzner storage tests
│   ├── test_otp_api.py                  # OTP API tests
│   ├── test_postgis_api.py              # PostGIS API tests
│   ├── test_postgis_integration.py      # PostGIS integration tests
│   ├── test_updated_api_endpoints.py    # Updated API endpoint tests
│   └── verify_test_data.py              # Test data verification
├── logs/                    # Application logs
├── main.py                  # Application entry point
├── setup_postgresql.py      # PostgreSQL setup automation script
├── pyproject.toml           # Project dependencies
├── uv.lock                  # UV dependency lock file
├── LICENSE                  # License file
└── README.md               # This file
```

## Key Features

### 🔐 OTP Authentication System
Complete SMS-based One-Time Password authentication system for secure phone number verification:
- **SMS Integration**: Real SMS delivery via Ozonetel API
- **Security**: HMAC-SHA256 OTP hashing with salts and time-based expiry
- **Rate Limiting**: Built-in protection against spam and abuse
- **Phone Validation**: International phone number format validation
- **JWT Integration**: Seamless token generation after successful verification

📖 **[Detailed OTP Authentication Guide](docs/OTP_AUTHENTICATION_GUIDE.md)**

### 🌍 PostGIS Geographic Integration
Advanced spatial data handling with PostGIS for location-based features:
- **Spatial Queries**: Efficient geographic data operations and indexing
- **Location Services**: Precise coordinate handling and validation
- **Performance Optimization**: Specialized indexes for geographic queries
- **Data Integrity**: Robust validation for coordinate formats and ranges

📖 **[PostGIS Integration Guide](docs/POSTGIS_INTEGRATION.md)**

### 👥 Role-Based Access Control (RBAC)
Comprehensive user management system with flexible permissions:
- **Multi-Role Support**: Admin, User, and Reviewer roles with granular permissions
- **Performance Optimized**: Efficient user-role queries and caching strategies
- **Scalable Architecture**: Designed for large-scale user management

📖 **[RBAC Performance Optimization Guide](docs/RBAC_PERFORMANCE_OPTIMIZATION.md)**

## Quick Start

1. **Clone and navigate to the project:**
   ```bash
   cd corpus-te
   ```

2. **Create a virtual environment:**
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   uv pip install -e .
   ```

4. **Install development dependencies:**
   ```bash
   uv pip install -e ".[dev]"
   ```

   *Alternative: Install all dependencies with uv sync (if using uv.lock):*
   ```bash
   uv sync --dev
   ```

4. **Set up PostgreSQL database:**
   
   See [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md) for detailed PostgreSQL installation and setup instructions.

5. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration (see Configuration section below)
   ```

6. **Generate a secure secret key for JWT:**
   For Bash
   ```bash
   openssl rand -hex 32
   ```
   OR using Python
   ```python
         import secrets
         secrets.token_urlsafe(32)
   ```
   Update the `APP_SECRET_KEY` in your `.env` file with the generated key.

   Example:
   ```bash
   APP_SECRET_KEY="your-generated-secret-key"
   ```

6. **Set up PostgreSQL database with automated script (Recommended):**

   Use the provided setup script to automatically create the database and run initial setup:

   ```bash
   # Run complete database setup (recommended for first-time setup)
   python setup_postgresql.py --all
   ```
   
   Or run individual steps:
   ```bash
   # Test PostgreSQL connection
   python setup_postgresql.py --test-connection
   
   # Create database if it doesn't exist
   python setup_postgresql.py --create-db
   
   # Run database migrations
   python setup_postgresql.py --migrate
   
   # Seed initial data (roles)
   python setup_postgresql.py --seed
   ```
   
   **Alternative: Manual database setup:**
   
   If you prefer manual setup, see [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md) for detailed PostgreSQL installation and setup instructions, then run:
   ```bash
   alembic upgrade head
   ```

7. **Run the application:**
   ```bash
   python main.py
   ```

8. **Access the API documentation:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Development

### Installing additional dependencies:
```bash
uv pip install package-name
```

### Installing development dependencies:
```bash
uv pip install -e ".[dev]"
```

### Running with auto-reload:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### PostgreSQL Setup Script

The `setup_postgresql.py` script provides automated database setup and testing functionality:

```bash
# Show current database configuration
python setup_postgresql.py

# Run complete setup (creates DB, runs migrations, seeds data)
python setup_postgresql.py --all

# Individual operations:
python setup_postgresql.py --test-connection    # Test PostgreSQL server connection
python setup_postgresql.py --create-db          # Create database if missing
python setup_postgresql.py --migrate            # Run Alembic migrations
python setup_postgresql.py --seed               # Seed initial roles data
```

**What the script does:**
- **Connection Testing**: Verifies PostgreSQL server accessibility
- **Database Creation**: Creates the target database if it doesn't exist
- **Migration Execution**: Runs all pending Alembic migrations
- **Data Seeding**: Creates initial roles (admin, user, reviewer)
- **Error Handling**: Provides clear feedback on setup status

**Prerequisites:**
- PostgreSQL server running and accessible
- Correct database credentials in `.env` file
- `psycopg2-binary` installed (included in project dependencies)

### Database migrations:

Before running the migrations check [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md) for PostgreSQL setup.

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Check migration status
alembic current

# Downgrade to previous migration
alembic downgrade -1
```

### Running tests:
```bash
pytest
```

### Code formatting with uv:
```bash
uv pip install black isort
black .
isort .
```

### Updating dependencies:
```bash
uv pip install --upgrade package-name
```

## Configuration

Key environment variables in `.env` file:

### Database Configuration
- `DATABASE_URL`: PostgreSQL connection string
- `DB_HOST`: PostgreSQL host (default: localhost)
- `DB_PORT`: PostgreSQL port (default: 5432)
- `DB_NAME`: Database name
- `DB_USER`: PostgreSQL username
- `DB_PASSWORD`: PostgreSQL password

### Application Settings
- `PROJECT_NAME`: Application name
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Authentication
- `APP_SECRET_KEY`: JWT secret key (change in production)
- `ALGORITHM`: JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time (default: 30)

### CORS Configuration
- `BACKEND_CORS_ORIGINS`: Comma-separated list of allowed origins

### Object Storage (Optional)
- `HZ_OBJ_ACCESS_KEY`: Object storage access key
- `HZ_OBJ_SECRET_KEY`: Object storage secret key
- `HZ_OBJ_API_TOKEN`: Object storage API token
- `HZ_OBJ_ENDPOINT`: Object storage endpoint
- `HZ_OBJ_BUCKET_NAME`: Object storage bucket name

### File Upload Settings
- `MAX_FILE_SIZE`: Maximum file size in bytes (default: 104857600 = 100MB)

Example `.env` file:
```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=corpus_te
DB_USER=postgres
DB_PASSWORD=your_password_here
DATABASE_URL="postgresql://postgres:your_password_here@localhost:5432/corpus_te"

# Application Settings
PROJECT_NAME="Telugu Corpus Collections API"
LOG_LEVEL="WARNING"

# JWT Configuration
APP_SECRET_KEY="your-secret-key-here"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS Origins
BACKEND_CORS_ORIGINS="http://localhost:3000,http://localhost:8080"

# File Upload Settings
MAX_FILE_SIZE=104857600
```

## API Endpoints

### Core Endpoints
- `GET /`: Welcome message
- `GET /health`: Health check
- `GET /docs`: Swagger UI API documentation
- `GET /redoc`: ReDoc API documentation

### Authentication (`/api/v1/auth/`)
- `POST /api/v1/auth/login`: User login (returns JWT token)
- `POST /api/v1/auth/register`: User registration

### User Management (`/api/v1/users/`)
- `GET /api/v1/users/`: List all users (with pagination)
- `POST /api/v1/users/`: Create a new user
- `GET /api/v1/users/{user_id}`: Get user by ID
- `PUT /api/v1/users/{user_id}`: Update user
- `DELETE /api/v1/users/{user_id}`: Delete user
- `GET /api/v1/users/{user_id}/with-roles`: Get user with roles populated
- `GET /api/v1/users/phone/{phone}`: Get user by phone number

### User Role Management (`/api/v1/users/{user_id}/roles/`)
- `GET /api/v1/users/{user_id}/roles`: Get user's roles
- `POST /api/v1/users/{user_id}/roles`: Assign roles to user (replace all)
- `PUT /api/v1/users/{user_id}/roles/add`: Add a role to user
- `DELETE /api/v1/users/{user_id}/roles/{role_id}`: Remove role from user

### Role Management (`/api/v1/roles/`)
- `GET /api/v1/roles/`: List all roles
- `POST /api/v1/roles/`: Create a new role
- `GET /api/v1/roles/{role_id}`: Get role by ID
- `PUT /api/v1/roles/{role_id}`: Update role
- `DELETE /api/v1/roles/{role_id}`: Delete role

### Category Management (`/api/v1/categories/`)
- `GET /api/v1/categories/`: List all categories
- `POST /api/v1/categories/`: Create a new category
- `GET /api/v1/categories/{category_id}`: Get category by ID
- `PUT /api/v1/categories/{category_id}`: Update category
- `DELETE /api/v1/categories/{category_id}`: Delete category

### Record Management (`/api/v1/records/`)
- `GET /api/v1/records/`: List all records
- `POST /api/v1/records/`: Create a new record
- `GET /api/v1/records/{record_id}`: Get record by ID
- `PUT /api/v1/records/{record_id}`: Update record
- `DELETE /api/v1/records/{record_id}`: Delete record

## Database Setup

This application uses PostgreSQL as the primary database. For detailed setup instructions, see [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md).

### Quick PostgreSQL Setup
1. Install PostgreSQL on your system
2. Create a database and user:
   ```sql
   CREATE DATABASE corpus_te;
   CREATE USER corpus_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE corpus_te TO corpus_user;
   ```
3. Update your `.env` file with the database credentials
4. Run migrations: `alembic upgrade head`

### Database Schema
The application includes:
- **Users**: User accounts with many-to-many role relationships
- **Roles**: System roles (admin, user, reviewer)
- **Categories**: Content organization categories
- **Records**: Media submissions with metadata
- **User-Role Association**: Many-to-many relationship table

## Authentication

The API uses JWT (JSON Web Tokens) for authentication:

1. **Register/Login**: Use `/api/v1/auth/register` or `/api/v1/auth/login`
2. **Get Token**: Login returns an access token
3. **Use Token**: Include in Authorization header: `Bearer <token>`
4. **Protected Endpoints**: Most endpoints require authentication

Example authentication flow:
```bash
# Register a new user
# role_ids 1 for admin
curl -X 'POST' \
  'http://localhost:8000/api/v1/users/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "phone": "1234567890",
  "name": "John",
  "email": "John@example.com",
  "gender": "male",
  "date_of_birth": "2025-07-01",
  "place": "Telangana",
  "password": "password",
  "role_ids": [
    1
  ],
  "has_given_consent": true
}'

# Login to get token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"phone": "1234567890", "password": "password"}'

# Use token in requests
curl -X GET "http://localhost:8000/api/v1/users/" \
  -H "Authorization: Bearer <your-token-here>"
```

## Troubleshooting

### PostgreSQL Setup Issues

**Database Connection Fails:**
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Test connection manually
psql -h localhost -U postgres -d postgres
```

**Setup Script Issues:**
```bash
# Check database configuration
python setup_postgresql.py

# Run with verbose output
python setup_postgresql.py --test-connection
```

**Common Error Solutions:**

1. **"PostgreSQL server connection failed"**
   - Ensure PostgreSQL is installed and running
   - Check credentials in `.env` file
   - Verify host and port settings

2. **"Database connection failed"**
   - Run `python setup_postgresql.py --create-db` first
   - Check if database name matches `.env` configuration

3. **"Migration failed"**
   - Ensure database exists and is accessible
   - Check for conflicting migrations with `alembic current`
   - Reset migrations if needed: `alembic downgrade base`

4. **"Permission denied"**
   - Ensure PostgreSQL user has CREATE DATABASE privileges
   - Check PostgreSQL authentication settings in `pg_hba.conf`

5. **"password authentication failed"**
   - verify your database password
   - for unix based systems like linux
        sudo sed -i /etc/postgresql/17/main/pg_hba.conf  s/peer/scram-sha-256/g
        sudo systemctl restart postgresql

**Database Reset (Development Only):**
```bash
# Drop and recreate database
psql -h localhost -U postgres -c "DROP DATABASE IF EXISTS corpus_te;"
python setup_postgresql.py --all
```

### Application Issues

**Import Errors:**
- Ensure virtual environment is activated
- Install dependencies: `uv sync --dev`

**Port Already in Use:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

For more detailed troubleshooting, see [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md).

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the terms specified in the [LICENSE](LICENSE) file.
