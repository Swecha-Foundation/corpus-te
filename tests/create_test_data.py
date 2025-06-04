#!/usr/bin/env python3
"""
Create test data: 3 users (admin, reviewer, user roles), 2 categories, and 4 records
"""

import sys
import os
from datetime import datetime, date, timezone
from uuid import UUID

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import Session, select
from app.db.session import engine
from app.models.user import User
from app.models.role import Role, RoleEnum
from app.models.category import Category
from app.models.record import Record, MediaType
from app.models.associations import UserRoleLink
from app.core.auth import get_password_hash


def create_test_data():
    """Create comprehensive test data for the application"""
    
    print("🚀 Creating Test Data")
    print("=" * 50)
    
    with Session(engine) as session:
        
        # 1. Ensure roles exist (should already exist from migration)
        print("\n1. 🔑 Checking/Creating Roles...")
        
        roles_data = [
            {"name": RoleEnum.admin, "description": "Administrator with full access"},
            {"name": RoleEnum.reviewer, "description": "Reviewer with moderate access"},
            {"name": RoleEnum.user, "description": "Regular user with limited access"}
        ]
        
        role_objects = {}
        for role_data in roles_data:
            existing_role = session.exec(
                select(Role).where(Role.name == role_data["name"])
            ).first()
            
            if not existing_role:
                role = Role(**role_data)
                session.add(role)
                session.flush()
                role_objects[role_data["name"]] = role
                print(f"   ✅ Created role: {role_data['name']}")
            else:
                role_objects[role_data["name"]] = existing_role
                print(f"   ℹ️ Role already exists: {role_data['name']}")
        
        session.commit()
        
        # 2. Create 3 test users
        print("\n2. 👥 Creating Test Users...")
        
        users_data = [
            {
                "phone": "1111111111",
                "name": "Admin User",
                "email": "admin@example.com",
                "gender": "other",
                "date_of_birth": date(1990, 1, 15),
                "place": "Hyderabad, Telangana",
                "password": "admin123",
                "role": RoleEnum.admin
            },
            {
                "phone": "2222222222", 
                "name": "Reviewer User",
                "email": "reviewer@example.com",
                "gender": "female",
                "date_of_birth": date(1985, 6, 20),
                "place": "Bangalore, Karnataka",
                "password": "reviewer123",
                "role": RoleEnum.reviewer
            },
            {
                "phone": "3333333333",
                "name": "Regular User",
                "email": "user@example.com", 
                "gender": "male",
                "date_of_birth": date(1995, 12, 10),
                "place": "Chennai, Tamil Nadu",
                "password": "user123",
                "role": RoleEnum.user
            }
        ]
        
        created_users = []
        for user_data in users_data:
            # Check if user already exists
            existing_user = session.exec(
                select(User).where(User.phone == user_data["phone"])
            ).first()
            
            if existing_user:
                print(f"   ℹ️ User already exists: {user_data['name']} ({user_data['phone']})")
                created_users.append(existing_user)
                continue
            
            # Create new user
            user_role = user_data.pop("role")
            password = user_data.pop("password")
            
            user = User(
                **user_data,
                hashed_password=get_password_hash(password),
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            session.add(user)
            session.flush()  # Get the user ID
            
            # Assign role to user
            role_obj = role_objects[user_role]
            user_role_link = UserRoleLink(user_id=user.id, role_id=role_obj.id)
            session.add(user_role_link)
            
            created_users.append(user)
            print(f"   ✅ Created user: {user.name} ({user.phone}) with role: {user_role}")
        
        session.commit()
        
        # 3. Create 2 categories
        print("\n3. 📂 Creating Test Categories...")
        
        categories_data = [
            {
                "name": "stories",
                "title": "Folk Stories",
                "description": "Traditional stories and folklore from Telugu culture",
                "published": True,
                "rank": 1
            },
            {
                "name": "songs",
                "title": "Traditional Songs", 
                "description": "Folk songs, lullabies, and traditional music",
                "published": True,
                "rank": 2
            }
        ]
        
        created_categories = []
        for category_data in categories_data:
            # Check if category already exists
            existing_category = session.exec(
                select(Category).where(Category.name == category_data["name"])
            ).first()
            
            if existing_category:
                print(f"   ℹ️ Category already exists: {category_data['title']}")
                created_categories.append(existing_category)
                continue
            
            category = Category(
                **category_data,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            session.add(category)
            session.flush()
            created_categories.append(category)
            print(f"   ✅ Created category: {category.title} ({category.name})")
        
        session.commit()
        
        # 4. Create 4 records
        print("\n4. 📝 Creating Test Records...")
        
        if len(created_users) >= 2 and len(created_categories) >= 2:
            records_data = [
                {
                    "title": "The Wise Farmer's Tale",
                    "description": "A traditional Telugu story about a farmer who outwits a cunning merchant",
                    "media_type": MediaType.text,
                    "file_url": "/files/stories/wise_farmer.txt",
                    "file_name": "wise_farmer.txt",
                    "file_size": 2048,
                    "status": "uploaded",
                    "user_id": created_users[0].id,  # Admin user
                    "category_id": created_categories[0].id,  # Stories category
                    "reviewed": True
                },
                {
                    "title": "Lullaby for the Moon",
                    "description": "A gentle Telugu lullaby sung to children under the moonlight",
                    "media_type": MediaType.audio,
                    "file_url": "/files/songs/moon_lullaby.mp3",
                    "file_name": "moon_lullaby.mp3", 
                    "file_size": 5242880,  # 5MB
                    "status": "uploaded",
                    "geo_lat": 17.3850,  # Hyderabad coordinates
                    "geo_lng": 78.4867,
                    "user_id": created_users[1].id,  # Reviewer user
                    "category_id": created_categories[1].id,  # Songs category
                    "reviewed": True
                },
                {
                    "title": "Village Festival Dance",
                    "description": "Video recording of traditional dance performed during village festivals",
                    "media_type": MediaType.video,
                    "file_url": "/files/videos/festival_dance.mp4",
                    "file_name": "festival_dance.mp4",
                    "file_size": 52428800,  # 50MB
                    "status": "uploaded",
                    "geo_lat": 13.0827,  # Chennai coordinates
                    "geo_lng": 80.2707,
                    "user_id": created_users[2].id,  # Regular user
                    "category_id": created_categories[1].id,  # Songs category (dance goes with music)
                    "reviewed": False
                },
                {
                    "title": "The Legend of Banjara Hills",
                    "description": "An ancient story about the formation of the famous Banjara Hills",
                    "media_type": MediaType.text,
                    "file_url": "/files/stories/banjara_legend.txt",
                    "file_name": "banjara_legend.txt",
                    "file_size": 3584,
                    "status": "pending",
                    "user_id": created_users[1].id,  # Reviewer user
                    "category_id": created_categories[0].id,  # Stories category
                    "reviewed": False
                }
            ]
            
            created_records = []
            for record_data in records_data:
                # Check if record with same title already exists
                existing_record = session.exec(
                    select(Record).where(Record.title == record_data["title"])
                ).first()
                
                if existing_record:
                    print(f"   ℹ️ Record already exists: {record_data['title']}")
                    continue
                
                record = Record(
                    **record_data,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                
                session.add(record)
                created_records.append(record)
                print(f"   ✅ Created record: {record.title} ({record.media_type})")
            
            session.commit()
            
        else:
            print("   ❌ Cannot create records: insufficient users or categories")
        
        # 5. Summary
        print("\n" + "=" * 50)
        print("📊 Test Data Creation Summary")
        print("=" * 50)
        
        # Count existing data
        total_users = len(session.exec(select(User)).all())
        total_roles = len(session.exec(select(Role)).all())
        total_categories = len(session.exec(select(Category)).all())
        total_records = len(session.exec(select(Record)).all())
        total_role_assignments = len(session.exec(select(UserRoleLink)).all())
        
        print(f"👥 Total Users: {total_users}")
        print(f"🔑 Total Roles: {total_roles}")
        print(f"📂 Total Categories: {total_categories}")
        print(f"📝 Total Records: {total_records}")
        print(f"🔗 Total Role Assignments: {total_role_assignments}")
        
        print("\n🔐 Test Login Credentials:")
        print("   Admin:    phone=1111111111, password=admin123")
        print("   Reviewer: phone=2222222222, password=reviewer123")
        print("   User:     phone=3333333333, password=user123")
        
        print("\n✅ Test data creation completed successfully!")


def cleanup_test_data():
    """Clean up test data (optional function)"""
    print("🧹 Cleaning up test data...")
    
    with Session(engine) as session:
        # Delete test records
        test_titles = [
            "The Wise Farmer's Tale",
            "Lullaby for the Moon", 
            "Village Festival Dance",
            "The Legend of Banjara Hills"
        ]
        
        for title in test_titles:
            record = session.exec(select(Record).where(Record.title == title)).first()
            if record:
                session.delete(record)
                print(f"   🗑️ Deleted record: {title}")
        
        # Delete test categories
        test_category_names = ["stories", "songs"]
        for name in test_category_names:
            category = session.exec(select(Category).where(Category.name == name)).first()
            if category:
                session.delete(category)
                print(f"   🗑️ Deleted category: {name}")
        
        # Delete test users and their role assignments
        test_phones = ["1111111111", "2222222222", "3333333333"]
        for phone in test_phones:
            user = session.exec(select(User).where(User.phone == phone)).first()
            if user:
                # Delete role assignments first
                role_links = session.exec(
                    select(UserRoleLink).where(UserRoleLink.user_id == user.id)
                ).all()
                for link in role_links:
                    session.delete(link)
                
                session.delete(user)
                print(f"   🗑️ Deleted user: {phone}")
        
        session.commit()
        print("✅ Cleanup completed!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage test data for the application")
    parser.add_argument(
        "action", 
        choices=["create", "cleanup"], 
        help="Action to perform: create or cleanup test data"
    )
    
    args = parser.parse_args()
    
    if args.action == "create":
        create_test_data()
    elif args.action == "cleanup":
        cleanup_test_data()
