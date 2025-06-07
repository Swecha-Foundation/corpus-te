# app/api/v1/endpoints/auth.py
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlmodel import select

from app.core.auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_password_hash,
    verify_password,
)
from app.core.config import settings
from app.db.session import SessionDep
from app.models.user import User
from app.schemas import (
    Token,
    LoginRequest,
    UserRead,
    PasswordChangeRequest,
    PasswordResetRequest,
    MessageResponse,
)
from app.schemas.otp import OTPSendRequest, OTPVerifyRequest, OTPResponse, TokenResponse
from app.services.otp_service import OTPService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()


@router.post("/login", response_model=Token)
async def login_for_access_token(
    login_data: LoginRequest,
    session: SessionDep
):
    """Authenticate user and return access token."""
    user = authenticate_user(session, login_data.phone, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect phone number or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login time
    from datetime import datetime
    user.last_login_at = datetime.utcnow()
    session.add(user)
    session.commit()
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserRead)
async def read_users_me(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information."""
    return current_user


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    password_data: PasswordChangeRequest,
    session: SessionDep,
    current_user: User = Depends(get_current_active_user)
):
    """Change current user's password."""
    if not current_user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have a password set"
        )
    
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    session.add(current_user)
    session.commit()
    
    return MessageResponse(message="Password changed successfully")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    reset_data: PasswordResetRequest,
    session: SessionDep,
    current_user: User = Depends(get_current_active_user)
):
    """Reset user password (admin functionality - should be protected in production)."""
    statement = select(User).where(User.phone == reset_data.phone)
    user = session.exec(statement).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    user.hashed_password = get_password_hash(reset_data.new_password)
    session.add(user)
    session.commit()
    
    return MessageResponse(message="Password reset successfully")


@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_active_user)
):
    """Refresh access token."""
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(current_user.id), expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/send-otp", response_model=OTPResponse)
async def send_otp(
    request: OTPSendRequest,
    session: SessionDep
):
    """Send OTP to phone number via SMS"""
    try:
        otp_service = OTPService(session)
        
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
    session: SessionDep
):
    """Verify OTP and generate JWT token"""
    try:
        otp_service = OTPService(session)
        
        # Verify OTP
        is_valid = await otp_service.verify_otp(request.phone_number, request.otp_code)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP"
            )
        
        # Check if user exists, create if not
        statement = select(User).where(User.phone == request.phone_number)
        user = session.exec(statement).first()
        
        if not user:
            # Create new user with phone number
            user = User(
                phone=request.phone_number,
                name="",  # Will be updated later
                is_active=True
            )
            session.add(user)
            session.commit()
            session.refresh(user)
        
        # Update last login time
        from datetime import datetime
        user.last_login_at = datetime.utcnow()
        session.add(user)
        session.commit()
        
        # Generate JWT token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=str(user.id), expires_delta=access_token_expires
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=str(user.id),
            phone_number=user.phone
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
    session: SessionDep
):
    """Resend OTP to phone number"""
    try:
        otp_service = OTPService(session)
        
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
