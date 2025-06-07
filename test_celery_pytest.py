#!/usr/bin/env python3
"""
Pytest-compatible test suite for Celery integration in corpus-te project.
Tests task registration, basic functionality, and API integration.
"""

import pytest
import sys
import os
from uuid import uuid4
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, '/home/bhuvan/Swecha/SOAI/corpus-te/corpus-te')

def test_task_registration():
    """Test that all Celery tasks are properly registered."""
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
    assert not missing_tasks, f"Missing tasks: {missing_tasks}"
    
    extra_tasks = set(registered_tasks) - set(expected_tasks)
    if extra_tasks:
        print(f"ℹ️  Extra tasks found: {extra_tasks}")
    
    print("✅ All expected tasks are registered!")
    assert len(expected_tasks) == 18

def test_task_imports():
    """Test that all task functions can be imported without errors."""
    from app.tasks import (
        process_audio_file, upload_to_storage, batch_process_files,
        send_email, send_processing_complete_notification, send_bulk_notification, send_system_alert,
        analyze_audio_content, generate_corpus_statistics, batch_language_detection,
        cleanup_old_files, optimize_database, health_check, backup_database,
        generate_daily_report, generate_user_report, generate_system_health_report, export_user_data
    )
    
    # Verify all functions are callable
    tasks = [
        process_audio_file, upload_to_storage, batch_process_files,
        send_email, send_processing_complete_notification, send_bulk_notification, send_system_alert,
        analyze_audio_content, generate_corpus_statistics, batch_language_detection,
        cleanup_old_files, optimize_database, health_check, backup_database,
        generate_daily_report, generate_user_report, generate_system_health_report, export_user_data
    ]
    
    for task in tasks:
        assert callable(task), f"Task {task} is not callable"
    
    print("✅ All task functions imported successfully!")

def test_task_sync_execution():
    """Test synchronous execution of simple tasks (without Redis/workers)."""
    from app.tasks.maintenance import health_check
    
    # Test health check task (should work without external dependencies)
    print("  Testing health_check task...")
    
    # For bound tasks, call the underlying function directly
    result = health_check()
    
    assert isinstance(result, dict), f"Expected dict result, got {type(result)}"
    assert 'status' in result, f"Missing 'status' key in result: {result}"
    assert 'health_status' in result, f"Missing 'health_status' key in result: {result}"
    
    health_status = result.get('health_status', {})
    overall_status = health_status.get('overall', 'unknown')
    
    print(f"  ✅ Health check completed: status={result['status']}, overall={overall_status}")

def test_database_integration():
    """Test database connectivity for tasks."""
    from app.db.session import engine
    from sqlmodel import Session, text
    
    with Session(engine) as session:
        # Test basic database connectivity
        result = session.exec(text("SELECT 1 as test")).first()
        assert result and result[0] == 1, "Database connectivity failed"
        print("  ✅ Database connectivity: OK")
        
        # Test model imports
        from app.models import User, Record, Category
        print("  ✅ Model imports: OK")
        
        # Test basic query
        users_count = session.exec(text("SELECT COUNT(*) FROM \"user\"")).first()
        records_count = session.exec(text("SELECT COUNT(*) FROM record")).first()
        
        assert users_count is not None, "User count query failed"
        assert records_count is not None, "Record count query failed"
        
        print(f"  ✅ Database stats - Users: {users_count[0]}, Records: {records_count[0]}")

def test_storage_integration():
    """Test Hetzner storage integration."""
    from app.utils.hetzner_storage import HetznerStorageClient
    
    # Just test initialization - don't perform actual operations
    storage_client = HetznerStorageClient()
    print("  ✅ Storage client initialization: OK")
    
    # Test if required methods exist
    methods = ['upload_file_data', 'delete_object', 'list_objects']
    for method in methods:
        assert hasattr(storage_client, method), f"Storage method '{method}' is missing"
        print(f"  ✅ Storage method '{method}': Available")

def test_celery_configuration():
    """Test Celery configuration."""
    from app.core.celery_app import celery_app
    from app.core.config import settings
    
    # Test basic configuration
    assert celery_app.main, "Celery app name not configured"
    print(f"  Celery app name: {celery_app.main}")
    
    # Test configuration availability (settings may be empty in test mode)
    broker_configured = bool(settings.CELERY_BROKER_URL)
    result_backend_configured = bool(settings.CELERY_RESULT_BACKEND)
    
    print(f"  Broker URL configured: {'✅' if broker_configured else '❌'}")
    print(f"  Result backend configured: {'✅' if result_backend_configured else '❌'}")
    
    # Test task routing (optional)
    if hasattr(celery_app.conf, 'task_routes'):
        print(f"  Task routing configured: ✅")
    
    print("  ✅ Celery configuration: OK")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
