from pydantic import BaseModel, EmailStr, Field, ConfigDict
from uuid import UUID
from datetime import date, datetime
from enum import Enum
from typing import Optional, List

# Import geographic schemas
from .geo_schemas import Coordinates, LocationSearch, BoundingBox

class RoleEnum(str, Enum):
    admin = "admin"
    user = "user"
    reviewer = "reviewer"

class MediaType(str, Enum):
    text = "text"
    audio = "audio"
    video = "video"
    image = "image"

# Authentication schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None

class LoginRequest(BaseModel):
    phone: str = Field(..., min_length=1, max_length=20)
    password: str = Field(..., min_length=1)

class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6, max_length=100)

class PasswordResetRequest(BaseModel):
    phone: str = Field(..., min_length=1, max_length=20)
    new_password: str = Field(..., min_length=6, max_length=100)

# Role schemas
class RoleBase(BaseModel):
    name: RoleEnum
    description: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class RoleRead(RoleBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# User schemas
class UserBase(BaseModel):
    phone: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    place: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)
    role_ids: List[int] = Field(default=[2])  # Default to user role (id=2)

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    place: Optional[str] = None
    is_active: Optional[bool] = None

class UserRead(UserBase):
    id: UUID
    is_active: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class UserWithRoles(UserRead):
    roles: List[RoleRead] = []

# User role management schemas
class UserRoleAssignment(BaseModel):
    user_id: UUID
    role_ids: List[int]

class UserRoleResponse(BaseModel):
    user_id: UUID
    roles: List[RoleRead]
    model_config = ConfigDict(from_attributes=True)

# Category schemas
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    published: bool = False
    rank: int = 0

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    published: Optional[bool] = None
    rank: Optional[int] = None

class CategoryRead(CategoryBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Record schemas
class RecordBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    media_type: MediaType
    file_url: Optional[str] = Field(None, max_length=500)
    file_name: Optional[str] = Field(None, max_length=255)
    file_size: Optional[int] = Field(None, ge=0)
    status: str = Field(default="pending", max_length=20)
    location: Optional[Coordinates] = None  # PostGIS Point coordinates
    reviewed: bool = Field(default=False)
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None

class RecordCreate(RecordBase):
    user_id: UUID
    category_id: UUID

class RecordUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    media_type: Optional[MediaType] = None
    file_url: Optional[str] = Field(None, max_length=500)
    file_name: Optional[str] = Field(None, max_length=255)
    file_size: Optional[int] = Field(None, ge=0)
    status: Optional[str] = Field(None, max_length=20)
    location: Optional[Coordinates] = None  # PostGIS Point coordinates
    reviewed: Optional[bool] = None
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None

class RecordRead(RecordBase):
    uid: UUID
    user_id: UUID
    category_id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Response schemas
class MessageResponse(BaseModel):
    message: str

class ErrorResponse(BaseModel):
    detail: str
