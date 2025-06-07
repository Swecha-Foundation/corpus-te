# app/models/user.py
import uuid as uuid_pkg
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import date, datetime
from uuid import UUID

if TYPE_CHECKING:
    from .record import Record

class User(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid_pkg.uuid4, primary_key=True)
    phone: str = Field(max_length=20, unique=True, index=True)
    name: str = Field(max_length=100)
    email: Optional[str] = Field(default=None, max_length=100, unique=True, index=True)
    gender: Optional[str] = Field(default=None, max_length=20)
    date_of_birth: Optional[date] = Field(default=None)
    place: Optional[str] = Field(default=None, max_length=100)
    profile_picture_path: Optional[str] = Field(default=None, max_length=255)

    hashed_password: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    last_login_at: Optional[datetime] = Field(default=None)
    
    # Consent tracking
    has_given_consent: bool = Field(default=False)
    consent_given_at: Optional[datetime] = Field(default=None)

    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    # Many-to-many relationship with roles (will be defined after UserRoleLink import)
    
    # One-to-many relationship with records (as creator)
    records: List["Record"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[Record.user_id]"}
    )
    
    # One-to-many relationship with records (as reviewer)
    reviewed_records: List["Record"] = Relationship(
        back_populates="reviewer", 
        sa_relationship_kwargs={"foreign_keys": "[Record.reviewed_by]"}
    )
