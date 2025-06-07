# app/models/role.py
from sqlmodel import SQLModel, Field
from typing import Optional, TYPE_CHECKING
import enum

if TYPE_CHECKING:
    pass

class RoleEnum(str, enum.Enum):
    admin = "admin"
    user = "user"
    reviewer = "reviewer"

class Role(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: RoleEnum = Field(unique=True, index=True)
    description: Optional[str] = Field(default=None, max_length=255)
    
    # Many-to-many relationship with users (will be defined after UserRoleLink import)
