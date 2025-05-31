# app/models/__init__.py
from .associations import UserRoleLink
from .role import Role, RoleEnum
from .user import User
from .category import Category
from .record import Record, MediaType

# Now define the many-to-many relationships after all models are imported
from sqlmodel import Relationship
from typing import List

# Add the relationship fields to the models
Role.users = Relationship(back_populates="roles", link_model=UserRoleLink)
User.roles = Relationship(back_populates="users", link_model=UserRoleLink)

# Import all models to ensure they're registered with SQLModel
__all__ = [
    "Role",
    "RoleEnum", 
    "User",
    "UserRoleLink",
    "Category", 
    "Record",
    "MediaType"
]
