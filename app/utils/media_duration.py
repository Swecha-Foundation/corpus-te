"""
Utility functions for computing media file durations using moviepy.
"""

from typing import Optional

try:
    from moviepy import VideoFileClip, AudioFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False


def get_media_duration(file_path: str, file_type: str) -> Optional[int]:
    """
    Compute the duration of an audio or video file using moviepy.
    
    Args:
        file_path: Path to the media file (string)
        file_type: File type ('audio' or 'video')
    
    Returns:
        Duration in seconds as int, or None if duration cannot be computed
        
    Raises:
        ImportError: If moviepy is not available
        ValueError: If file type is not supported
    """
    if not MOVIEPY_AVAILABLE:
        raise ImportError("moviepy is required for media duration computation. "
                         "Install with: pip install moviepy")
    
    try:
        if file_type.lower() == 'video':
            with VideoFileClip(file_path) as clip:
                return int(clip.duration)
        elif file_type.lower() == 'audio':
            with AudioFileClip(file_path) as clip:
                return int(clip.duration)
        else:
            raise ValueError(f"Unsupported file type: {file_type}. "
                           f"Supported types: 'audio', 'video'")
    
    except Exception as e:
        # Log the error but don't raise it, return None instead
        print(f"Error computing duration for {file_path}: {str(e)}")
        return None





 