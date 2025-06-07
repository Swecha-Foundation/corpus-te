"""
Task registration module for Celery.
Import all task modules to ensure they're registered with Celery.
"""

# Import all task modules to register them with Celery
from . import file_processing
from . import notifications
from . import data_analysis
from . import maintenance
from . import reports

# Re-export commonly used tasks for convenience
from .file_processing import process_audio_file, upload_to_storage, batch_process_files
from .notifications import send_email, send_processing_complete_notification, send_bulk_notification, send_system_alert
from .data_analysis import analyze_audio_content, generate_corpus_statistics, batch_language_detection
from .maintenance import cleanup_old_files, optimize_database, health_check, backup_database
from .reports import generate_daily_report, generate_user_report, generate_system_health_report, export_user_data

__all__ = [
    # File processing tasks
    'process_audio_file',
    'upload_to_storage', 
    'batch_process_files',
    
    # Notification tasks
    'send_email',
    'send_processing_complete_notification',
    'send_bulk_notification',
    'send_system_alert',
    
    # Data analysis tasks
    'analyze_audio_content',
    'generate_corpus_statistics',
    'batch_language_detection',
    
    # Maintenance tasks
    'cleanup_old_files',
    'optimize_database',
    'health_check',
    'backup_database',
    
    # Reporting tasks
    'generate_daily_report',
    'generate_user_report',
    'generate_system_health_report',
    'export_user_data',
]
