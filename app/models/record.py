# app/models/record.py
import uuid as uuid_pkg
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from uuid import UUID
import enum

if TYPE_CHECKING:
    from .user import User
    from .category import Category

class MediaType(str, enum.Enum):
    text = "text"
    audio = "audio"
    video = "video"
    image = "image"

class Record(SQLModel, table=True):
    uid: Optional[UUID] = Field(default_factory=uuid_pkg.uuid4, primary_key=True)
    
    # Main content fields
    title: str = Field(max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    
    # Media and file info
    media_type: MediaType = Field(index=True)
    file_url: Optional[str] = Field(default=None, max_length=500)
    file_name: Optional[str] = Field(default=None, max_length=255)
    file_size: Optional[int] = Field(default=None)
    
    status: str = Field(default="pending", max_length=20)  # pending/uploaded/failed

    # Location data
    geo_lat: Optional[float] = Field(default=None)
    geo_lng: Optional[float] = Field(default=None)

    # Foreign keys
    user_id: UUID = Field(foreign_key="user.id")
    category_id: UUID = Field(foreign_key="category.id")
    reviewed: bool = Field(default=False)
    reviewed_by: Optional[UUID] = Field(default=None, foreign_key="user.id")

    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = Field(default=None)

    # Relationships - explicitly specify foreign keys to avoid ambiguity
    user: Optional["User"] = Relationship(
        back_populates="records",
        sa_relationship_kwargs={"foreign_keys": "[Record.user_id]"}
    )
    reviewer: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Record.reviewed_by]"}
    )
    category: Optional["Category"] = Relationship(back_populates="records")
