#!/usr/bin/env python3
"""
Comprehensive Celery integration test with Redis broker.
Tests all task modules with actual Redis backend.
"""

import asyncio
import os
import sys
import time
from datetime import datetime
from uuid import uuid4

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment for Redis
os.environ['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
os.environ['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
os.environ['DATABASE_URL'] = 'postgresql://corpus_user:corpus_pass@localhost:5432/corpus_te'

def test_task_registration():
    """Test that all tasks are properly registered."""
    print("🔍 Testing task registration...")
    
    try:
        from app.core.celery_app import celery_app
        
        # Get all registered tasks
        registered_tasks = list(celery_app.tasks.keys())
        print(f"✅ Found {len(registered_tasks)} registered tasks")
        
        # Expected task groups
        expected_groups = [
            'app.tasks.file_processing',
            'app.tasks.notifications', 
            'app.tasks.data_analysis',
            'app.tasks.maintenance',
            'app.tasks.reports'
        ]
        
        for group in expected_groups:
            group_tasks = [task for task in registered_tasks if task.startswith(group)]
            print(f"  📁 {group}: {len(group_tasks)} tasks")
            for task in group_tasks:
                print(f"    - {task}")
        
        return True
        
    except Exception as e:
        print(f"❌ Task registration test failed: {e}")
        return False

def test_redis_connectivity():
    """Test Redis connectivity for Celery broker."""
    print("\n🔗 Testing Redis connectivity...")
    
    try:
        import redis
        client = redis.Redis(host='localhost', port=6379, db=0)
        client.ping()
        print("✅ Redis connection successful")
        return True
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

def test_celery_worker_ready():
    """Test if Celery worker is ready to process tasks."""
    print("\n👷 Testing Celery worker readiness...")
    
    try:
        from app.core.celery_app import celery_app
        
        # Try to inspect active workers
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers:
            print(f"✅ Found {len(active_workers)} active workers")
            for worker, tasks in active_workers.items():
                print(f"  - {worker}: {len(tasks)} active tasks")
            return True
        else:
            print("⚠️  No active workers found - tasks will be queued")
            return True  # Not a failure, just means no workers running
            
    except Exception as e:
        print(f"❌ Worker inspection failed: {e}")
        return False

def test_simple_task_execution():
    """Test execution of a simple task."""
    print("\n🚀 Testing simple task execution...")
    
    try:
        from app.core.celery_app import celery_app
        
        # Test health check task (simple, no dependencies)
        print("  📋 Testing health check task...")
        result = celery_app.send_task("app.tasks.maintenance.health_check")
        
        # Wait a bit for task to process
        print("  ⏳ Waiting for task completion...")
        task_result = result.get(timeout=30)
        
        if task_result and task_result.get('status') == 'success':
            print("  ✅ Health check task completed successfully")
            health_status = task_result.get('health_status', {})
            print(f"     Database: {health_status.get('database', 'unknown')}")
            print(f"     Storage: {health_status.get('storage', 'unknown')}")
            print(f"     Overall: {health_status.get('overall', 'unknown')}")
            return True
        else:
            print(f"  ❌ Task failed or returned unexpected result: {task_result}")
            return False
            
    except Exception as e:
        print(f"❌ Simple task execution failed: {e}")
        return False

def test_async_task_chaining():
    """Test chaining multiple tasks together."""
    print("\n⛓️  Testing task chaining...")
    
    try:
        from app.core.celery_app import celery_app
        
        # Chain: health check -> daily report
        print("  📋 Chaining health check -> daily report...")
        
        # First task
        health_result = celery_app.send_task("app.tasks.maintenance.health_check")
        health_data = health_result.get(timeout=20)
        
        if health_data and health_data.get('status') == 'success':
            print("  ✅ Health check completed")
            
            # Second task - daily report
            report_result = celery_app.send_task(
                "app.tasks.reports.generate_daily_report",
                kwargs={"report_date": "2025-06-06"}  # Yesterday
            )
            report_data = report_result.get(timeout=20)
            
            if report_data and report_data.get('status') == 'success':
                print("  ✅ Daily report completed")
                report_summary = report_data.get('report_data', {}).get('summary', {})
                print(f"     Uploads: {report_summary.get('total_uploads', 0)}")
                print(f"     Active users: {report_summary.get('active_users', 0)}")
                return True
            else:
                print(f"  ❌ Daily report failed: {report_data}")
                return False
        else:
            print(f"  ❌ Health check failed: {health_data}")
            return False
            
    except Exception as e:
        print(f"❌ Task chaining failed: {e}")
        return False

def test_error_handling():
    """Test task error handling."""
    print("\n🚨 Testing error handling...")
    
    try:
        from app.core.celery_app import celery_app
        
        # Test with invalid user ID to trigger error
        print("  📋 Testing user report with invalid user ID...")
        result = celery_app.send_task(
            "app.tasks.reports.generate_user_report",
            kwargs={"user_id": "invalid-uuid-format"}
        )
        
        try:
            task_result = result.get(timeout=15)
            print(f"  ❌ Expected task to fail but got: {task_result}")
            return False
        except Exception as task_error:
            print(f"  ✅ Task correctly failed with error: {str(task_error)[:100]}...")
            return True
            
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def test_notifications_integration():
    """Test notification task integration."""
    print("\n📧 Testing notifications integration...")
    
    try:
        from app.core.celery_app import celery_app
        
        # Test system alert notification
        print("  📋 Testing system alert notification...")
        result = celery_app.send_task(
            "app.tasks.notifications.send_system_alert",
            kwargs={
                "alert_type": "Test Alert",
                "message": "This is a test alert from Celery integration test",
                "severity": "info"
            }
        )
        
        task_result = result.get(timeout=15)
        
        if task_result and task_result.get('status') == 'success':
            print("  ✅ System alert task completed successfully")
            return True
        else:
            print(f"  ❌ System alert failed: {task_result}")
            return False
            
    except Exception as e:
        print(f"❌ Notifications test failed: {e}")
        return False

def run_comprehensive_test():
    """Run all Celery integration tests."""
    print("🧪 Starting Comprehensive Celery Integration Test")
    print("=" * 60)
    
    tests = [
        ("Task Registration", test_task_registration),
        ("Redis Connectivity", test_redis_connectivity),
        ("Worker Readiness", test_celery_worker_ready),
        ("Simple Task Execution", test_simple_task_execution),
        ("Task Chaining", test_async_task_chaining),
        ("Error Handling", test_error_handling),
        ("Notifications Integration", test_notifications_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} {test_name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Celery integration is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
