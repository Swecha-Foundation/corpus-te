#!/usr/bin/env python3
"""
Verification script to check test data creation
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.models import User, Role, Category, Record, UserRoleLink

def verify_test_data():
    """Verify that all test data was created successfully"""
    
    # Create database engine and session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    print("🔍 Verifying Test Data")
    print("=" * 50)
    
    with SessionLocal() as session:
        # Check roles
        roles = session.query(Role).all()
        print(f"🔑 Roles: {len(roles)}")
        for role in roles:
            print(f"   - {role.name}")
        
        # Check users
        users = session.query(User).all()
        print(f"\n👥 Users: {len(users)}")
        for user in users:
            print(f"   - {user.name} ({user.phone})")
        
        # Check user-role assignments
        user_roles = session.query(UserRoleLink).all()
        print(f"\n🔗 User-Role Assignments: {len(user_roles)}")
        for ur in user_roles:
            user = session.query(User).filter(User.id == ur.user_id).first()
            role = session.query(Role).filter(Role.id == ur.role_id).first()
            print(f"   - {user.name} → {role.name}")
        
        # Check categories
        categories = session.query(Category).all()
        print(f"\n📂 Categories: {len(categories)}")
        for category in categories:
            print(f"   - {category.name}")
        
        # Check records
        records = session.query(Record).all()
        print(f"\n📝 Records: {len(records)}")
        for record in records:
            category = session.query(Category).filter(Category.id == record.category_id).first()
            user = session.query(User).filter(User.id == record.user_id).first()
            print(f"   - {record.title} ({record.media_type}) | Category: {category.name} | Created by: {user.name}")
    
    print("\n✅ Verification completed successfully!")

if __name__ == "__main__":
    verify_test_data()
