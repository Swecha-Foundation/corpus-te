from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re

class OTPSendRequest(BaseModel):
    phone_number: str = Field(..., description="Phone number with country code (e.g., +919177980938)")
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        # Remove spaces and dashes
        cleaned = re.sub(r'[\s\-\(\)]', '', v)
        
        # Check if it's a valid phone number format
        if not re.match(r'^\+?[1-9]\d{1,14}$', cleaned):
            raise ValueError('Invalid phone number format')
        
        # Ensure it starts with country code
        if not cleaned.startswith('+'):
            if cleaned.startswith('91') and len(cleaned) == 12:  # Indian number
                cleaned = '+' + cleaned
            elif len(cleaned) == 10:  # Assume Indian number
                cleaned = '+91' + cleaned
            else:
                raise ValueError('Phone number must include country code')
        
        return cleaned

class OTPResponse(BaseModel):
    status: str
    message: str
    reference_id: Optional[str] = None

class OTPVerifyRequest(BaseModel):
    phone_number: str = Field(..., description="Phone number with country code")
    otp_code: str = Field(..., min_length=4, max_length=8, description="OTP code")
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        # Reuse the validation logic from OTPSendRequest
        return OTPSendRequest.validate_phone_number(v)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    phone_number: str
