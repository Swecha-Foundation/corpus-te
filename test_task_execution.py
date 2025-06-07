#!/usr/bin/env python3
"""
Test actual task execution with a running Celery worker.
"""

import time
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.celery_app import celery_app


def test_task_execution():
    """Test executing tasks and waiting for results."""
    print("🚀 Testing Task Execution with Running Worker")
    print("=" * 60)
    
    # Test simple tasks that should complete quickly
    test_tasks = [
        {
            'name': 'Health Check',
            'task': 'app.tasks.maintenance.health_check',
            'args': [],
            'timeout': 30
        },
        {
            'name': 'Generate Corpus Statistics',
            'task': 'app.tasks.data_analysis.generate_corpus_statistics',
            'args': [],
            'timeout': 30
        },
        {
            'name': 'Generate System Health Report',
            'task': 'app.tasks.reports.generate_system_health_report',
            'args': [],
            'timeout': 30
        }
    ]
    
    results = []
    
    for test_case in test_tasks:
        print(f"\n🔄 Testing: {test_case['name']}")
        print(f"   Task: {test_case['task']}")
        
        try:
            # Send task
            result = celery_app.send_task(
                test_case['task'], 
                args=test_case['args']
            )
            
            print(f"   Task ID: {result.task_id}")
            print(f"   Initial Status: {result.status}")
            
            # Wait for completion with timeout
            start_time = time.time()
            timeout = test_case['timeout']
            
            while time.time() - start_time < timeout:
                status = result.status
                print(f"   Status: {status}", end='\r')
                
                if status in ['SUCCESS', 'FAILURE', 'REVOKED']:
                    break
                    
                time.sleep(1)
            
            final_status = result.status
            print(f"\n   Final Status: {final_status}")
            
            if final_status == 'SUCCESS':
                try:
                    task_result = result.get()
                    print(f"   ✅ Result: {task_result}")
                    results.append(True)
                except Exception as e:
                    print(f"   ⚠️  Result Error: {e}")
                    results.append(False)
            elif final_status == 'FAILURE':
                try:
                    error = result.traceback
                    print(f"   ❌ Error: {error}")
                    results.append(False)
                except Exception as e:
                    print(f"   ❌ Failed to get error: {e}")
                    results.append(False)
            else:
                print(f"   ⏱️  Timeout or pending: Status {final_status}")
                results.append(False)
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("TASK EXECUTION SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"📊 Tasks completed successfully: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tasks executed successfully!")
        return 0
    else:
        print(f"⚠️  {total - passed} task(s) failed or timed out.")
        return 1


def check_worker_status():
    """Check if workers are running."""
    print("🔍 Checking Worker Status")
    print("=" * 60)
    
    try:
        inspect = celery_app.control.inspect()
        
        # Get active workers
        stats = inspect.stats()
        if stats:
            print(f"✅ Found {len(stats)} active worker(s):")
            for worker_name, worker_stats in stats.items():
                print(f"   - {worker_name}")
        else:
            print("❌ No active workers found!")
            print("   Start a worker with:")
            print("   uv run celery -A app.core.celery_app worker --loglevel=info")
            return False
            
        # Get active tasks
        active = inspect.active()
        if active:
            total_active = sum(len(worker_tasks) for worker_tasks in active.values())
            print(f"📊 Active tasks: {total_active}")
        else:
            print("📊 No active tasks")
            
        return True
        
    except Exception as e:
        print(f"❌ Error checking worker status: {e}")
        return False


def main():
    """Run the task execution test."""
    print(f"📅 Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check worker status first
    if not check_worker_status():
        print("\n⚠️  No workers available for testing.")
        return 1
    
    # Run task execution tests
    return test_task_execution()


if __name__ == "__main__":
    sys.exit(main())
