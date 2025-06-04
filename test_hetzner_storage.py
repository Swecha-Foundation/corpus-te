#!/usr/bin/env python3
"""
Test script for Hetzner Object Storage utility.
This script tests the basic functionality of the storage client.
"""

import os
import sys
import asyncio
import tempfile
from io import BytesIO
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.utils.hetzner_storage import (
    HetznerStorageClient, 
    upload_file_to_hetzner, 
    delete_file_from_hetzner,
    get_file_url
)
from app.core.config import settings
from fastapi import UploadFile


async def test_storage_client():
    """Test the Hetzner storage client functionality."""
    print("🧪 Testing Hetzner Object Storage Client")
    print("=" * 50)
    
    # Check if credentials are configured
    print("📋 Checking configuration...")
    if not all([
        settings.MINIO_ENDPOINT,
        settings.MINIO_ACCESS_KEY,
        settings.MINIO_SECRET_KEY
    ]):
        print("❌ Missing Hetzner storage credentials!")
        print("Please set the following environment variables:")
        print("- HZ_OBJ_ENDPOINT")
        print("- HZ_OBJ_ACCESS_KEY") 
        print("- HZ_OBJ_SECRET_KEY")
        print("- HZ_OBJ_BUCKET_NAME (optional, defaults to 'corpus-data')")
        return False
    
    print(f"✅ Endpoint: {settings.MINIO_ENDPOINT}")
    print(f"✅ Bucket: {settings.MINIO_BUCKET_NAME}")
    print(f"✅ SSL: {settings.MINIO_USE_SSL}")
    
    try:
        # Initialize client
        print("\n🔧 Initializing storage client...")
        client = HetznerStorageClient()
        print("✅ Client initialized successfully")
        
        # Create a test file
        print("\n📄 Creating test file...")
        test_content = b"Hello, Hetzner Object Storage! This is a test file."
        test_filename = "test_file.txt"
        
        # Create a mock UploadFile
        test_file = UploadFile(
            filename=test_filename,
            file=BytesIO(test_content),
            size=len(test_content),
            headers={"content-type": "text/plain"}
        )
        
        # Test upload
        print("\n⬆️ Testing file upload...")
        upload_result = await upload_file_to_hetzner(
            file=test_file,
            prefix="test/",
            metadata={
                "test": "true",
                "purpose": "unit_test"
            }
        )
        
        print("✅ Upload successful!")
        print(f"   Object Key: {upload_result['object_key']}")
        print(f"   File Size: {upload_result['file_size']} bytes")
        print(f"   URL: {upload_result['object_url']}")
        
        object_key = upload_result['object_key']
        
        # Test object existence
        print("\n🔍 Testing object existence...")
        exists = client.object_exists(object_key)
        print(f"✅ Object exists: {exists}")
        
        # Test getting object info
        print("\n📊 Getting object information...")
        obj_info = client.get_object_info(object_key)
        print(f"✅ Object size: {obj_info['size']} bytes")
        print(f"   Content type: {obj_info['content_type']}")
        print(f"   Last modified: {obj_info['last_modified']}")
        
        # Test presigned URL generation
        print("\n🔗 Testing presigned URL generation...")
        presigned_url = client.get_presigned_url(object_key)
        print(f"✅ Generated presigned URL (length: {len(presigned_url)})")
        
        # Test listing objects
        print("\n📂 Testing object listing...")
        objects = client.list_objects(prefix="test/", max_keys=10)
        print(f"✅ Found {len(objects)} objects with 'test/' prefix")
        
        # Test file URL helper
        print("\n🌐 Testing URL helper functions...")
        public_url = get_file_url(object_key)
        presigned_url_helper = get_file_url(object_key, presigned=True, expires_hours=2)
        print(f"✅ Public URL: {public_url[:50]}...")
        print(f"✅ Presigned URL: {presigned_url_helper[:50]}...")
        
        # Test deletion
        print("\n🗑️ Testing file deletion...")
        delete_success = delete_file_from_hetzner(object_key)
        print(f"✅ Deletion successful: {delete_success}")
        
        # Verify deletion
        print("\n✔️ Verifying deletion...")
        exists_after_delete = client.object_exists(object_key)
        print(f"✅ Object exists after deletion: {exists_after_delete}")
        
        if not exists_after_delete:
            print("\n🎉 All tests passed successfully!")
            return True
        else:
            print("\n❌ Test failed: Object still exists after deletion")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False


def test_configuration():
    """Test configuration loading."""
    print("⚙️ Testing configuration...")
    print(f"Endpoint: {settings.MINIO_ENDPOINT or 'NOT SET'}")
    print(f"Access Key: {'***' + (settings.MINIO_ACCESS_KEY[-4:] if settings.MINIO_ACCESS_KEY else 'NOT SET')}")
    print(f"Secret Key: {'***' + (settings.MINIO_SECRET_KEY[-4:] if settings.MINIO_SECRET_KEY else 'NOT SET')}")
    print(f"Bucket: {settings.MINIO_BUCKET_NAME}")
    print(f"SSL: {settings.MINIO_USE_SSL}")
    print(f"Max file size: {settings.MAX_FILE_SIZE:,} bytes")


async def test_large_file_handling():
    """Test handling of large files (simulated)."""
    print("\n📏 Testing large file validation...")
    
    try:
        # Create a mock large file that exceeds the limit
        large_content = b"x" * (settings.MAX_FILE_SIZE + 1)
        large_file = UploadFile(
            filename="large_file.bin",
            file=BytesIO(large_content),
            size=len(large_content)
        )
        
        # This should raise an exception
        await upload_file_to_hetzner(large_file, prefix="test/")
        print("❌ Large file upload should have failed!")
        return False
        
    except Exception as e:
        if "exceeds maximum allowed size" in str(e):
            print("✅ Large file validation working correctly")
            return True
        else:
            print(f"❌ Unexpected error: {e}")
            return False


async def main():
    """Main test function."""
    print("🚀 Hetzner Object Storage Test Suite")
    print("=" * 60)
    
    # Test configuration
    test_configuration()
    
    # Test basic functionality
    basic_test_passed = await test_storage_client()
    
    # Test large file handling
    large_file_test_passed = await test_large_file_handling()
    
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    print(f"✅ Basic functionality: {'PASSED' if basic_test_passed else 'FAILED'}")
    print(f"✅ Large file validation: {'PASSED' if large_file_test_passed else 'FAILED'}")
    
    overall_success = basic_test_passed and large_file_test_passed
    print(f"\n🎯 Overall result: {'ALL TESTS PASSED' if overall_success else 'SOME TESTS FAILED'}")
    
    return 0 if overall_success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
