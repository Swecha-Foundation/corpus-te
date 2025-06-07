import random
import hashlib
import hmac
import requests
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from sqlmodel import Session, select, desc
import logging

from app.core.config import settings
from app.models.otp import OTP

logger = logging.getLogger(__name__)

class OTPService:
    def __init__(self, db: Session):
        self.db = db
        self.expiry_minutes = settings.OTP_EXPIRY_MINUTES
        self.max_attempts = settings.OTP_MAX_ATTEMPTS
        self.rate_limit_minutes = settings.OTP_RATE_LIMIT_MINUTES

    def generate_otp(self, length: int = 6) -> str:
        """Generate a random OTP code."""
        return ''.join([str(random.randint(0, 9)) for _ in range(length)])

    def hash_otp(self, otp: str, phone_number: str) -> str:
        """Hash OTP with phone number as salt for security."""
        salt = f"{phone_number}{settings.SECRET_KEY}"
        return hmac.new(
            salt.encode(), 
            otp.encode(), 
            hashlib.sha256
        ).hexdigest()

    def verify_otp_hash(self, otp: str, phone_number: str, stored_hash: str) -> bool:
        """Verify OTP against stored hash."""
        computed_hash = self.hash_otp(otp, phone_number)
        return hmac.compare_digest(computed_hash, stored_hash)

    async def send_otp_sms(self, phone_number: str, otp: str) -> Optional[str]:
        """Send OTP via SMS using the configured SMS service."""
        try:
            # Remove '+' from phone number for SMS service
            clean_phone = phone_number.replace('+', '')
            sms_text = settings.OTP_SMS_TEXT.format(otp=otp)
            
            # Ozonetel API expects form data, not JSON
            payload = {
                "userName": settings.OTP_USER_NAME,
                "entityId": settings.OTP_ENTITY_ID,
                "templateId": settings.OTP_TEMPLATE_ID,
                "destinationNumber": clean_phone,
                "smsText": sms_text,
                "apiKey": settings.OTP_API_KEY,
                "smsType": settings.OTP_SMS_TYPE,
                "senderId": settings.OTP_SENDER_ID
            }
            
            logger.info(f"Sending OTP SMS to {phone_number} via {settings.OTP_SERVICE_URL}")
            
            response = requests.post(
                settings.OTP_SERVICE_URL,
                data=payload,  # Use form data instead of JSON
                timeout=30
            )
            
            if response.status_code == 200:
                # Ozonetel typically returns text response, not JSON
                result_text = response.text.strip()
                logger.info(f"SMS API response: {result_text}")
                
                # Check if response indicates success
                if "success" in result_text.lower() or len(result_text) > 5:  # Assuming successful response has content
                    logger.info(f"SMS sent successfully. Response: {result_text}")
                    return result_text  # Return the response as reference ID
                else:
                    logger.error(f"SMS service error: {result_text}")
                    return None
            else:
                logger.error(f"SMS service HTTP error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error sending SMS: {str(e)}")
            return None

    async def check_rate_limit(self, phone_number: str) -> bool:
        """Check if OTP can be sent (rate limiting)."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=self.rate_limit_minutes)
        
        statement = select(OTP).where(
            OTP.phone_number == phone_number,
            OTP.created_at > cutoff_time
        )
        recent_otp = self.db.exec(statement).first()
        
        return recent_otp is None

    def get_valid_otp(self, phone_number: str) -> Optional[OTP]:
        """Get valid (non-expired, non-verified) OTP for phone number."""
        now = datetime.now(timezone.utc)
        
        statement = select(OTP).where(
            OTP.phone_number == phone_number,
            OTP.expires_at > now,
            OTP.is_verified == False,
            OTP.attempts < self.max_attempts
        ).order_by(desc(OTP.created_at))
        
        return self.db.exec(statement).first()

    async def send_otp(self, phone_number: str) -> Dict[str, Any]:
        """Send OTP to phone number."""
        # Check rate limiting
        if not await self.check_rate_limit(phone_number):
            return {
                "status": "error",
                "message": f"Please wait {self.rate_limit_minutes} minute(s) before requesting another OTP"
            }

        # Generate OTP
        otp_code = self.generate_otp()
        logger.info(f"Generated OTP for {phone_number}: {otp_code}")  # Remove in production
        
        # Send SMS
        reference_id = await self.send_otp_sms(phone_number, otp_code)
        if not reference_id:
            return {
                "status": "error",
                "message": "Failed to send OTP. Please try again later."
            }

        # Store OTP in database
        otp_hash = self.hash_otp(otp_code, phone_number)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.expiry_minutes)
        
        otp_record = OTP(
            phone_number=phone_number,
            otp_hash=otp_hash,
            expires_at=expires_at,
            reference_id=reference_id
        )
        
        self.db.add(otp_record)
        self.db.commit()
        self.db.refresh(otp_record)
        
        return {
            "status": "success",
            "message": "OTP sent successfully",
            "reference_id": reference_id,
            "expires_in_minutes": self.expiry_minutes
        }

    async def verify_otp(self, phone_number: str, otp_code: str) -> bool:
        """Verify OTP code."""
        # Get valid OTP record
        otp_record = self.get_valid_otp(phone_number)
        if not otp_record:
            return False

        # Increment attempts
        otp_record.attempts += 1
        
        # Check if max attempts reached
        if otp_record.attempts > self.max_attempts:
            self.db.commit()
            return False

        # Verify OTP
        if not self.verify_otp_hash(otp_code, phone_number, otp_record.otp_hash):
            self.db.commit()
            return False

        # Mark as verified
        otp_record.is_verified = True
        otp_record.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        
        return True
    
    async def invalidate_otp(self, phone_number: str) -> None:
        """Invalidate any existing OTP for the phone number."""
        statement = select(OTP).where(
            OTP.phone_number == phone_number,
            OTP.is_verified == False
        )
        otp_records = self.db.exec(statement).all()
        
        for otp_record in otp_records:
            otp_record.is_verified = True
            otp_record.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
    
    async def get_otp_status(self, phone_number: str) -> Dict[str, Any]:
        """Get OTP status for a phone number."""
        otp_record = self.get_valid_otp(phone_number)
        
        if not otp_record:
            return {
                "has_pending_otp": False,
                "attempts_remaining": self.max_attempts,
                "expires_at": None,
                "can_resend": await self.check_rate_limit(phone_number)
            }
        
        return {
            "has_pending_otp": True,
            "attempts_remaining": max(0, self.max_attempts - otp_record.attempts),
            "expires_at": otp_record.expires_at.isoformat(),
            "can_resend": await self.check_rate_limit(phone_number)
        }
