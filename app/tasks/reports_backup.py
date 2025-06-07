"""
Report generation tasks.
"""
import logging
import os
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional
import json

from sqlmodel import Session, select, func

from app.core.celery_app import celery_app
from app.db.session import engine
from sqlmodel import Session
from app.models import Record, User

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.reports.generate_daily_report")
def generate_daily_report(self, report_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate daily activity report.
    
    Args:
        report_date: Date to generate report for (YYYY-MM-DD format)
        
    Returns:
        Dict with report data
    """
    try:
        if report_date:
            target_date = datetime.strptime(report_date, '%Y-%m-%d').date()
        else:
            target_date = (datetime.utcnow() - timedelta(days=1)).date()  # Yesterday
        
        logger.info(f"Generating daily report for {target_date}")
        
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())
        
        with get_session() as session:
            # Records uploaded today
            new_records = session.exec(
                select(Record).where(
                    Record.created_at >= start_datetime,
                    Record.created_at <= end_datetime
                )
            ).all()
            
            # Records processed today - using status instead of processing_status
            processed_records = session.exec(
                select(Record).where(
                    Record.updated_at >= start_datetime,
                    Record.updated_at <= end_datetime,
                    Record.status == 'completed'
                )
            ).all()
            
            # User activity
            active_users = session.exec(
                select(func.count(func.distinct(Record.user_id))).where(
                    Record.created_at >= start_datetime,
                    Record.created_at <= end_datetime
                )
            ).first()
            
            # Calculate statistics
            total_uploaded = len(new_records)
            total_processed = len(processed_records)
            # total_duration = sum(r.audio_duration or 0 for r in processed_records) # Field doesn't exist
            
            # File type breakdown - using media_type instead of file_type
            file_types = {}
            for record in new_records:
                file_type = record.media_type or 'unknown'
                file_types[file_type] = file_types.get(file_type, 0) + 1
            
            # Language breakdown - commenting out since field doesn't exist
            languages = {}
            # for record in processed_records:
            #     if record.detected_language:
            #         lang = record.detected_language
            #         languages[lang] = languages.get(lang, 0) + 1
            
            # Processing success rate
            failed_records = session.exec(
                select(func.count(Record.uid)).where(
                    Record.updated_at >= start_datetime,
                    Record.updated_at <= end_datetime,
                    Record.status == 'failed'
                )
            ).first()
            
            total_attempts = total_processed + (failed_records or 0)
            success_rate = (total_processed / total_attempts * 100) if total_attempts > 0 else 0
            
            report_data = {
                'report_date': target_date.isoformat(),
                'summary': {
                    'total_uploads': total_uploaded,
                    'total_processed': total_processed,
                    'total_failed': failed_records or 0,
                    'active_users': active_users or 0,
                    'success_rate_percent': round(success_rate, 2),
                    'total_audio_duration_seconds': 0  # Placeholder since field doesn't exist
                },
                'file_types': file_types,
                'languages': languages,
                'generated_at': datetime.utcnow().isoformat()
            }
            
            # Store report in database or send via email
            # For now, we'll just log it
            logger.info(f"Daily report generated: {json.dumps(report_data, indent=2)}")
            
            # Send report to administrators
            celery_app.send_task(
                "app.tasks.notifications.send_system_alert",
                kwargs={
                    "alert_type": "Daily Report",
                    "message": f"Daily activity report for {target_date}:\n"
                               f"Uploads: {total_uploaded}, Processed: {total_processed}, "
                               f"Active Users: {active_users}, Success Rate: {success_rate:.1f}%",
                    "severity": "info"
                }
            )
            
            return {
                'status': 'success',
                'report_data': report_data
            }
            
    except Exception as e:
        logger.error(f"Failed to generate daily report: {str(e)}")
        raise


@celery_app.task(bind=True, name="app.tasks.reports.generate_user_report")
def generate_user_report(self, user_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate user activity report.
    
    Args:
        user_id: User ID to generate report for
        start_date: Start date (YYYY-MM-DD format)
        end_date: End date (YYYY-MM-DD format)
        
    Returns:
        Dict with user report data
    """
    try:
        logger.info(f"Generating user report for user {user_id}")
        
        # Default to last 30 days if dates not provided
        if not end_date:
            end_date_obj = datetime.utcnow().date()
        else:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            
        if not start_date:
            start_date_obj = end_date_obj - timedelta(days=30)
        else:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        start_datetime = datetime.combine(start_date_obj, datetime.min.time())
        end_datetime = datetime.combine(end_date_obj, datetime.max.time())
        
        with get_session() as session:
            # Get user info
            user = session.get(User, user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Get user's records in date range
            user_records = session.exec(
                select(Record).where(
                    Record.user_id == user_id,
                    Record.created_at >= start_datetime,
                    Record.created_at <= end_datetime
                )
            ).all()
            
            # Calculate statistics
            total_uploads = len(user_records)
            processed_count = sum(1 for r in user_records if r.status == 'completed')
            failed_count = sum(1 for r in user_records if r.status == 'failed')
            pending_count = total_uploads - processed_count - failed_count
            
            # total_duration = sum(r.audio_duration or 0 for r in user_records if r.audio_duration) # Field doesn't exist
            
            # File type breakdown - using media_type
            file_types = {}
            for record in user_records:
                file_type = record.media_type or 'unknown'
                file_types[file_type] = file_types.get(file_type, 0) + 1
            
            # Daily activity (uploads per day)
            daily_activity = {}
            for record in user_records:
                if record.created_at:
                    day = record.created_at.date().isoformat()
                    daily_activity[day] = daily_activity.get(day, 0) + 1
            
            # Success rate
            success_rate = (processed_count / total_uploads * 100) if total_uploads > 0 else 0
            
            report_data = {
                'user_id': user_id,
                'username': user.name,  # Using name instead of username
                'email': user.email,
                'report_period': {
                    'start_date': start_date_obj.isoformat(),
                    'end_date': end_date_obj.isoformat()
                },
                'summary': {
                    'total_uploads': total_uploads,
                    'processed_count': processed_count,
                    'failed_count': failed_count,
                    'pending_count': pending_count,
                    'success_rate_percent': round(success_rate, 2),
                    'total_audio_duration_seconds': 0  # Placeholder since field doesn't exist
                },
                'file_types': file_types,
                'daily_activity': daily_activity,
                'generated_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"User report generated for user {user_id}: {total_uploads} uploads")
            
            return {
                'status': 'success',
                'report_data': report_data
            }
            
    except Exception as e:
        logger.error(f"Failed to generate user report: {str(e)}")
        raise


@celery_app.task(bind=True, name="app.tasks.reports.generate_system_health_report")
def generate_system_health_report(self) -> Dict[str, Any]:
    """
    Generate comprehensive system health report.
    
    Returns:
        Dict with system health report data
    """
    try:
        logger.info("Generating system health report")
        
        # Get current system health
        health_result = celery_app.send_task("app.tasks.maintenance.health_check").get()
        
        with get_session() as session:
            # Database statistics - using User.uid instead of User.id
            total_users = session.exec(select(func.count(User.uid))).first()
            total_records = session.exec(select(func.count(Record.uid))).first()
            
            # Processing statistics - using status instead of processing_status
            completed_records = session.exec(
                select(func.count(Record.uid)).where(Record.status == 'completed')
            ).first()
            
            failed_records = session.exec(
                select(func.count(Record.uid)).where(Record.status == 'failed')
            ).first()
            
            pending_records = session.exec(
                select(func.count(Record.uid)).where(Record.status == 'pending')
            ).first()
            
            # Recent activity (last 24 hours)
            yesterday = datetime.utcnow() - timedelta(days=1)
            recent_uploads = session.exec(
                select(func.count(Record.uid)).where(Record.created_at >= yesterday)
            ).first()
            
            # Storage usage - using file_size with proper check
            total_file_size = session.exec(
                select(func.sum(Record.file_size)).where(Record.file_size != None)
            ).first()
            
            report_data = {
                'system_health': health_result.get('health_status', {}),
                'database_stats': {
                    'total_users': total_users or 0,
                    'total_records': total_records or 0,
                    'completed_records': completed_records or 0,
                    'failed_records': failed_records or 0,
                    'pending_records': pending_records or 0
                },
                'activity_stats': {
                    'recent_uploads_24h': recent_uploads or 0,
                    'overall_success_rate': round(
                        (completed_records / total_records * 100) if total_records and completed_records else 0, 2
                    )
                },
                'storage_stats': {
                    'total_file_size_bytes': total_file_size or 0,
                    'total_file_size_mb': round((total_file_size or 0) / (1024 * 1024), 2)
                },
                'generated_at': datetime.utcnow().isoformat()
            }
            
            logger.info("System health report generated successfully")
            
            # Send critical alerts if needed
            if health_result.get('health_status', {}).get('overall') in ['unhealthy', 'degraded']:
                celery_app.send_task(
                    "app.tasks.notifications.send_system_alert",
                    kwargs={
                        "alert_type": "System Health Report",
                        "message": f"System health issues detected in daily report. "
                                   f"Overall status: {health_result.get('health_status', {}).get('overall')}",
                        "severity": "error"
                    }
                )
            
            return {
                'status': 'success',
                'report_data': report_data
            }
            
    except Exception as e:
        logger.error(f"Failed to generate system health report: {str(e)}")
        raise


@celery_app.task(bind=True, name="app.tasks.reports.export_user_data")
def export_user_data(self, user_id: int, export_format: str = "json") -> Dict[str, Any]:
    """
    Export all user data (for GDPR compliance, data portability, etc.).
    
    Args:
        user_id: User ID to export data for
        export_format: Export format (json, csv, etc.)
        
    Returns:
        Dict with export results
    """
    try:
        logger.info(f"Exporting user data for user {user_id} in {export_format} format")
        
        with get_session() as session:
            # Get user info
            user = session.get(User, user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Get all user records
            user_records = session.exec(
                select(Record).where(Record.user_id == user_id)
            ).all()
            
            # Prepare export data with available fields only
            export_data = {
                'user_info': {
                    'uid': str(user.uid),  # Using uid instead of id
                    'name': user.name,  # Using name instead of username
                    'email': user.email,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'updated_at': user.updated_at.isoformat() if user.updated_at else None
                },
                'records': [
                    {
                        'uid': str(record.uid),  # Using uid instead of id
                        'file_url': record.file_url,
                        'media_type': record.media_type,  # Using media_type instead of file_type
                        'file_size': record.file_size,
                        'status': record.status,  # Using status instead of processing_status
                        'created_at': record.created_at.isoformat() if record.created_at else None,
                        'updated_at': record.updated_at.isoformat() if record.updated_at else None
                        # Commented out fields that don't exist:
                        # 'transcription': record.transcription,
                        # 'detected_language': record.detected_language,
                        # 'confidence_score': record.confidence_score,
                        # 'filename': record.filename,
                    }
                    for record in user_records
                ],
                'export_info': {
                    'export_date': datetime.utcnow().isoformat(),
                    'format': export_format,
                    'total_records': len(user_records)
                }
            }
            
            # Generate export file
            export_filename = f"user_{user_id}_data_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{export_format}"
            export_path = f"/tmp/{export_filename}"
            
            if export_format.lower() == 'json':
                with open(export_path, 'w') as f:
                    json.dump(export_data, f, indent=2)
            else:
                # Could implement CSV or other formats
                raise ValueError(f"Export format {export_format} not supported")
            
            logger.info(f"User data exported successfully: {export_path}")
            
            # Optionally, upload to secure storage and send download link
            # For now, just return the local path
            
            return {
                'status': 'success',
                'export_file': export_path,
                'export_size': os.path.getsize(export_path),
                'user_id': user_id,
                'total_records': len(user_records)
            }
            
    except Exception as e:
        logger.error(f"Failed to export user data: {str(e)}")
        raise
