#!/usr/bin/env python3
"""
Example usage of the Hetzner Object Storage utility.
This script demonstrates how to use the storage client in different scenarios.
"""

import asyncio
import sys
from pathlib import Path
from io import BytesIO

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.utils.hetzner_storage import (
    HetznerStorageClient,
    upload_file_to_hetzner,
    delete_file_from_hetzner,
    get_file_url
)
from fastapi import UploadFile


async def example_basic_usage():
    """Example: Basic file upload and management."""
    print("📝 Example 1: Basic File Upload")
    print("-" * 40)
    
    # Create some sample content
    content = b"This is a sample text file for demonstration."
    
    # Create a mock UploadFile (in real FastAPI app, this comes from the request)
    upload_file = UploadFile(
        filename="sample.txt",
        file=BytesIO(content),
        size=len(content),
        headers={"content-type": "text/plain"}
    )
    
    try:
        # Upload the file
        result = await upload_file_to_hetzner(
            file=upload_file,
            prefix="examples/",
            metadata={
                "uploaded_by": "example_script",
                "category": "documentation"
            }
        )
        
        print(f"✅ File uploaded successfully!")
        print(f"   Object Key: {result['object_key']}")
        print(f"   Public URL: {result['object_url']}")
        print(f"   File Size: {result['file_size']} bytes")
        
        return result['object_key']
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return None


async def example_file_management(object_key: str):
    """Example: File management operations."""
    print(f"\n🔧 Example 2: File Management")
    print("-" * 40)
    
    try:
        # Initialize client for direct operations
        client = HetznerStorageClient()
        
        # Check if file exists
        exists = client.object_exists(object_key)
        print(f"📁 File exists: {exists}")
        
        if exists:
            # Get file information
            info = client.get_object_info(object_key)
            print(f"📊 File info:")
            print(f"   Size: {info['size']} bytes")
            print(f"   Content Type: {info['content_type']}")
            print(f"   Last Modified: {info['last_modified']}")
            
            # Generate different types of URLs
            public_url = get_file_url(object_key)
            presigned_url = get_file_url(object_key, presigned=True, expires_hours=1)
            
            print(f"🔗 URLs:")
            print(f"   Public: {public_url}")
            print(f"   Presigned (1h): {presigned_url[:50]}...")
        
    except Exception as e:
        print(f"❌ File management failed: {e}")


async def example_media_organization():
    """Example: Organizing files by media type."""
    print(f"\n📱 Example 3: Media Type Organization")
    print("-" * 40)
    
    # Sample files for different media types
    media_files = [
        {
            "content": b"Sample audio file content",
            "filename": "sample.mp3",
            "media_type": "audio",
            "content_type": "audio/mpeg"
        },
        {
            "content": b"Sample video file content", 
            "filename": "sample.mp4",
            "media_type": "video",
            "content_type": "video/mp4"
        },
        {
            "content": b"Sample image file content",
            "filename": "sample.jpg", 
            "media_type": "image",
            "content_type": "image/jpeg"
        }
    ]
    
    uploaded_keys = []
    
    for media in media_files:
        try:
            upload_file = UploadFile(
                filename=media["filename"],
                file=BytesIO(media["content"]),
                size=len(media["content"]),
                headers={"content-type": media["content_type"]}
            )
            
            # Upload with media type prefix
            result = await upload_file_to_hetzner(
                file=upload_file,
                prefix=f"{media['media_type']}/",
                metadata={
                    "media_type": media["media_type"],
                    "example": "media_organization"
                }
            )
            
            uploaded_keys.append(result['object_key'])
            print(f"✅ {media['media_type'].title()} uploaded: {result['object_key']}")
            
        except Exception as e:
            print(f"❌ Failed to upload {media['filename']}: {e}")
    
    return uploaded_keys


async def example_bulk_operations():
    """Example: Bulk file operations."""
    print(f"\n📦 Example 4: Bulk Operations")
    print("-" * 40)
    
    try:
        client = HetznerStorageClient()
        
        # List all files with 'examples/' prefix
        objects = client.list_objects(prefix="examples/", max_keys=20)
        print(f"📂 Found {len(objects)} files in examples/ folder:")
        
        for obj in objects:
            print(f"   - {obj['object_key']} ({obj['size']} bytes)")
        
        # List audio files
        audio_objects = client.list_objects(prefix="audio/", max_keys=10)
        print(f"🎵 Found {len(audio_objects)} audio files:")
        
        for obj in audio_objects:
            print(f"   - {obj['object_key']}")
            
    except Exception as e:
        print(f"❌ Bulk operations failed: {e}")


async def cleanup_examples(object_keys: list):
    """Clean up example files."""
    print(f"\n🧹 Cleanup: Removing Example Files")
    print("-" * 40)
    
    for key in object_keys:
        try:
            success = delete_file_from_hetzner(key)
            if success:
                print(f"✅ Deleted: {key}")
            else:
                print(f"❌ Failed to delete: {key}")
        except Exception as e:
            print(f"❌ Error deleting {key}: {e}")


async def main():
    """Run all examples."""
    print("🎯 Hetzner Object Storage Usage Examples")
    print("=" * 60)
    
    all_keys = []
    
    # Basic upload
    key1 = await example_basic_usage()
    if key1:
        all_keys.append(key1)
        
        # File management
        await example_file_management(key1)
    
    # Media organization
    media_keys = await example_media_organization()
    all_keys.extend(media_keys)
    
    # Bulk operations
    await example_bulk_operations()
    
    # Ask user if they want to clean up
    print(f"\n❓ Clean up example files? ({len(all_keys)} files)")
    response = input("Enter 'y' to delete example files: ").lower().strip()
    
    if response == 'y':
        await cleanup_examples(all_keys)
    else:
        print("📝 Example files left in storage:")
        for key in all_keys:
            print(f"   - {key}")
    
    print(f"\n✨ Examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
