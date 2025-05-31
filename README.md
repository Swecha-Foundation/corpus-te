# Telugu Corpus Collections API

A FastAPI-based backend service for managing Telugu corpus collections, supporting text, audio, video, and image submissions with PostgreSQL database and JWT authentication.

## Features

- **Multi-media Support**: Handle text, audio, video, and image submissions
- **User Management**: Many-to-many role-based user system (admin/user/reviewer)
- **Authentication**: JWT-based authentication and authorization
- **Category Management**: Organize submissions by categories
- **Record Review System**: Support for content review workflows
- **Geolocation**: Track submission locations
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
│   │   └── logging_config.py # Logging setup
│   ├── db/
│   │   └── session.py       # Database session
│   ├── models/
│   │   ├── __init__.py      # Database models
│   │   ├── associations.py  # Many-to-many association tables
│   │   ├── user.py          # User model
│   │   ├── role.py          # Role model
│   │   ├── category.py      # Category model
│   │   └── record.py        # Record model
│   ├── schemas/
│   │   └── __init__.py      # Pydantic schemas
│   ├── api/
│   │   └── v1/
│   │       ├── api.py       # API router
│   │       └── endpoints/
│   │           ├── auth.py      # Authentication endpoints
│   │           ├── users.py     # User management endpoints
│   │           ├── roles.py     # Role management endpoints
│   │           ├── categories.py # Category endpoints
│   │           └── records.py   # Record endpoints
│   └── services/            # Business logic services
├── alembic/                 # Database migrations
│   ├── versions/            # Migration files
│   ├── alembic.ini          # Alembic configuration
│   └── env.py              # Migration environment
├── tests/                   # Test files
├── logs/                    # Application logs
├── main.py                  # Application entry point
├── pyproject.toml           # Project dependencies
├── POSTGRESQL_SETUP.md      # PostgreSQL setup guide
└── README.md               # This file
```

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

6. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

7. **Run the application:**
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

### Database migrations:
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
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"phone": "1234567890", "name": "John Doe", "password": "secure123"}'

# Login to get token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"phone": "1234567890", "password": "secure123"}'

# Use token in requests
curl -X GET "http://localhost:8000/api/v1/users/" \
  -H "Authorization: Bearer <your-token-here>"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the terms specified in the [LICENSE](LICENSE) file.