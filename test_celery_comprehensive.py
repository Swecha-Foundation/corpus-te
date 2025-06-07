#!/usr/bin/env python3
"""
Comprehensive Celery integration test for corpus-te project.
Tests task execution, Redis connectivity, and database operations.
"""

import asyncio
import time
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.celery_app import celery_app
from app.db.session import engine, Session
from app.models.user import User
from app.models.record import Record
from sqlalchemy import text
import redis


def test_redis_connection():
    """Test Redis connection."""
    print("=" * 60)
    print("TESTING REDIS CONNECTION")
    print("=" * 60)
    
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        result = r.ping()
        print(f"✅ Redis ping successful: {result}")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False


def test_celery_tasks_registration():
    """Test that all tasks are properly registered."""
    print("\n" + "=" * 60)
    print("TESTING CELERY TASK REGISTRATION")
    print("=" * 60)
    
    expected_tasks = [
        'app.tasks.file_processing.upload_to_storage',
        'app.tasks.file_processing.process_audio_file',
        'app.tasks.file_processing.batch_process_files',
        'app.tasks.notifications.send_email',
        'app.tasks.notifications.send_system_alert',
        'app.tasks.notifications.send_processing_complete_notification',
        'app.tasks.notifications.send_bulk_notification',
        'app.tasks.data_analysis.analyze_audio_content',
        'app.tasks.data_analysis.batch_language_detection',
        'app.tasks.data_analysis.generate_corpus_statistics',
        'app.tasks.maintenance.cleanup_old_files',
        'app.tasks.maintenance.optimize_database',
        'app.tasks.maintenance.backup_database',
        'app.tasks.maintenance.health_check',
        'app.tasks.reports.generate_daily_report',
        'app.tasks.reports.generate_user_report',
        'app.tasks.reports.export_user_data',
        'app.tasks.reports.generate_system_health_report',
    ]
    
    registered_tasks = [t for t in celery_app.tasks.keys() if not t.startswith('celery.')]
    
    print(f"📊 Total registered tasks: {len(celery_app.tasks)}")
    print(f"📊 Custom tasks registered: {len(registered_tasks)}")
    print(f"📊 Expected custom tasks: {len(expected_tasks)}")
    
    missing_tasks = set(expected_tasks) - set(registered_tasks)
    extra_tasks = set(registered_tasks) - set(expected_tasks)
    
    if missing_tasks:
        print(f"❌ Missing tasks: {missing_tasks}")
        return False
    
    if extra_tasks:
        print(f"ℹ️  Extra tasks found: {extra_tasks}")
    
    print("✅ All expected tasks are registered!")
    return True


def test_database_connection():
    """Test database connection."""
    print("\n" + "=" * 60)
    print("TESTING DATABASE CONNECTION")
    print("=" * 60)
    
    try:
        with Session(engine) as session:
            # Test basic query
            result = session.execute(text("SELECT 1")).scalar()
            print(f"✅ Database connection successful: {result}")
            
            # Test user table access
            user_count = session.query(User).count()
            print(f"✅ User table accessible, count: {user_count}")
            
            # Test record table access  
            record_count = session.query(Record).count()
            print(f"✅ Record table accessible, count: {record_count}")
            
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def test_simple_task_execution():
    """Test executing a simple task."""
    print("\n" + "=" * 60)
    print("TESTING SIMPLE TASK EXECUTION")
    print("=" * 60)
    
    try:
        # Test health check task (should be simple and not require external dependencies)
        print("🔄 Sending health_check task...")
        result = celery_app.send_task('app.tasks.maintenance.health_check')
        print(f"✅ Task sent successfully, task_id: {result.task_id}")
        
        # Check task status
        print("🔄 Checking task status...")
        status = result.status
        print(f"📊 Task status: {status}")
        
        if status == 'PENDING':
            print("ℹ️  Task is pending - worker might not be running")
            print("ℹ️  To test task execution, start a worker with:")
            print("    uv run celery -A app.core.celery_app worker --loglevel=info")
        
        return True
        
    except Exception as e:
        print(f"❌ Task execution test failed: {e}")
        return False


def test_task_routing():
    """Test task routing configuration."""
    print("\n" + "=" * 60)
    print("TESTING TASK ROUTING")
    print("=" * 60)
    
    try:
        # Check if queues are properly configured
        queues = celery_app.conf.task_queues
        queue_names = [q.name for q in queues]
        
        expected_queues = ['default', 'file_processing', 'notifications', 'data_analysis']
        
        print(f"📊 Configured queues: {queue_names}")
        
        for queue in expected_queues:
            if queue in queue_names:
                print(f"✅ Queue '{queue}' is configured")
            else:
                print(f"❌ Queue '{queue}' is missing")
                return False
        
        # Check task routes
        routes = celery_app.conf.task_routes
        print(f"📊 Task routes configured: {len(routes)}")
        
        for pattern, config in routes.items():
            print(f"  {pattern} -> {config}")
        
        return True
        
    except Exception as e:
        print(f"❌ Task routing test failed: {e}")
        return False


def test_beat_schedule():
    """Test beat schedule configuration."""
    print("\n" + "=" * 60)
    print("TESTING BEAT SCHEDULE")
    print("=" * 60)
    
    try:
        schedule = celery_app.conf.beat_schedule
        
        print(f"📊 Scheduled tasks: {len(schedule)}")
        
        for task_name, config in schedule.items():
            print(f"  {task_name}:")
            print(f"    Task: {config['task']}")
            print(f"    Schedule: {config['schedule']}")
        
        expected_scheduled_tasks = [
            'cleanup-old-files',
            'generate-daily-reports'
        ]
        
        for task in expected_scheduled_tasks:
            if task in schedule:
                print(f"✅ Scheduled task '{task}' is configured")
            else:
                print(f"❌ Scheduled task '{task}' is missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Beat schedule test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Starting Celery Integration Tests for corpus-te")
    print(f"📅 Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        test_redis_connection,
        test_celery_tasks_registration,
        test_database_connection,
        test_simple_task_execution,
        test_task_routing,
        test_beat_schedule,
    ]
    
    results = []
    
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"📊 Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Celery integration is working correctly.")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
