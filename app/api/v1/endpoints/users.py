# app/api/v1/endpoints/users.py
from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Query, Depends
from sqlmodel import select

from app.db.session import SessionDep
from app.models.user import User
from app.models.role import Role
from app.models.record import Record, MediaType

from app.models.associations import UserRoleLink
from app.schemas import UserRead, UserCreate, UserUpdate, MessageResponse, RoleRead, UserWithRoles, ContributionResponse, ContirbutionMediaCountResponse, ContributionRead, ContributionFilterRead
from app.core.exceptions import DuplicateEntry, UserNotFound
from app.core.auth import get_password_hash
from app.core.rbac_fastapi import create_rbac_dependency, require_admin, require_users_read, require_users_write, require_users_update, require_users_delete, get_current_active_user

router = APIRouter()

@router.get("/", response_model=List[UserRead])
async def get_users(
    session: SessionDep,
    current_user: User = Depends(require_admin()),
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of users to return")
):
    """Get all users with pagination."""
    statement = select(User).offset(skip).limit(limit)
    users = session.exec(statement).all()
    
    # Handle users with empty or None names by setting a default value
    processed_users = []
    for user in users:
        # Create a copy of user data
        user_dict = user.model_dump()
        
        # Fix empty or None names
        if not user_dict.get('name') or user_dict['name'].strip() == '':
            user_dict['name'] = f"User {user_dict['phone'][-4:]}"  # Use last 4 digits of phone
        
        # Convert back to UserRead object for proper validation
        processed_users.append(UserRead.model_validate(user_dict))
    
    return processed_users

@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: UUID, 
    session: SessionDep,
    current_user: User = Depends(create_rbac_dependency(roles=["admin", "reviewer"]))
):
    """Get a specific user by ID."""
    user = session.get(User, user_id)
    if not user:
        raise UserNotFound(str(user_id))
    return user

@router.get("/{user_id}/with-roles", response_model=UserWithRoles)
async def get_user_with_roles(
    user_id: UUID, 
    session: SessionDep,
    current_user: User = Depends(require_users_read())
):
    """Get a specific user by ID with their roles populated."""
    user = session.get(User, user_id)
    if not user:
        raise UserNotFound(str(user_id))
    
    # Get user's roles through association table
    statement = select(Role).join(UserRoleLink).where(UserRoleLink.user_id == user_id)
    roles = session.exec(statement).all()
    
    # Create response with roles
    user_dict = user.model_dump()
    user_dict['roles'] = roles
    return UserWithRoles.model_validate(user_dict)

@router.get("/phone/{phone}", response_model=UserRead)
async def get_user_by_phone(
    phone: str, 
    session: SessionDep,
    current_user: User = Depends(require_users_read())
):
    """Get a user by phone number."""
    statement = select(User).where(User.phone == phone)
    user = session.exec(statement).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with phone {phone} not found"
        )
    return user

@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate, 
    session: SessionDep,
    # Note: Create user endpoint allows registration without authentication
    # current_user: User = Depends(require_users_write())
):
    """Create a new user."""
    # Validate consent requirement
    if not user_data.has_given_consent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User consent is required to create an account"
        )
    
    # Check if roles exist
    for role_id in user_data.role_ids:
        role = session.get(Role, role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role with id {role_id} not found"
            )
    
    # Check if user with same phone already exists
    statement = select(User).where(User.phone == user_data.phone)
    existing_user = session.exec(statement).first()
    
    if existing_user:
        raise DuplicateEntry("Phone", user_data.phone)
    
    # Check if email is provided and already exists
    if user_data.email:
        statement = select(User).where(User.email == user_data.email)
        existing_email = session.exec(statement).first()
        
        if existing_email:
            raise DuplicateEntry("Email", user_data.email)
    
    # Create new user
    user_dict = user_data.model_dump(exclude={'role_ids', 'password'})
    user = User.model_validate(user_dict)
    
    # Hash the password
    user.hashed_password = get_password_hash(user_data.password)
    
    # Set consent timestamp if consent is given
    if user_data.has_given_consent:
        from datetime import datetime
        user.consent_given_at = datetime.utcnow()
    
    session.add(user)
    session.flush()  # Get the user ID before committing
    
    # Assign roles to user using the association table
    from app.models.associations import UserRoleLink
    for role_id in user_data.role_ids:
        role = session.get(Role, role_id)
        if role:
            # Create association record
            user_role_link = UserRoleLink(user_id=user.id, role_id=role_id)
            session.add(user_role_link)
    
    session.commit()
    session.refresh(user)
    return user

