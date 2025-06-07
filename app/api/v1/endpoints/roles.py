# app/api/v1/endpoints/roles.py
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import select

from app.db.session import SessionDep
from app.models.role import Role
from app.models.user import User
from app.schemas import RoleRead, RoleCreate, MessageResponse
from app.core.exceptions import DuplicateEntry
from app.core.rbac_fastapi import require_admin
router = APIRouter()

@router.get("/", response_model=List[RoleRead])
async def get_roles(
    session: SessionDep,
    current_user: User = Depends(require_admin())
):
    """Get all roles."""
    statement = select(Role)
    roles = session.exec(statement).all()
    return roles

@router.get("/{role_id}", response_model=RoleRead)
async def get_role(
    role_id: int, 
    session: SessionDep, 
    current_user: User = Depends(require_admin())
):
    """Get a specific role by ID."""
    role = session.get(Role, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with id {role_id} not found"
        )
    return role

@router.post("/", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate, 
    session: SessionDep, 
    current_user: User = Depends(require_admin())
    ):
    """Create a new role."""
    # Check if role with same name already exists
    statement = select(Role).where(Role.name == role_data.name)
    existing_role = session.exec(statement).first()
    
    if existing_role:
        raise DuplicateEntry("Role", role_data.name.value)
    
    # Create new role
    role = Role.model_validate(role_data)
    session.add(role)
    session.commit()
    session.refresh(role)
    return role

@router.delete("/{role_id}", response_model=MessageResponse)
async def delete_role(
    role_id: int, 
    session: SessionDep, 
    current_user: User = Depends(require_admin())
    ):
    """Delete a role."""
    role = session.get(Role, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with id {role_id} not found"
        )
    
    session.delete(role)
    session.commit()
    return MessageResponse(message=f"Role {role.name.value} deleted successfully")
