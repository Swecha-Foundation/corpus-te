# app/models/associations.py
from sqlmodel import SQLModel, Field
from uuid import UUID
from typing import Optional

# Association table for many-to-many relationship between User and Role
class UserRoleLink(SQLModel, table=True):
    __tablename__ = "user_roles"
    
    user_id: Optional[UUID] = Field(default=None, foreign_key="user.id", primary_key=True)
    role_id: Optional[int] = Field(default=None, foreign_key="role.id", primary_key=True)
