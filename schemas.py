from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import date
from enum import Enum

class RoleEnum(str, Enum):
    admin = "admin"
    user = "user"

# Base user schema
class UserBase(BaseModel):
    phone: str = Field(..., example="+919876543210")
    name: str
    email: EmailStr | None
    gender: str | None
    date_of_birth: date | None
    place: str | None

# properties to receive on user creation
class UserCreate(UserBase):
    role: RoleEnum = Field(default=RoleEnum.user)

# properties to return to client
class UserRead(UserBase):
    id: UUID
    role: RoleEnum
    is_active: bool
    last_login_at: date | None

    class Config:
        orm_mode = True

class CategoryBase(BaseModel):
    name: str
    title: str
    description: str | None = None
    published: bool = False
    rank: int = 0

class CategoryCreate(CategoryBase):
    pass

class CategoryRead(CategoryBase):
    id: UUID
    class Config:
        orm_mode = True

class MediaType(str, Enum):
    text = "text"
    audio = "audio"
    video = "video"
    image = "image"

class RecordBase(BaseModel):
    type: MediaType
    user_id: UUID
    category_id: UUID
    geo_lat: float | None
    geo_lng: float | None

class RecordCreate(RecordBase):
    pass

class RecordRead(RecordBase):
    uid: UUID
    storage_path: str | None
    status: str

    class Config:
        orm_mode = True