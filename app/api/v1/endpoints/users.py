# app/api/v1/endpoints/users.py
from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Query, Depends
from sqlmodel import select

from app.db.session import SessionDep
from app.models.user import User
from app.models.role import Role
from app.models.associations import UserRoleLink
from app.schemas import UserRead, UserCreate, UserUpdate, MessageResponse, RoleRead, UserWithRoles
from app.core.exceptions import DuplicateEntry, UserNotFound
from app.core.auth import get_password_hash
from app.core.rbac_fastapi import require_admin, require_users_read, require_users_write, require_users_update, require_users_delete

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
    return users

@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: UUID, 
    session: SessionDep,
    current_user: User = Depends(require_users_read())
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
