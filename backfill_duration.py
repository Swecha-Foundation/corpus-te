#!/usr/bin/env python3
"""
Backfill Duration Script for Audio and Video Records

This script:
1. Fetches all audio and video records that don't have duration_seconds set
2. Downloads each file from Hetzner Object Storage to a temporary location
3. Computes the duration using moviepy
4. Updates the database with the calculated duration
5. Cleans up temporary files
6. Provides progress reporting and error handling

Usage:
    python backfill_duration.py [--dry-run] [--limit N] [--media-type audio|video|both]
"""

import os
import sys
import tempfile
import logging
import argparse
from typing import Optional, List, Dict, Any
from pathlib import Path
import time
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from sqlmodel import Session, select
from app.db.session import engine
from app.models.record import Record, MediaType
from app.utils.hetzner_storage import get_storage_client
from app.utils.media_duration import get_media_duration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backfill_duration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DurationBackfiller:
    """Handles backfilling duration for audio and video records."""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.storage_client = get_storage_client()
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
    
    def get_records_without_duration(self, media_type: Optional[str] = None, limit: Optional[int] = None) -> List[Record]:
        """
        Get records that don't have duration_seconds set.
        
        Args:
            media_type: Filter by media type ('audio', 'video', or None for both)
            limit: Maximum number of records to process
            
        Returns:
            List of records without duration
        """
        with Session(engine) as session:
            query = select(Record).where(
                Record.duration_seconds.is_(None),
                Record.file_url.is_not(None),
                Record.status == "uploaded"
            )
            
            # Filter by media type if specified
            if media_type:
                if media_type.lower() == 'audio':
                    query = query.where(Record.media_type == MediaType.audio)
                elif media_type.lower() == 'video':
                    query = query.where(Record.media_type == MediaType.video)
                else:
                    raise ValueError(f"Invalid media type: {media_type}")
            else:
                # Filter for audio and video only
                query = query.where(Record.media_type.in_([MediaType.audio, MediaType.video]))
            
            # Apply limit if specified
            if limit:
                query = query.limit(limit)
            
            records = session.exec(query).all()
            logger.info(f"Found {len(records)} records without duration")
            return records
    
    def download_file_to_temp(self, record: Record) -> Optional[str]:
        """
        Download a file from object storage to a temporary location.
        
        Args:
            record: Record containing file information
            
        Returns:
            Path to temporary file, or None if download failed
        """
        if not record.file_url:
            logger.warning(f"Record {record.uid} has no file_url")
            return None
        
        try:
            # Extract object key from file_url
            # Assuming file_url format: https://endpoint/bucket/object_key
            url_parts = record.file_url.split('/')
            if len(url_parts) < 2:
                logger.error(f"Invalid file_url format for record {record.uid}: {record.file_url}")
                return None
            
            object_key = '/'.join(url_parts[-2:])  # bucket/object_key
            if not object_key:
                logger.error(f"Could not extract object key from {record.file_url}")
                return None
            
            # Create temporary file
            file_extension = Path(record.file_name or object_key).suffix if record.file_name else ''
            if not file_extension:
                # Try to determine extension from object key
                file_extension = Path(object_key).suffix
            
            # Create temp file with proper extension
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=file_extension,
                prefix=f"duration_backfill_{record.uid}_"
            )
            temp_path = temp_file.name
            temp_file.close()
            
            logger.info(f"Downloading {object_key} to {temp_path}")
            
            # Download file from object storage
            self.storage_client.client.fget_object(
                bucket_name=self.storage_client.bucket_name,
                object_name=object_key,
                file_path=temp_path
            )
            
            # Verify file was downloaded and has content
            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                logger.info(f"Successfully downloaded {object_key} ({os.path.getsize(temp_path)} bytes)")
                return temp_path
            else:
                logger.error(f"Downloaded file {temp_path} is empty or doesn't exist")
                return None
                
        except Exception as e:
            logger.error(f"Failed to download file for record {record.uid}: {e}")
            return None
    
    def calculate_duration(self, file_path: str, media_type: MediaType) -> Optional[int]:
        """
        Calculate duration for a media file.
        
        Args:
            file_path: Path to the media file
            media_type: Type of media (audio or video)
            
        Returns:
            Duration in seconds, or None if calculation failed
        """
        try:
            start_time = time.time()
            duration = get_media_duration(file_path, media_type.value)
            calculation_time = time.time() - start_time
            
            if duration is not None:
                logger.info(f"Calculated duration: {duration}s (took {calculation_time:.2f}s)")
            else:
                logger.warning(f"Could not calculate duration (took {calculation_time:.2f}s)")
            
            return duration
            
        except Exception as e:
            logger.error(f"Error calculating duration for {file_path}: {e}")
            return None
    
    def update_record_duration(self, record: Record, duration: int) -> bool:
        """
        Update a record with the calculated duration.
        
        Args:
            record: Record to update
            duration: Duration in seconds
            
        Returns:
            True if update was successful
        """
        try:
            with Session(engine) as session:
                # Get fresh record from database
                db_record = session.get(Record, record.uid)
                if not db_record:
                    logger.error(f"Record {record.uid} not found in database")
                    return False
                
                if self.dry_run:
                    logger.info(f"[DRY RUN] Would update record {record.uid} with duration {duration}s")
                    return True
                
                # Update duration and timestamp
                db_record.duration_seconds = duration
                db_record.updated_at = datetime.utcnow()
                
                session.add(db_record)
                session.commit()
                
                logger.info(f"Updated record {record.uid} with duration {duration}s")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update record {record.uid}: {e}")
            return False
    
    def cleanup_temp_file(self, file_path: str) -> None:
        """
        Clean up temporary file.
        
        Args:
            file_path: Path to temporary file to delete
        """
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                logger.debug(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up temporary file {file_path}: {e}")
    
    def process_record(self, record: Record) -> bool:
        """
        Process a single record: download, calculate duration, update database.
        
        Args:
            record: Record to process
            
        Returns:
            True if processing was successful
        """
        temp_file_path = None
        
        try:
            logger.info(f"Processing record {record.uid} ({record.media_type.value}): {record.title}")
            
            # Download file to temporary location
            temp_file_path = self.download_file_to_temp(record)
            if not temp_file_path:
                self.stats['failed'] += 1
                self.stats['errors'].append(f"Record {record.uid}: Failed to download file")
                return False
            
            # Calculate duration
            duration = self.calculate_duration(temp_file_path, record.media_type)
            if duration is None:
                self.stats['failed'] += 1
                self.stats['errors'].append(f"Record {record.uid}: Failed to calculate duration")
                return False
            
            # Update database
            if self.update_record_duration(record, duration):
                self.stats['successful'] += 1
                return True
            else:
                self.stats['failed'] += 1
                self.stats['errors'].append(f"Record {record.uid}: Failed to update database")
                return False
                
        except Exception as e:
            logger.error(f"Unexpected error processing record {record.uid}: {e}")
            self.stats['failed'] += 1
            self.stats['errors'].append(f"Record {record.uid}: {str(e)}")
            return False
            
        finally:
            # Always clean up temporary file
            if temp_file_path:
                self.cleanup_temp_file(temp_file_path)
    
    def run_backfill(self, media_type: Optional[str] = None, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Run the complete backfill process.
        
        Args:
            media_type: Filter by media type ('audio', 'video', or None for both)
            limit: Maximum number of records to process
            
        Returns:
            Statistics about the backfill process
        """
        logger.info(f"Starting duration backfill process")
        logger.info(f"Dry run: {self.dry_run}")
        logger.info(f"Media type filter: {media_type or 'both'}")
        logger.info(f"Limit: {limit or 'no limit'}")
        
        start_time = time.time()
        
        # Get records to process
        records = self.get_records_without_duration(media_type, limit)
        
        if not records:
            logger.info("No records found that need duration backfill")
            return self.stats
        
        logger.info(f"Processing {len(records)} records...")
        
        # Process each record
        for i, record in enumerate(records, 1):
            logger.info(f"Progress: {i}/{len(records)} ({i/len(records)*100:.1f}%)")
            
            self.stats['total_processed'] += 1
            
            if self.process_record(record):
                logger.info(f"✓ Successfully processed record {record.uid}")
            else:
                logger.error(f"✗ Failed to process record {record.uid}")
        
        # Calculate final statistics
        total_time = time.time() - start_time
        self.stats['total_time_seconds'] = total_time
        self.stats['average_time_per_record'] = total_time / len(records) if records else 0
        
        # Log final results
        logger.info("=" * 60)
        logger.info("BACKFILL COMPLETED")
        logger.info("=" * 60)
        logger.info(f"Total processed: {self.stats['total_processed']}")
        logger.info(f"Successful: {self.stats['successful']}")
        logger.info(f"Failed: {self.stats['failed']}")
        logger.info(f"Skipped: {self.stats['skipped']}")
        logger.info(f"Total time: {total_time:.2f} seconds")
        logger.info(f"Average time per record: {self.stats['average_time_per_record']:.2f} seconds")
        
        if self.stats['errors']:
            logger.info("Errors encountered:")
            for error in self.stats['errors']:
                logger.error(f"  - {error}")
        
        return self.stats


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Backfill duration for audio and video records",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all audio and video records without duration
  python backfill_duration.py
  
  # Dry run - show what would be processed without making changes
  python backfill_duration.py --dry-run
  
  # Process only audio files, limit to 10 records
  python backfill_duration.py --media-type audio --limit 10
  
  # Process only video files
  python backfill_duration.py --media-type video
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be processed without making database changes'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        help='Maximum number of records to process'
    )
    
    parser.add_argument(
        '--media-type',
        choices=['audio', 'video', 'both'],
        default='both',
        help='Filter by media type (default: both)'
    )
    
    args = parser.parse_args()
    
    # Convert 'both' to None for internal processing
    media_type = None if args.media_type == 'both' else args.media_type
    
    try:
        # Initialize backfiller
        backfiller = DurationBackfiller(dry_run=args.dry_run)
        
        # Run backfill
        stats = backfiller.run_backfill(
            media_type=media_type,
            limit=args.limit
        )
        
        # Exit with error code if there were failures
        if stats['failed'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        logger.info("Backfill interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Backfill failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 