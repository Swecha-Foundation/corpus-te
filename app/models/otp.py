from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field
import uuid

class OTPBase(SQLModel):
    phone_number: str = Field(index=True, description="Phone number (with country code)")
    otp_hash: str = Field(description="Hashed OTP code")
    attempts: int = Field(default=0, description="Number of verification attempts")
    is_verified: bool = Field(default=False, description="Whether OTP was successfully verified")
    expires_at: datetime = Field(description="OTP expiry timestamp")
    reference_id: Optional[str] = Field(default=None, description="SMS service reference ID")

class OTP(OTPBase, table=True):
    __tablename__ = "otp"
    
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class OTPCreate(OTPBase):
    pass

class OTPRead(OTPBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