@router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: UUID, 
    user_update: UserUpdate, 
    session: SessionDep,
    current_user: User = Depends(require_users_update())
):
    """Update a user."""
    user = session.get(User, user_id)
    if not user:
        raise UserNotFound(str(user_id))
    
    # Check email uniqueness if being updated
    if user_update.email and user_update.email != user.email:
        statement = select(User).where(User.email == user_update.email)
        existing_email = session.exec(statement).first()
        
        if existing_email:
            raise DuplicateEntry("Email", user_update.email)
    
    # Update user fields
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: UUID, 
    session: SessionDep,
    current_user: User = Depends(require_users_delete())
):
    """Delete a user."""
    user = session.get(User, user_id)
    if not user:
        raise UserNotFound(str(user_id))
    
    session.delete(user)
    session.commit()
    return MessageResponse(message=f"User {user.name} deleted successfully")

# Role management endpoints
@router.get("/{user_id}/roles", response_model=List[RoleRead])
async def get_user_roles(
    user_id: UUID, 
    session: SessionDep,
    current_user: User = Depends(require_users_read())
):
    """Get all roles assigned to a user."""
    user = session.get(User, user_id)
    if not user:
        raise UserNotFound(str(user_id))
    
    # Get roles through association table
    statement = select(Role).join(UserRoleLink).where(UserRoleLink.user_id == user_id)
    roles = session.exec(statement).all()
    return roles

@router.post("/{user_id}/roles", response_model=List[RoleRead])
async def assign_roles_to_user(
    user_id: UUID, 
    role_ids: List[int], 
    session: SessionDep,
    current_user: User = Depends(require_users_write())
):
    """Assign roles to a user."""
    user = session.get(User, user_id)
    if not user:
        raise UserNotFound(str(user_id))
    
    # Verify all roles exist
    for role_id in role_ids:
        role = session.get(Role, role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role with id {role_id} not found"
            )
    
    # Clear existing roles for this user
    delete_statement = select(UserRoleLink).where(UserRoleLink.user_id == user_id)
    existing_links = session.exec(delete_statement).all()
    for link in existing_links:
        session.delete(link)
    
    # Add new role assignments
    for role_id in role_ids:
        user_role_link = UserRoleLink(user_id=user_id, role_id=role_id)
        session.add(user_role_link)
    
    session.commit()
    
    # Return the assigned roles
    statement = select(Role).join(UserRoleLink).where(UserRoleLink.user_id == user_id)
    roles = session.exec(statement).all()
    return roles

@router.put("/{user_id}/roles/add", response_model=List[RoleRead])
async def add_role_to_user(
    user_id: UUID, 
    role_id: int, 
    session: SessionDep,
    current_user: User = Depends(require_users_update())
):
    """Add a single role to a user (keeping existing roles)."""
    user = session.get(User, user_id)
    if not user:
        raise UserNotFound(str(user_id))
    
    role = session.get(Role, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role with id {role_id} not found"
        )
    
    # Check if user already has this role
    existing_link_statement = select(UserRoleLink).where(
        UserRoleLink.user_id == user_id,
        UserRoleLink.role_id == role_id
    )
    existing_link = session.exec(existing_link_statement).first()
    
    if not existing_link:
        # Add the role assignment
        user_role_link = UserRoleLink(user_id=user_id, role_id=role_id)
        session.add(user_role_link)
        session.commit()
    
    # Return all roles for this user
    statement = select(Role).join(UserRoleLink).where(UserRoleLink.user_id == user_id)
    roles = session.exec(statement).all()
    return roles

