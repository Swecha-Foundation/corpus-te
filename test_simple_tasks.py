#!/usr/bin/env python3
"""
Simple task execution test - focusing on working tasks only.
"""

import time
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.celery_app import celery_app


def test_simple_tasks():
    """Test simple working tasks."""
    print("🚀 Testing Simple Working Tasks")
    print("=" * 60)
    
    # Test only tasks that we know work
    test_tasks = [
        {
            'name': 'Health Check',
            'task': 'app.tasks.maintenance.health_check',
            'args': [],
        },
        {
            'name': 'Generate Corpus Statistics',
            'task': 'app.tasks.data_analysis.generate_corpus_statistics',
            'args': [],
        },
    ]
    
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
            
            # Wait for completion 
            for i in range(15):  # Wait up to 15 seconds
                status = result.status
                if status == 'SUCCESS':
                    task_result = result.get()
                    print(f"   ✅ Success: {task_result}")
                    break
                elif status == 'FAILURE':
                    print(f"   ❌ Failed: {result.traceback}")
                    break
                elif i == 14:
                    print(f"   ⏱️  Timeout: Status {status}")
                    break
                else:
                    print(f"   Status: {status}", end='\r')
                    time.sleep(1)
                    
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print(f"\n🎉 Simple task testing completed!")


if __name__ == "__main__":
    test_simple_tasks()
