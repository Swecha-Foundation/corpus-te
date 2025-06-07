#!/usr/bin/env python3
"""
Comprehensive test script for Celery integration in corpus-te project.
Tests task registration, basic functionality, and API integration.
"""

import asyncio
import json
import sys
import os
from uuid import uuid4
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, '/home/bhuvan/Swecha/SOAI/corpus-te/corpus-te')

def test_task_registration():
    """Test that all Celery tasks are properly registered."""
    print("🔍 Testing Celery task registration...")
    
    try:
        import app.tasks  # This registers all tasks
        from app.core.celery_app import celery_app
        
        expected_tasks = [
            'app.tasks.file_processing.process_audio_file',
            'app.tasks.file_processing.upload_to_storage',
            'app.tasks.file_processing.batch_process_files',
            'app.tasks.notifications.send_email',
            'app.tasks.notifications.send_processing_complete_notification',
            'app.tasks.notifications.send_bulk_notification',
            'app.tasks.notifications.send_system_alert',
            'app.tasks.data_analysis.analyze_audio_content',
            'app.tasks.data_analysis.generate_corpus_statistics',
            'app.tasks.data_analysis.batch_language_detection',
            'app.tasks.maintenance.cleanup_old_files',
            'app.tasks.maintenance.optimize_database',
            'app.tasks.maintenance.health_check',
            'app.tasks.maintenance.backup_database',
            'app.tasks.reports.generate_daily_report',
            'app.tasks.reports.generate_user_report',
            'app.tasks.reports.generate_system_health_report',
            'app.tasks.reports.export_user_data',
        ]
        
        registered_tasks = [name for name in celery_app.tasks.keys() if not name.startswith('celery.')]
        
        print(f"✅ Expected {len(expected_tasks)} tasks, found {len(registered_tasks)} tasks")
        
        missing_tasks = set(expected_tasks) - set(registered_tasks)
        if missing_tasks:
            print(f"❌ Missing tasks: {missing_tasks}")
            return False
        
        extra_tasks = set(registered_tasks) - set(expected_tasks)
        if extra_tasks:
            print(f"ℹ️  Extra tasks found: {extra_tasks}")
        
        print("✅ All expected tasks are registered!")
        return True
        
    except Exception as e:
        print(f"❌ Task registration test failed: {e}")
        return False

def test_task_imports():
    """Test that all task functions can be imported without errors."""
    print("\n🔍 Testing task imports...")
    
    try:
        from app.tasks import (
            process_audio_file, upload_to_storage, batch_process_files,
            send_email, send_processing_complete_notification, send_bulk_notification, send_system_alert,
            analyze_audio_content, generate_corpus_statistics, batch_language_detection,
            cleanup_old_files, optimize_database, health_check, backup_database,
            generate_daily_report, generate_user_report, generate_system_health_report, export_user_data
        )
        
        print("✅ All task functions imported successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Task import test failed: {e}")
        return False

def test_task_sync_execution():
    """Test synchronous execution of simple tasks (without Redis/workers)."""
    print("\n🔍 Testing synchronous task execution...")
    
    try:
        from app.tasks.maintenance import health_check
        
        # Test health check task (should work without external dependencies)
        print("  Testing health_check task...")
        
        # Create a mock self object for the bound task
        class MockTask:
            def update_state(self, state, meta=None):
                print(f"    Task state: {state}, meta: {meta}")
        
        mock_self = MockTask()
        result = health_check(mock_self)
        
        if isinstance(result, dict) and 'status' in result:
            print(f"  ✅ Health check completed: {result['status']}")
            return True
        else:
            print(f"  ❌ Unexpected health check result: {result}")
            return False
            
    except Exception as e:
        print(f"  ❌ Sync execution test failed: {e}")
        return False

