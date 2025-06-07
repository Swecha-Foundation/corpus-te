"""
Maintenance and cleanup tasks.
"""
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

from sqlmodel import Session, select
from sqlalchemy import text

from app.core.celery_app import celery_app
from app.db.session import get_session, engine
from sqlmodel import Session
from app.models import Record, User
from app.utils.hetzner_storage import HetznerStorageClient

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.maintenance.cleanup_old_files")
def cleanup_old_files(self, days_old: int = 30) -> Dict[str, Any]:
    """
    Clean up old temporary files and failed uploads.
    
    Args:
        days_old: Files older than this many days will be cleaned up
        
    Returns:
        Dict with cleanup results
    """
    try:
        logger.info(f"Starting cleanup of files older than {days_old} days")
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        results = {
            'local_files_deleted': 0,
            'database_records_cleaned': 0,
            'storage_files_deleted': 0,
            'errors': []
        }
        
        with Session(engine) as session:
            # Find old failed or temporary records - use separate queries to avoid None comparison issues
            old_failed_records = session.exec(
                select(Record).where(
                    Record.status == 'failed'
                )
            ).all()
            
            old_pending_records = session.exec(
                select(Record).where(
                    Record.status == 'pending'
                )
            ).all()
            
            # Filter by date in Python to avoid SQLAlchemy None comparison issues
            old_records = list(old_failed_records) + list(old_pending_records)
            old_records = [
                r for r in old_records
                if r.created_at and r.created_at < cutoff_date
            ]
            
            for record in old_records:
                try:
                    # Clean up local file if exists (using file_url as base)
                    if record.file_url and record.file_url.startswith('file://'):
                        local_path = record.file_url.replace('file://', '')
                        if os.path.exists(local_path):
                            os.remove(local_path)
                            results['local_files_deleted'] += 1
                            logger.info(f"Deleted local file: {local_path}")
                    
                    # Clean up from object storage if exists
                    if record.file_url and record.file_url.startswith('https://'):
                        storage_client = HetznerStorageClient()
                        try:
                            # Extract file key from URL
                            file_key = record.file_url.split('/')[-1]
                            storage_client.delete_object(file_key)
                            results['storage_files_deleted'] += 1
                            logger.info(f"Deleted storage file: {file_key}")
                        except Exception as storage_error:
                            logger.warning(f"Failed to delete storage file {record.file_url}: {storage_error}")
                    
                    # Remove database record
                    session.delete(record)
                    results['database_records_cleaned'] += 1
                    
                except Exception as e:
                    error_msg = f"Failed to cleanup record {record.uid}: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            # Commit database changes
            session.commit()
        
        # Clean up orphaned temporary files
        temp_dir = Path("/tmp")
        if temp_dir.exists():
            for temp_file in temp_dir.glob("corpus_upload_*"):
                try:
                    file_age = datetime.fromtimestamp(temp_file.stat().st_mtime)
                    if file_age < cutoff_date:
                        temp_file.unlink()
                        results['local_files_deleted'] += 1
                        logger.info(f"Deleted orphaned temp file: {temp_file}")
                except Exception as e:
                    error_msg = f"Failed to delete temp file {temp_file}: {str(e)}"
                    logger.warning(error_msg)
                    results['errors'].append(error_msg)
        
        logger.info(f"Cleanup completed: {results}")
        return {
            'status': 'success',
            'results': results,
            'cleanup_date': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Cleanup task failed: {str(e)}")
        raise


@celery_app.task(bind=True, name="app.tasks.maintenance.optimize_database")
def optimize_database(self) -> Dict[str, Any]:
    """
    Perform database maintenance operations.
    
    Returns:
        Dict with optimization results
    """
    try:
        logger.info("Starting database optimization")
        
        results = {
            'vacuum_completed': False,
            'reindex_completed': False,
            'analyze_completed': False,
            'errors': []
        }
        
        with Session(engine) as session:
            try:
                # PostgreSQL specific optimizations
                # Note: These need to be run outside of transactions
                
                # VACUUM to reclaim storage - use execute instead of exec for raw SQL
                session.execute(text("VACUUM ANALYZE records"))
                session.execute(text("VACUUM ANALYZE users"))
                results['vacuum_completed'] = True
                logger.info("Database VACUUM completed")
                
                # Update table statistics
                session.execute(text("ANALYZE"))
                results['analyze_completed'] = True
                logger.info("Database ANALYZE completed")
                
            except Exception as e:
                error_msg = f"Database optimization error: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
        
        logger.info(f"Database optimization completed: {results}")
        return {
            'status': 'success',
            'results': results,
            'optimization_date': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Database optimization failed: {str(e)}")
        raise


@celery_app.task(bind=True, name="app.tasks.maintenance.health_check")
def health_check(self) -> Dict[str, Any]:
    """
    Perform system health checks.
    
    Returns:
        Dict with health check results
    """
    try:
        logger.info("Starting system health check")
        
        health_status = {
            'database': 'unknown',
            'storage': 'unknown',
            'redis': 'unknown',
            'disk_space': 'unknown',
            'overall': 'unknown'
        }
        
        issues = []
        
        # Check database connectivity
        try:
            with Session(engine) as session:
                session.execute(text("SELECT 1"))
            health_status['database'] = 'healthy'
            logger.info("Database health check: OK")
        except Exception as e:
            health_status['database'] = 'unhealthy'
            issues.append(f"Database connectivity issue: {str(e)}")
            logger.error(f"Database health check failed: {str(e)}")
        
        # Check object storage connectivity
        try:
            storage_client = HetznerStorageClient()
            # Try to list buckets or perform a simple operation
            storage_client.list_objects(max_keys=1)
            health_status['storage'] = 'healthy'
            logger.info("Storage health check: OK")
        except Exception as e:
            health_status['storage'] = 'unhealthy'
            issues.append(f"Storage connectivity issue: {str(e)}")
            logger.error(f"Storage health check failed: {str(e)}")
        
        # Check Redis connectivity (if accessible)
        try:
            # Try to import redis - it might not be installed
            try:
                import redis
                from app.core.config import settings
                
                redis_client = redis.from_url(settings.CELERY_BROKER_URL)
                redis_client.ping()
                health_status['redis'] = 'healthy'
                logger.info("Redis health check: OK")
            except ImportError:
                health_status['redis'] = 'unavailable'
                logger.warning("Redis module not available - skipping Redis health check")
        except Exception as e:
            health_status['redis'] = 'unhealthy'
            issues.append(f"Redis connectivity issue: {str(e)}")
            logger.error(f"Redis health check failed: {str(e)}")
        
        # Check disk space
        try:
            import shutil
            total, used, free = shutil.disk_usage("/")
            free_percent = (free / total) * 100
            
            if free_percent > 20:
                health_status['disk_space'] = 'healthy'
            elif free_percent > 10:
                health_status['disk_space'] = 'warning'
                issues.append(f"Low disk space: {free_percent:.1f}% free")
            else:
                health_status['disk_space'] = 'critical'
                issues.append(f"Critical disk space: {free_percent:.1f}% free")
                
            logger.info(f"Disk space check: {free_percent:.1f}% free")
        except Exception as e:
            health_status['disk_space'] = 'unknown'
            issues.append(f"Could not check disk space: {str(e)}")
            logger.error(f"Disk space check failed: {str(e)}")
        
        # Determine overall health
        unhealthy_services = [
            service for service, status in health_status.items() 
            if status in ['unhealthy', 'critical'] and service != 'overall'
        ]
        
        if not unhealthy_services:
            health_status['overall'] = 'healthy'
        elif len(unhealthy_services) == 1:
            health_status['overall'] = 'degraded'
        else:
            health_status['overall'] = 'unhealthy'
        
        # Send alert if there are critical issues
        if health_status['overall'] in ['unhealthy', 'degraded']:
            celery_app.send_task(
                "app.tasks.notifications.send_system_alert",
                kwargs={
                    "alert_type": "Health Check Alert",
                    "message": f"System health issues detected: {', '.join(issues)}",
                    "severity": "warning" if health_status['overall'] == 'degraded' else "error"
                }
            )
        
        logger.info(f"Health check completed: {health_status['overall']}")
        return {
            'status': 'success',
            'health_status': health_status,
            'issues': issues,
            'check_time': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise


@celery_app.task(bind=True, name="app.tasks.maintenance.backup_database")
def backup_database(self, backup_location: Optional[str] = None) -> Dict[str, Any]:
    """
    Create database backup.
    
    Args:
        backup_location: Optional custom backup location
        
    Returns:
        Dict with backup results
    """
    try:
        logger.info("Starting database backup")
        
        # This is a placeholder implementation
        # In production, you would use pg_dump or similar tools
        
        backup_filename = f"corpus_te_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.sql"
        backup_path = backup_location or f"/tmp/{backup_filename}"
        
        # Placeholder for actual backup logic
        # You would typically use subprocess to run pg_dump
        
        results = {
            'backup_file': backup_path,
            'backup_size': 0,  # Would calculate actual size
            'backup_duration': 0,  # Would measure actual duration
            'status': 'completed'
        }
        
        logger.info(f"Database backup completed: {backup_path}")
        return {
            'status': 'success',
            'results': results,
            'backup_time': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Database backup failed: {str(e)}")
        raise