@router.delete("/{user_id}/roles/{role_id}", response_model=List[RoleRead])
async def remove_role_from_user(
    user_id: UUID, 
    role_id: int, 
    session: SessionDep,
    current_user: User = Depends(require_users_delete())
):
    """Remove a role from a user."""
    user = session.get(User, user_id)
    if not user:
        raise UserNotFound(str(user_id))
    
    role = session.get(Role, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role with id {role_id} not found"
        )
    
    # Find and remove the role assignment
    delete_statement = select(UserRoleLink).where(
        UserRoleLink.user_id == user_id,
        UserRoleLink.role_id == role_id
    )
    existing_link = session.exec(delete_statement).first()
    
    if existing_link:
        session.delete(existing_link)
        session.commit()
    
    # Return remaining roles for this user
    statement = select(Role).join(UserRoleLink).where(UserRoleLink.user_id == user_id)
    roles = session.exec(statement).all()
    return roles

# Contributions endpoints
@router.get("/{user_id}/contributions", response_model=ContributionRead)
async def get_user_contributions(
    user_id: UUID, 
    session: SessionDep,
    current_user: User = Depends(get_current_active_user), 
):
    """Get all records submitted by a user. Allow self-access or users with permission."""
    user = session.get(User, user_id)
    if not user:
        raise UserNotFound(str(user_id))
    # Get roles through association table
    # Allow if current_user is the user, or if they have permission
    if current_user.id != user_id:
        # Only allow if user has permission to read users
        require_users_read_dep = require_users_read()
        await require_users_read_dep(current_user)  # raises if not allowed

    statement = select(Record).where(Record.user_id == user_id)
    records = session.scalars(statement).all()
    total_count = len(records)
    # Group counts by media_type
    counts_by_media = {
        "text": 0,
        "audio": 0,
        "image": 0,
        "video": 0,
    }
    audio_contributions = []
    video_contributions = []
    text_contributions = []
    image_contributions = []

    for r in records:
        counts_by_media[r.media_type] += 1
        contribution = ContributionResponse(
            id=r.uid,
            size=r.file_size or 0,
            category_id=r.category_id,
            reviewed=r.reviewed,
            title=r.title,
        )
        if r.media_type == "audio":
            audio_contributions.append(contribution)
        elif r.media_type == "video":
            video_contributions.append(contribution)
        elif r.media_type == "text":
            text_contributions.append(contribution)
        elif r.media_type == "image":
            image_contributions.append(contribution)

    counts_obj = ContirbutionMediaCountResponse(**counts_by_media)

    return ContributionRead(
        user_id=user_id,
        total_contributions=total_count,
        contributions_by_media_type=counts_obj,
        audio_contributions=audio_contributions or None,
        video_contributions=video_contributions or None,
        text_contributions=text_contributions or None,
        image_contributions=image_contributions or None,
    )

@router.get("/{user_id}/contributions/{media_type}", response_model=ContributionFilterRead)
async def get_user_contributions_by_media(
    user_id: UUID, 
    session: SessionDep,
    media_type: MediaType,
    current_user: User = Depends(get_current_active_user),  # Allow any authenticated user
):
    """Get all records submitted by a user for a specific media type. Allow self-access or users with permission."""
    user = session.get(User, user_id)
    if not user:
        raise UserNotFound(str(user_id))

    if current_user.id != user_id:
        require_users_read_dep = require_users_read()
        await require_users_read_dep(current_user)

    statement = select(Record).where(Record.user_id == user_id, Record.media_type == media_type)
    records = session.scalars(statement).all()
    total_count = len(records)

    contributions = []

    for r in records:
        contribution = ContributionResponse(
            id=r.uid,
            size=r.file_size or 0,
            category_id=r.category_id,
            reviewed=r.reviewed,
            title=r.title,
        )
        contributions.append(contribution)
        
    return ContributionFilterRead(
        user_id=user_id,
        total_contributions=total_count,
        contributions=contributions or None,
    )