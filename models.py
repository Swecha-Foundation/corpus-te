from sqlalchemy import Column, String, Boolean, Integer, Date, ForeignKey, Enum, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from .database import Base

class RoleEnum(enum.Enum):
    admin = "admin"
    user = "user"

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Enum(RoleEnum), unique=True, nullable=False)
    description = Column(String, nullable=True)
    users = relationship("User", back_populates="role")

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    phone = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    gender = Column(String, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    place = Column(String, nullable=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    last_login_at = Column(Date, nullable=True)

    role = relationship("Role", back_populates="users")
    records = relationship("Record", back_populates="user")

class Category(Base):
    __tablename__ = "categories"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    published = Column(Boolean, default=False)
    rank = Column(Integer, default=0)

    records = relationship("Record", back_populates="category")

class MediaType(enum.Enum):
    text = "text"
    audio = "audio"
    video = "video"
    image = "image"

class Record(Base):
    __tablename__ = "records"
    uid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(Enum(MediaType), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False)
    geo_lat = Column(Float, nullable=True)
    geo_lng = Column(Float, nullable=True)
    storage_path = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending/uploaded/failed

    user = relationship("User", back_populates="records")
    category = relationship("Category", back_populates="records")