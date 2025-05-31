# app/core/auth.py
from datetime import datetime, timedelta
from typing import Any, List, Optional, Union
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import select
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.db.session import SessionDep
from app.models.user import User
from app.models.role import RoleEnum

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token authentication scheme
security = HTTPBearer()


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def decode_token(token: str) -> Optional[str]:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except JWTError:
        return None


async def get_current_user(
    session: SessionDep,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Get current authenticated user."""
    token = credentials.credentials
    user_id = decode_token(token)
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = session.get(User, user_uuid)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    return current_user


def require_roles(allowed_roles: List[RoleEnum]):
    """Dependency to require specific roles."""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        user_role_names = [role.name for role in current_user.roles]
        
        if not any(role in user_role_names for role in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[role.value for role in allowed_roles]}"
            )
        return current_user
    
    return role_checker


# Role-specific dependencies
require_admin = require_roles([RoleEnum.admin])
require_admin_or_reviewer = require_roles([RoleEnum.admin, RoleEnum.reviewer])
require_any_role = require_roles([RoleEnum.admin, RoleEnum.user, RoleEnum.reviewer])


def authenticate_user(session: SessionDep, phone: str, password: str) -> Optional[User]:
    """Authenticate user by phone and password."""
    statement = select(User).where(User.phone == phone)
    user = session.exec(statement).first()
    
    if not user:
        return None
    
    if not user.hashed_password:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user
