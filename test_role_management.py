#!/usr/bin/env python3
"""
Quick test of user role management functionality
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import Session, select
from app.db.session import engine
from app.models.user import User
from app.models.role import Role, RoleEnum
from app.models.associations import UserRoleLink

def test_role_management():
    """Test basic role management functionality."""
    print("🧪 Testing User Role Management")
    print("=" * 50)
    
    with Session(engine) as session:
        # List roles
        print("\n🔑 Available Roles:")
        roles = session.exec(select(Role)).all()
        for role in roles:
            print(f"  - {role.name.value}: {role.description}")
        
        # List users
        print("\n👥 All Users:")
        users = session.exec(select(User)).all()
        for user in users:
            print(f"  - {user.name} ({user.email or user.phone})")
            
            # Get user roles
            role_links = session.exec(
                select(UserRoleLink).where(UserRoleLink.user_id == user.id)
            ).all()
            
            user_roles = []
            for link in role_links:
                role = session.exec(select(Role).where(Role.id == link.role_id)).first()
                if role:
                    user_roles.append(role.name.value)
            
            print(f"    Roles: {', '.join(user_roles) if user_roles else 'None'}")
        
        print(f"\n📊 Summary:")
        print(f"  - Total roles: {len(roles)}")
        print(f"  - Total users: {len(users)}")
        print(f"  - Total role assignments: {len(session.exec(select(UserRoleLink)).all())}")

if __name__ == "__main__":
    test_role_management()
