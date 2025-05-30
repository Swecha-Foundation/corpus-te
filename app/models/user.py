# app/models/user.py
import uuid as uuid_pkg
from sqlalchemy import Column, String, Date, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID # For other DBs, consider sqlalchemy_utils.UUIDType
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base
# from app.models.role import Role # Role import for type hinting if needed, ForeignKey uses string

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4, index=True)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=True)
    email = Column(String(100), unique=True, index=True, nullable=True)
    gender = Column(String(10), nullable=True) # e.g., "male", "female", "other", "prefer_not_to_say"
    date_of_birth = Column(Date, nullable=True)
    place = Column(String(100), nullable=True)
    profile_picture_path = Column(String(255), nullable=True) # Path in MinIO

    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    # role = relationship("Role", back_populates="users") # We'll add relationships later

    hashed_password = Column(String(255), nullable=True) # For potential future password auth
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
