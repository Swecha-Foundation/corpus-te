# app/models/category.py
import uuid as uuid_pkg
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from uuid import UUID

if TYPE_CHECKING:
    from .record import Record

class Category(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid_pkg.uuid4, primary_key=True)
    name: str = Field(max_length=100, unique=True, index=True)
    title: str = Field(max_length=200)
    description: Optional[str] = Field(default=None, max_length=500)
    published: bool = Field(default=False)
    rank: int = Field(default=0)

    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    # One-to-many relationship with records
    records: List["Record"] = Relationship(back_populates="category")
