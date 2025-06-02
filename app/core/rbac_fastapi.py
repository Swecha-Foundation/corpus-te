# app/core/rbac_fastapi.py
"""
FastAPI-compatible Role-Based Access Control (RBAC) System

Uses dependency injection instead of decorators for proper FastAPI integration
"""

from typing import List, Union
from fastapi import HTTPException, status, Depends
from sqlmodel import Session, select

from app.models.user import User
from app.models.role import Role
from app.models.associations import UserRoleLink
from app.db.session import engine
from app.core.auth import get_current_active_user


def get_user_roles(user_id) -> List[str]:
    """
    Get role names for a user by querying the association table.
    """
    with Session(engine) as session:
        # Query roles through the association table
        roles = session.exec(
            select(Role)
            .join(UserRoleLink)
            .where(UserRoleLink.user_id == user_id)
        ).all()
        
        # Extract role names (handle enum values)
        role_names = []
        for role in roles:
            if hasattr(role.name, 'value'):
                role_names.append(role.name.value)
            else:
                role_names.append(str(role.name))
        
        return role_names


def require_roles(allowed_roles: Union[str, List[str]]):
    """
    Create a dependency that requires specific roles.
    
    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(
            current_user: User = Depends(require_roles("admin"))
        ):
            return {"message": "Admin access granted"}
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]
    
    def check_roles(current_user: User = Depends(get_current_active_user)) -> User:
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive"
            )
        
        # Get user's role names
        user_role_names = get_user_roles(current_user.id)
        
        # Admin has access to everything
        if "admin" in user_role_names:
            return current_user
        
        # Check if user has any of the required roles
        if not any(role in user_role_names for role in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {allowed_roles}. Your roles: {user_role_names}"
            )
        
        return current_user
    
    return check_roles


def require_permission(resource: str, method: str):
    """
    Create a dependency that requires specific permissions.
    
    Usage:
        @router.get("/records")
        async def get_records(
            current_user: User = Depends(require_permission("records", "GET"))
        ):
            return records
    """
    def check_permission(current_user: User = Depends(get_current_active_user)) -> User:
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive"
            )
        
        user_role_names = get_user_roles(current_user.id)
        
        # Admin has access to everything
        if "admin" in user_role_names:
            return current_user
        
        # Define permissions for reviewer
        reviewer_permissions = {
            "records": ["GET", "PUT"],
            "categories": ["GET"],
            "users": ["GET"]
        }
        
        # Define permissions for regular user
        user_permissions = {
            "records": ["GET"],
            "categories": ["GET"]
        }
        
        # Check reviewer permissions
        if "reviewer" in user_role_names:
            if resource.lower() in reviewer_permissions:
                if method.upper() in reviewer_permissions[resource.lower()]:
                    return current_user
        
        # Check regular user permissions
        if "user" in user_role_names:
            if resource.lower() in user_permissions:
                if method.upper() in user_permissions[resource.lower()]:
                    return current_user
        
        # If no permissions match, deny access
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Insufficient permissions for {resource}:{method}. Your roles: {user_role_names}"
        )
    
    return check_permission


# Convenience dependency functions
def require_admin():
    """Dependency to require admin role."""
    return require_roles("admin")


def require_reviewer():
    """Dependency to require reviewer role (or admin)."""
    return require_roles(["admin", "reviewer"])


def require_user():
    """Dependency to require any authenticated user role."""
    return require_roles(["admin", "reviewer", "user"])


# Permission-specific dependency functions
def require_users_read():
    """Dependency for users GET operations."""
    return require_permission("users", "GET")


def require_users_write():
    """Dependency for users POST operations."""
    return require_permission("users", "POST")


def require_users_update():
    """Dependency for users PUT operations."""
    return require_permission("users", "PUT")


def require_users_delete():
    """Dependency for users DELETE operations."""
    return require_permission("users", "DELETE")
