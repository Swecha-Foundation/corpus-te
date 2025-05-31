from typing import Annotated
from sqlmodel import Session, create_engine
from fastapi import Depends
from app.core.config import settings

# Create engine with proper configuration
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=False  # Set to True for SQL debugging
)

def create_db_and_tables():
    """Create database tables if they don't exist"""
    from sqlmodel import SQLModel
    # Import all models to ensure they're registered
    from app.models import Role, User, Category, Record
    SQLModel.metadata.create_all(engine)

def get_session():
    """Dependency to get database session"""
    with Session(engine) as session:
        yield session

# Type annotation for session dependency
SessionDep = Annotated[Session, Depends(get_session)]
