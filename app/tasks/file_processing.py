"""
File processing tasks for handling uploads, conversions, and analysis.
"""
import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

from celery import current_task
from sqlmodel import Session, select

from app.core.celery_app import celery_app
from app.db.session import engine
from app.models.record import Record
from app.utils.hetzner_storage import HetznerStorageClient

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.file_processing.process_audio_file")
def process_audio_file(self, record_id: int, file_path: str) -> Dict[str, Any]:
    """
    Process uploaded audio file - validate, extract metadata, generate waveform.
    
    Args:
        record_id: Database record ID
        file_path: Path to the uploaded file
        
    Returns:
        Dict with processing results
    """
    try:
        logger.info(f"Starting audio processing for record {record_id}")
        
        # Update task progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': 'Validating file...'}
        )
        
        with Session(engine) as session:
            # Get record from database
            record = session.get(Record, record_id)
            if not record:
                raise ValueError(f"Record {record_id} not found")
            
            # Validate file exists and is accessible
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            self.update_state(
                state='PROGRESS',
                meta={'current': 30, 'total': 100, 'status': 'Extracting metadata...'}
            )
            
            # Extract audio metadata (duration, format, bitrate, etc.)
            metadata = extract_audio_metadata(file_path)
            
            self.update_state(
                state='PROGRESS',
                meta={'current': 60, 'total': 100, 'status': 'Generating waveform...'}
            )
            
            # Generate waveform data for visualization
            waveform_data = generate_waveform(file_path)
            
            self.update_state(
                state='PROGRESS',
                meta={'current': 80, 'total': 100, 'status': 'Updating database...'}
            )
            
            # Update record with processing results
            record.audio_duration = metadata.get('duration')
            record.audio_bitrate = metadata.get('bitrate')
            record.audio_format = metadata.get('format')
            record.processing_status = 'completed'
            record.waveform_data = waveform_data
            
            session.add(record)
            session.commit()
            
            self.update_state(
                state='PROGRESS',
                meta={'current': 100, 'total': 100, 'status': 'Processing complete'}
            )
            
            logger.info(f"Audio processing completed for record {record_id}")
            
            return {
                'status': 'success',
                'record_id': record_id,
                'metadata': metadata,
                'waveform_generated': len(waveform_data) > 0 if waveform_data else False
            }
            
    except Exception as e:
        logger.error(f"Audio processing failed for record {record_id}: {str(e)}")
        
        # Update record status to failed
        try:
            with Session(engine) as session:
                record = session.get(Record, record_id)
                if record:
                    record.processing_status = 'failed'
                    record.processing_error = str(e)
                    session.add(record)
                    session.commit()
        except Exception as db_error:
            logger.error(f"Failed to update record status: {str(db_error)}")
        
        # Re-raise the exception to mark task as failed
        raise


@celery_app.task(bind=True, name="app.tasks.file_processing.upload_to_storage")
def upload_to_storage(self, file_path: str, object_name: str, bucket_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Upload file to Hetzner Object Storage.
    
    Args:
        file_path: Local file path to upload
        object_name: Name for the object in storage
        bucket_name: Optional bucket name (uses default if not provided)
        
    Returns:
        Dict with upload results
    """
    try:
        logger.info(f"Starting upload to storage: {object_name}")
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': 'Initializing upload...'}
        )
        
        # Initialize storage service
        storage_service = HetznerStorageClient()
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 30, 'total': 100, 'status': 'Uploading file...'}
        )
        
        # Upload file using upload_file_data method
        with open(file_path, 'rb') as file_data:
            file_size = os.path.getsize(file_path)
            result = storage_service.upload_file_data(
                file_data=file_data,
                object_key=object_name,
                file_size=file_size,
                content_type="application/octet-stream"
            )
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 90, 'total': 100, 'status': 'Finalizing...'}
        )
        
        # Clean up local file if upload successful
        if result.get('success') and os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up local file: {file_path}")
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 100, 'total': 100, 'status': 'Upload complete'}
        )
        
        logger.info(f"Upload completed successfully: {object_name}")
        return result
        
    except Exception as e:
        logger.error(f"Upload failed for {object_name}: {str(e)}")
        raise


@celery_app.task(name="app.tasks.file_processing.batch_process_files")
def batch_process_files(record_ids: list[int]) -> Dict[str, Any]:
    """
    Process multiple files in batch.
    
    Args:
        record_ids: List of record IDs to process
        
    Returns:
        Dict with batch processing results
    """
    try:
        logger.info(f"Starting batch processing for {len(record_ids)} records")
        
        results = {
            'processed': [],
            'failed': [],
            'total': len(record_ids)
        }
        
        for record_id in record_ids:
            try:
                # Process each record
                with Session(engine) as session:
                    record = session.get(Record, record_id)
                    if not record:
                        results['failed'].append({
                            'record_id': record_id,
                            'error': 'Record not found'
                        })
                        continue
                    
                    # Queue individual processing task
                    # Note: This assumes file_url contains the local path during processing
                    # In production, you'd need to download from storage first
                    file_path = record.file_url or ""
                    task = celery_app.send_task(
                        'app.tasks.file_processing.process_audio_file',
                        args=[record_id, file_path]
                    )
                    
                    results['processed'].append({
                        'record_id': record_id,
                        'task_id': task.id
                    })
                    
            except Exception as e:
                logger.error(f"Failed to queue processing for record {record_id}: {str(e)}")
                results['failed'].append({
                    'record_id': record_id,
                    'error': str(e)
                })
        
        logger.info(f"Batch processing queued: {len(results['processed'])} successful, {len(results['failed'])} failed")
        return results
        
    except Exception as e:
        logger.error(f"Batch processing failed: {str(e)}")
        raise


def extract_audio_metadata(file_path: str) -> Dict[str, Any]:
    """
    Extract metadata from audio file.
    
    This is a placeholder - implement with actual audio processing library
    like librosa, pydub, or ffmpeg-python.
    """
    # Placeholder implementation
    file_size = os.path.getsize(file_path)
    file_ext = Path(file_path).suffix.lower()
    
    return {
        'duration': None,  # Would extract actual duration
        'bitrate': None,   # Would extract actual bitrate
        'format': file_ext,
        'file_size': file_size,
        'channels': None,  # Would extract channel count
        'sample_rate': None  # Would extract sample rate
    }


def generate_waveform(file_path: str) -> list[float]:
    """
    Generate waveform data for visualization.
    
    This is a placeholder - implement with actual audio processing.
    """
    # Placeholder implementation
    # In real implementation, you'd use librosa or similar to generate waveform peaks
    return []