def test_database_integration():
    """Test database connectivity for tasks."""
    print("\n🔍 Testing database integration...")
    
    try:
        from app.db.session import engine
        from sqlmodel import Session, text
        
        with Session(engine) as session:
            # Test basic database connectivity
            result = session.exec(text("SELECT 1 as test")).first()
            if result and result[0] == 1:
                print("  ✅ Database connectivity: OK")
            
            # Test model imports
            from app.models import User, Record, Category
            print("  ✅ Model imports: OK")
            
            # Test basic query
            users_count = session.exec(text("SELECT COUNT(*) FROM \"user\"")).first()
            records_count = session.exec(text("SELECT COUNT(*) FROM record")).first()
            print(f"  ✅ Database stats - Users: {users_count[0]}, Records: {records_count[0]}")
            
        return True
        
    except Exception as e:
        print(f"  ❌ Database integration test failed: {e}")
        return False

def test_storage_integration():
    """Test Hetzner storage integration."""
    print("\n🔍 Testing storage integration...")
    
    try:
        from app.utils.hetzner_storage import HetznerStorageClient
        
        # Just test initialization - don't perform actual operations
        storage_client = HetznerStorageClient()
        print("  ✅ Storage client initialization: OK")
        
        # Test if required methods exist
        methods = ['upload_file_data', 'delete_object', 'list_objects']
        for method in methods:
            if hasattr(storage_client, method):
                print(f"  ✅ Storage method '{method}': Available")
            else:
                print(f"  ❌ Storage method '{method}': Missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Storage integration test failed: {e}")
        return False

def test_celery_configuration():
    """Test Celery configuration."""
    print("\n🔍 Testing Celery configuration...")
    
    try:
        from app.core.celery_app import celery_app
        from app.core.config import settings
        
        # Test basic configuration
        print(f"  Celery app name: {celery_app.main}")
        print(f"  Broker URL configured: {'✅' if settings.CELERY_BROKER_URL else '❌'}")
        print(f"  Result backend configured: {'✅' if settings.CELERY_RESULT_BACKEND else '❌'}")
        
        # Test task routing
        if hasattr(celery_app.conf, 'task_routes'):
            print(f"  Task routing configured: ✅")
        
        print("  ✅ Celery configuration: OK")
        return True
        
    except Exception as e:
        print(f"  ❌ Celery configuration test failed: {e}")
        return False

def generate_test_report():
    """Generate a comprehensive test report."""
    print("\n" + "="*60)
    print("🎯 CORPUS-TE CELERY INTEGRATION TEST REPORT")
    print("="*60)
    
    tests = [
        ("Task Registration", test_task_registration),
        ("Task Imports", test_task_imports),
        ("Database Integration", test_database_integration),
        ("Storage Integration", test_storage_integration),
        ("Celery Configuration", test_celery_configuration),
        ("Sync Task Execution", test_task_sync_execution),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Celery integration is ready!")
        return True
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    print("Starting Corpus-TE Celery Integration Tests...")
    success = generate_test_report()
    
    print(f"\n{'='*60}")
    print("📋 NEXT STEPS:")
    print("="*60)
    
    if success:
        print("""
✅ Your Celery integration is ready! You can now:

1. Start Redis server:
   docker run -d -p 6379:6379 redis:alpine

2. Start Celery worker:
   cd /home/bhuvan/Swecha/SOAI/corpus-te/corpus-te
   python celery_worker.py

3. Start Celery beat scheduler (optional):
   cd /home/bhuvan/Swecha/SOAI/corpus-te/corpus-te
   python celery_beat.py

4. Test with FastAPI:
   python main.py
   # Then visit: http://localhost:8000/docs

5. Test task execution via API or Python:
   from app.tasks import health_check
   result = health_check.delay()
        """)
    else:
        print("""
⚠️  Please fix the failing tests before proceeding:

1. Check your database connection and models
2. Verify Hetzner storage configuration  
3. Ensure all task imports work correctly
4. Review Celery configuration settings

After fixes, run this test again to verify.
        """)
    
    sys.exit(0 if success else 1)
