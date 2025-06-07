#!/usr/bin/env python3
"""
Docker Database Initialization Script

This script runs the complete database setup within the Docker environment:
1. Waits for PostgreSQL to be ready
2. Creates database if needed
3. Enables PostGIS extension
4. Runs database migrations
5. Seeds initial data
6. Validates PostGIS functionality

This should be run as a one-time initialization service in Docker.
"""

import os
import sys
import time
import logging
from setup_postgresql import (
    test_postgres_connection,
    create_database,
    test_database_connection,
    check_postgis_availability,
    enable_postgis,
    run_migrations,
    seed_initial_data,
    validate_postgis_functionality,
    validate_record_table_postgis
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def wait_for_postgres(max_retries=30, delay=2):
    """Wait for PostgreSQL to be ready."""
    logger.info("🔍 Waiting for PostgreSQL to be ready...")
    
    for attempt in range(max_retries):
        try:
            if test_postgres_connection():
                logger.info("✅ PostgreSQL is ready!")
                return True
        except Exception as e:
            logger.info(f"Attempt {attempt + 1}/{max_retries}: PostgreSQL not ready yet...")
        
        if attempt < max_retries - 1:
            time.sleep(delay)
    
    logger.error("❌ PostgreSQL failed to become ready within timeout")
    return False

def initialize_database():
    """Run complete database initialization."""
    logger.info("🚀 Starting database initialization...")
    
    # Step 1: Wait for PostgreSQL
    if not wait_for_postgres():
        logger.error("❌ PostgreSQL not available, aborting initialization")
        return False
    
    # Step 2: Check PostGIS availability
    logger.info("🗺️  Checking PostGIS availability...")
    if not check_postgis_availability():
        logger.error("❌ PostGIS not available in PostgreSQL image")
        return False
    
    # Step 3: Create database
    logger.info("🏗️  Creating database if needed...")
    if not create_database():
        logger.error("❌ Failed to create database")
        return False
    
    # Step 4: Test database connection
    logger.info("🔍 Testing database connection...")
    if not test_database_connection():
        logger.error("❌ Failed to connect to database")
        return False
    
    # Step 5: Enable PostGIS
    logger.info("🗺️  Enabling PostGIS extension...")
    if not enable_postgis():
        logger.error("❌ Failed to enable PostGIS")
        return False
    
    # Step 6: Run migrations
    logger.info("🚀 Running database migrations...")
    if not run_migrations():
        logger.error("❌ Failed to run migrations")
        return False
    
    # Step 7: Validate PostGIS functionality
    logger.info("🧪 Validating PostGIS functionality...")
    if not validate_postgis_functionality():
        logger.warning("⚠️  PostGIS validation failed, but continuing...")
    
    # Step 8: Validate Record table PostGIS schema
    logger.info("🔍 Validating Record table PostGIS schema...")
    if not validate_record_table_postgis():
        logger.warning("⚠️  Record table validation failed, but continuing...")
    
    # Step 9: Seed initial data
    logger.info("🌱 Seeding initial data...")
    if not seed_initial_data():
        logger.warning("⚠️  Failed to seed initial data, but continuing...")
    
    logger.info("🎉 Database initialization completed successfully!")
    return True

def main():
    """Main initialization function."""
    try:
        success = initialize_database()
        if success:
            logger.info("✅ Database initialization completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Database initialization failed!")
            sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error during initialization: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
