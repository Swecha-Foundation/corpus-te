"""
Pydantic schemas for task-related API responses.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime


class TaskResponse(BaseModel):
    """Response schema for task creation."""
    task_id: str
    task_name: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    """Response schema for task status."""
    task_id: str
    status: str
    result: Optional[Any] = None
    traceback: Optional[str] = None
    progress: Optional[Dict[str, Any]] = None


class TaskInfo(BaseModel):
    """Schema for task information."""
    task_id: str
    task_name: str
    worker: Optional[str] = None
    args: List[Any] = []
    kwargs: Dict[str, Any] = {}
    time_start: Optional[str] = None
    eta: Optional[str] = None


class TaskListResponse(BaseModel):
    """Response schema for task lists."""
    tasks: List[TaskInfo]
    total_count: int


class BatchProcessRequest(BaseModel):
    """Request schema for batch processing."""
    record_ids: List[int]


class NotificationRequest(BaseModel):
    """Request schema for sending notifications."""
    recipients: List[str]
    subject: str
    message: str
    html_body: Optional[str] = None


class SystemAlertRequest(BaseModel):
    """Request schema for system alerts."""
    alert_type: str
    message: str
    severity: str = "info"


class CleanupRequest(BaseModel):
    """Request schema for cleanup tasks."""
    days_old: int = 30


class ReportRequest(BaseModel):
    """Request schema for report generation."""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    report_type: str = "user"


class ExportRequest(BaseModel):
    """Request schema for data export."""
    format: str = "json"
    include_files: bool = False
