from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI Backend App"
    API_V1_STR: str = "/api/v1"

    # Database settings
    DATABASE_URL: str = "sqlite:///./test.db" 
    # Example for PostgreSQL: DATABASE_URL: str = "postgresql://user:password@host:port/dbname"

    # MinIO settings
    MINIO_ENDPOINT: Optional[str] = None # e.g., "minio.example.com:9000" or "localhost:9000"
    MINIO_ACCESS_KEY: Optional[str] = None
    MINIO_SECRET_KEY: Optional[str] = None
    MINIO_BUCKET_RECORDS_DEV: str = "records-dev"
    MINIO_BUCKET_RECORDS_PROD: str = "records-prod"
    MINIO_USE_SSL: bool = True # Set to False for local MinIO without SSL

    # JWT settings
    JWT_SECRET_KEY: str = "a_very_secret_key_that_should_be_changed" # IMPORTANT: Change this in production!
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 # Access token validity in minutes
    OTP_EXPIRE_MINUTES: int = 5 # OTP validity in minutes
    
    # Add other settings as needed

    class Config:
        env_file = ".env" # pydantic-settings will automatically load from .env if python-dotenv is installed
        env_file_encoding = 'utf-8'
        extra = 'ignore' # Ignore extra fields from .env

settings = Settings()
