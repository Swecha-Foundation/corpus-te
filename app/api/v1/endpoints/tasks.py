"""
API endpoints for managing Celery tasks.
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session

from app.core.auth import get_current_active_user
from app.core.celery_app import celery_app
from app.db.session import get_session
from app.models.user import User
from app.schemas.task import TaskResponse, TaskStatusResponse, TaskListResponse
from app.tasks.file_processing import process_audio_file, batch_process_files, upload_to_storage
from app.tasks.notifications import (
    send_email, send_processing_complete_notification, 
    send_bulk_notification, send_system_alert
)
from app.tasks.data_analysis import (
    analyze_audio_content, generate_corpus_statistics, batch_language_detection
)
from app.tasks.maintenance import cleanup_old_files, optimize_database, health_check
from app.tasks.reports import (
    generate_daily_report, generate_user_report, 
    generate_system_health_report, export_user_data
)

router = APIRouter()


@router.post("/process-audio/{record_id}", response_model=TaskResponse)
async def start_audio_processing(
    record_id: int,
    current_user: User = Depends(get_current_active_user)
) -> TaskResponse:
    """Start audio file processing task."""
    try:
        # You might want to verify the user owns this record
        task = process_audio_file.delay(record_id, "")  # file_path would come from database
        
        return TaskResponse(
            task_id=task.id,
            task_name="process_audio_file",
            status="PENDING",
            message=f"Audio processing started for record {record_id}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-process", response_model=TaskResponse)
async def start_batch_processing(
    record_ids: List[int],
    current_user: User = Depends(get_current_active_user)
) -> TaskResponse:
    """Start batch processing of multiple records."""
    try:
        task = batch_process_files.delay(record_ids)
        
        return TaskResponse(
            task_id=task.id,
            task_name="batch_process_files",
            status="PENDING",
            message=f"Batch processing started for {len(record_ids)} records"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-content/{record_id}", response_model=TaskResponse)
async def start_content_analysis(
    record_id: int,
    current_user: User = Depends(get_current_active_user)
) -> TaskResponse:
    """Start content analysis (speech recognition, language detection) for a record."""
    try:
        task = analyze_audio_content.delay(record_id)
        
        return TaskResponse(
            task_id=task.id,
            task_name="analyze_audio_content",
            status="PENDING",
            message=f"Content analysis started for record {record_id}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-statistics", response_model=TaskResponse)
async def generate_statistics(
    user_specific: bool = False,
    current_user: User = Depends(get_current_active_user)
) -> TaskResponse:
    """Generate corpus statistics."""
    try:
        user_id = current_user.id if user_specific else None
        task = generate_corpus_statistics.delay(user_id)
        
        return TaskResponse(
            task_id=task.id,
            task_name="generate_corpus_statistics",
            status="PENDING",
            message="Statistics generation started"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-language-detection", response_model=TaskResponse)
async def start_batch_language_detection(
    record_ids: List[int],
    current_user: User = Depends(get_current_active_user)
) -> TaskResponse:
    """Start batch language detection for multiple records."""
    try:
        task = batch_language_detection.delay(record_ids)
        
        return TaskResponse(
            task_id=task.id,
            task_name="batch_language_detection",
            status="PENDING",
            message=f"Batch language detection started for {len(record_ids)} records"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-notification", response_model=TaskResponse)
async def send_notification(
    recipients: List[str],
    subject: str,
    message: str,
    current_user: User = Depends(get_current_active_user)
) -> TaskResponse:
    """Send email notification (admin only)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        task = send_email.delay(recipients, subject, message)
        
        return TaskResponse(
            task_id=task.id,
            task_name="send_email",
            status="PENDING",
            message=f"Email notification queued for {len(recipients)} recipients"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/system-alert", response_model=TaskResponse)
async def send_system_alert_endpoint(
    alert_type: str,
    message: str,
    severity: str = "info",
    current_user: User = Depends(get_current_active_user)
) -> TaskResponse:
    """Send system alert (admin only)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        task = send_system_alert.delay(alert_type, message, severity)
        
        return TaskResponse(
            task_id=task.id,
            task_name="send_system_alert",
            status="PENDING",
            message="System alert queued"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
) -> TaskStatusResponse:
    """Get the status of a specific task."""
    try:
        task_result = celery_app.AsyncResult(task_id)
        
        response = TaskStatusResponse(
            task_id=task_id,
            status=task_result.status,
            result=task_result.result if task_result.ready() else None,
            traceback=task_result.traceback if task_result.failed() else None
        )
        
        # Add progress information if available
        if hasattr(task_result, 'info') and isinstance(task_result.info, dict):
            response.progress = task_result.info
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cancel/{task_id}")
async def cancel_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Cancel a running task."""
    try:
        celery_app.control.revoke(task_id, terminate=True)
        
        return {
            "message": f"Task {task_id} cancellation requested",
            "task_id": task_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active", response_model=TaskListResponse)
async def get_active_tasks(
    current_user: User = Depends(get_current_active_user)
) -> TaskListResponse:
    """Get list of currently active tasks (admin only)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Get active tasks from all workers
        active_tasks = celery_app.control.inspect().active()
        
        tasks = []
        if active_tasks:
            for worker, worker_tasks in active_tasks.items():
                for task in worker_tasks:
                    tasks.append({
                        'task_id': task['id'],
                        'task_name': task['name'],
                        'worker': worker,
                        'args': task.get('args', []),
                        'kwargs': task.get('kwargs', {}),
                        'time_start': task.get('time_start')
                    })
        
        return TaskListResponse(
            tasks=tasks,
            total_count=len(tasks)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scheduled", response_model=TaskListResponse)
async def get_scheduled_tasks(
    current_user: User = Depends(get_current_active_user)
) -> TaskListResponse:
    """Get list of scheduled tasks (admin only)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Get scheduled tasks
        scheduled_tasks = celery_app.control.inspect().scheduled()
        
        tasks = []
        if scheduled_tasks:
            for worker, worker_tasks in scheduled_tasks.items():
                for task in worker_tasks:
                    tasks.append({
                        'task_id': task['request']['id'],
                        'task_name': task['request']['task'],
                        'worker': worker,
                        'eta': task.get('eta'),
                        'args': task['request'].get('args', []),
                        'kwargs': task['request'].get('kwargs', {})
                    })
        
        return TaskListResponse(
            tasks=tasks,
            total_count=len(tasks)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Admin-only maintenance endpoints
@router.post("/maintenance/cleanup", response_model=TaskResponse)
async def start_cleanup(
    days_old: int = 30,
    current_user: User = Depends(get_current_active_user)
) -> TaskResponse:
    """Start file cleanup task (admin only)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        task = cleanup_old_files.delay(days_old)
        
        return TaskResponse(
            task_id=task.id,
            task_name="cleanup_old_files",
            status="PENDING",
            message=f"Cleanup started for files older than {days_old} days"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/maintenance/optimize-db", response_model=TaskResponse)
async def start_database_optimization(
    current_user: User = Depends(get_current_active_user)
) -> TaskResponse:
    """Start database optimization task (admin only)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        task = optimize_database.delay()
        
        return TaskResponse(
            task_id=task.id,
            task_name="optimize_database",
            status="PENDING",
            message="Database optimization started"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/maintenance/health-check", response_model=TaskResponse)
async def start_health_check(
    current_user: User = Depends(get_current_active_user)
) -> TaskResponse:
    """Start system health check (admin only)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        task = health_check.delay()
        
        return TaskResponse(
            task_id=task.id,
            task_name="health_check",
            status="PENDING",
            message="Health check started"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports/daily", response_model=TaskResponse)
async def generate_daily_report_endpoint(
    report_date: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
) -> TaskResponse:
    """Generate daily report (admin only)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        task = generate_daily_report.delay(report_date)
        
        return TaskResponse(
            task_id=task.id,
            task_name="generate_daily_report",
            status="PENDING",
            message="Daily report generation started"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports/user", response_model=TaskResponse)
async def generate_user_report_endpoint(
    target_user_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
) -> TaskResponse:
    """Generate user report."""
    # Users can generate their own reports, admins can generate for any user
    user_id = target_user_id if current_user.role == "admin" else current_user.id
    
    try:
        task = generate_user_report.delay(user_id, start_date, end_date)
        
        return TaskResponse(
            task_id=task.id,
            task_name="generate_user_report",
            status="PENDING",
            message=f"User report generation started for user {user_id}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export-data", response_model=TaskResponse)
async def export_user_data_endpoint(
    export_format: str = "json",
    current_user: User = Depends(get_current_active_user)
) -> TaskResponse:
    """Export user's data."""
    try:
        task = export_user_data.delay(current_user.id, export_format)
        
        return TaskResponse(
            task_id=task.id,
            task_name="export_user_data",
            status="PENDING",
            message="Data export started"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
