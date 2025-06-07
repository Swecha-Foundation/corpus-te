import os
from typing import Optional

# Load environment variables from .env if it exists
from dotenv import load_dotenv
load_dotenv()

class Settings:
    # Project settings
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Telugu Corpus Collections API")
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Database settings - Individual components for PostgreSQL
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_NAME: str = os.getenv("DB_NAME", "corpus_te")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "password")
    
    # Database URL - prefer from environment, fallback to constructed
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    
    # CORS settings
    @property
    def cors_origins(self) -> list[str]:
        """Get CORS origins from environment or use defaults."""
        cors_str = os.getenv("BACKEND_CORS_ORIGINS")
        if cors_str:
            return [origin.strip() for origin in cors_str.split(",")]
        return ["*"]
    
    # MinIO/S3 settings (Hetzner Object Storage)
    MINIO_ENDPOINT: Optional[str] = os.getenv("HZ_OBJ_ENDPOINT")
    MINIO_ACCESS_KEY: Optional[str] = os.getenv("HZ_OBJ_ACCESS_KEY")
    MINIO_SECRET_KEY: Optional[str] = os.getenv("HZ_OBJ_SECRET_KEY")
    MINIO_BUCKET_NAME: str = os.getenv("HZ_OBJ_BUCKET_NAME", "corpus-data")
    MINIO_USE_SSL: bool = os.getenv("HZ_OBJ_USE_SSL", "true").lower() in ("true", "1", "yes")
    
    # JWT settings
    SECRET_KEY: str = os.getenv("APP_SECRET_KEY", "change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "WARNING")
    
    # File upload settings
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_AUDIO_EXTENSIONS: set[str] = {".mp3", ".wav", ".m4a", ".ogg"}
    ALLOWED_VIDEO_EXTENSIONS: set[str] = {".mp4", ".avi", ".mov", ".mkv"}
    ALLOWED_IMAGE_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png", ".gif"}
    
    # OTP Service settings
    OTP_USER_NAME: str = os.getenv("OTP_USER_NAME", "")
    OTP_ENTITY_ID: str = os.getenv("OTP_ENTITY_ID", "")
    OTP_TEMPLATE_ID: str = os.getenv("OTP_TEMPLATE_ID", "")
    OTP_SMS_TEXT: str = os.getenv("OTP_SMS_TEXT", "Your OTP is {otp}. Valid for 5 minutes.")
    OTP_API_KEY: str = os.getenv("OTP_API_KEY", "")
    OTP_SMS_TYPE: str = os.getenv("OTP_SMS_TYPE", "0")
    OTP_SENDER_ID: str = os.getenv("OTP_SENDER_ID", "")
    OTP_SERVICE_URL: str = os.getenv("OTP_SERVICE_URL", "")
    OTP_EXPIRY_MINUTES: int = int(os.getenv("OTP_EXPIRY_MINUTES", "5"))
    OTP_MAX_ATTEMPTS: int = int(os.getenv("OTP_MAX_ATTEMPTS", "3"))
    OTP_RATE_LIMIT_MINUTES: int = int(os.getenv("OTP_RATE_LIMIT_MINUTES", "1"))

settings = Settings()
