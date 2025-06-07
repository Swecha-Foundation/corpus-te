"""
OTP Authentication API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.otp import OTPSendRequest, OTPVerifyRequest, OTPResponse, TokenResponse
from app.services.otp_service import OTPService
from app.core.security import create_access_token
from app.models.user import User
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/send-otp", response_model=OTPResponse)
async def send_otp(
    request: OTPSendRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Send OTP to phone number via SMS
    """
    try:
        otp_service = OTPService(db)
        
        # Check rate limiting
        if not await otp_service.check_rate_limit(request.phone_number):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Send OTP
        result = await otp_service.send_otp(request.phone_number)
        
        if result["status"] == "success":
            return OTPResponse(
                status="success",
                message="OTP sent successfully",
                reference_id=result.get("reference_id")
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send OTP: {result.get('message', 'Unknown error')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending OTP: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(
    request: OTPVerifyRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Verify OTP and generate JWT token
    """
    try:
        otp_service = OTPService(db)
        
        # Verify OTP
        is_valid = await otp_service.verify_otp(request.phone_number, request.otp_code)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP"
            )
        
        # Check if user exists, create if not
        user = db.query(User).filter(User.phone_number == request.phone_number).first()
        if not user:
            # Create new user with phone number
            user = User(
                phone_number=request.phone_number,
                is_active=True,
                is_verified=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update verification status
            user.is_verified = True
            db.commit()
        
        # Generate JWT token
        access_token = create_access_token(
            data={"sub": str(user.id), "phone": user.phone_number}
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=str(user.id),
            phone_number=user.phone_number
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying OTP: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/resend-otp", response_model=OTPResponse)
async def resend_otp(
    request: OTPSendRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Resend OTP to phone number
    """
    try:
        otp_service = OTPService(db)
        
        # Check rate limiting for resend
        if not await otp_service.check_rate_limit(request.phone_number):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Invalidate existing OTP
        await otp_service.invalidate_otp(request.phone_number)
        
        # Send new OTP
        result = await otp_service.send_otp(request.phone_number)
        
        if result["status"] == "success":
            return OTPResponse(
                status="success",
                message="OTP resent successfully",
                reference_id=result.get("reference_id")
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to resend OTP: {result.get('message', 'Unknown error')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resending OTP: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/otp-status/{phone_number}")
async def get_otp_status(
    phone_number: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get OTP status for a phone number (for debugging/admin purposes)
    """
    try:
        otp_service = OTPService(db)
        status_info = await otp_service.get_otp_status(phone_number)
        
        return {
            "phone_number": phone_number,
            "has_pending_otp": status_info["has_pending_otp"],
            "attempts_remaining": status_info["attempts_remaining"],
            "expires_at": status_info["expires_at"],
            "can_resend": status_info["can_resend"]
        }
        
    except Exception as e:
        logger.error(f"Error getting OTP status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
