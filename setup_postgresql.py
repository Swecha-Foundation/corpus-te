#!/usr/bin/env python3
"""
PostgreSQL Database Setup and Connection Test Script

This script helps you:
1. Test the PostgreSQL connection
2. Create the database if it doesn't exist
3. Run migrations
4. Seed initial data

Usage:
    python setup_db.py [--create-db] [--test-connection] [--migrate] [--seed]
"""

import os
import sys
import argparse
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add the app directory to the path
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), ".")))

from app.core.config import settings

def test_postgres_connection():
    """Test if PostgreSQL server is accessible."""
    try:
        # Connect to PostgreSQL server (without specifying a database)
        server_url = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/postgres"
        engine = create_engine(server_url)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ PostgreSQL server connection successful!")
            print(f"   Version: {version}")
            return True
    except Exception as e:
        print(f"❌ PostgreSQL server connection failed: {e}")
        print("   Make sure PostgreSQL is running and credentials are correct.")
        return False

def database_exists():
    """Check if the target database exists."""
    try:
        server_url = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/postgres"
        engine = create_engine(server_url)
        
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname='{settings.DB_NAME}'"))
            exists = result.fetchone() is not None
            return exists
    except Exception as e:
        print(f"❌ Error checking database existence: {e}")
        return False

def create_database():
    """Create the database if it doesn't exist."""
    if database_exists():
        print(f"✅ Database '{settings.DB_NAME}' already exists.")
        return True
    
    try:
        # Connect using psycopg2 for database creation
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        cursor = conn.cursor()
        cursor.execute(f'CREATE DATABASE "{settings.DB_NAME}"')
        cursor.close()
        conn.close()
        
        print(f"✅ Database '{settings.DB_NAME}' created successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        return False

def test_database_connection():
    """Test connection to the target database."""
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT current_database()"))
            db_name = result.fetchone()[0]
            print(f"✅ Database '{db_name}' connection successful!")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def run_migrations():
    """Run Alembic migrations."""
    try:
        import subprocess
        result = subprocess.run(["alembic", "upgrade", "head"], 
                              capture_output=True, text=True, cwd=".")
        if result.returncode == 0:
            print("✅ Database migrations completed successfully!")
            print(result.stdout)
            return True
        else:
            print("❌ Migration failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        return False

def seed_initial_data():
    """Seed initial roles data."""
    try:
        from app.models import Role, RoleEnum
        from app.db.session import SessionLocal
        
        with SessionLocal() as session:
            # Check if roles already exist
            existing_roles = session.query(Role).count()
            if existing_roles > 0:
                print(f"✅ Roles already exist ({existing_roles} roles found).")
                return True
            
            # Create default roles
            roles = [
                Role(name=RoleEnum.admin, description="Administrator role"),
                Role(name=RoleEnum.user, description="Regular user role"),
                Role(name=RoleEnum.reviewer, description="Content reviewer role")
            ]
            
            for role in roles:
                session.add(role)
            
            session.commit()
            print("✅ Initial roles seeded successfully!")
            return True
    except Exception as e:
        print(f"❌ Failed to seed initial data: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="PostgreSQL Database Setup")
    parser.add_argument("--create-db", action="store_true", help="Create database if it doesn't exist")
    parser.add_argument("--test-connection", action="store_true", help="Test database connection")
    parser.add_argument("--migrate", action="store_true", help="Run database migrations")
    parser.add_argument("--seed", action="store_true", help="Seed initial data")
    parser.add_argument("--all", action="store_true", help="Run all setup steps")
    
    args = parser.parse_args()
    
    # If no specific flags, show current configuration
    if not any([args.create_db, args.test_connection, args.migrate, args.seed, args.all]):
        print("🔧 Current PostgreSQL Configuration:")
        print(f"   Host: {settings.DB_HOST}")
        print(f"   Port: {settings.DB_PORT}")
        print(f"   Database: {settings.DB_NAME}")
        print(f"   User: {settings.DB_USER}")
        print(f"   URL: {settings.DATABASE_URL}")
        print("\nUse --help to see available options, or --all to run full setup.")
        return
    
    success = True
    
    if args.all or args.test_connection:
        print("🔍 Testing PostgreSQL server connection...")
        if not test_postgres_connection():
            success = False
            return
    
    if args.all or args.create_db:
        print("🏗️  Creating database...")
        if not create_database():
            success = False
            return
    
    if args.all or args.test_connection:
        print("🔍 Testing database connection...")
        if not test_database_connection():
            success = False
            return
    
    if args.all or args.migrate:
        print("🚀 Running database migrations...")
        if not run_migrations():
            success = False
            return
    
    if args.all or args.seed:
        print("🌱 Seeding initial data...")
        if not seed_initial_data():
            success = False
            return
    
    if success:
        print("\n🎉 Database setup completed successfully!")
        print("You can now start the FastAPI application.")
    else:
        print("\n❌ Database setup failed. Please check the errors above.")

if __name__ == "__main__":
    main()
