#!/usr/bin/env python3
"""
Example usage of the Record File Generator utility.
This demonstrates how to create files with names matching record UIDs.
"""

import asyncio
import sys
from pathlib import Path
from uuid import UUID

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.utils.record_file_generator import (
    RecordFileGenerator,
    create_file_for_record,
    auto_generate_files_for_pending_records
)
from app.models.record import Record, MediaType
from app.db.session import engine
from sqlmodel import Session, select


async def example_single_record_file():
    """Example: Generate a file for a single record."""
    print("📝 Example 1: Generate File for Single Record")
    print("-" * 50)
    
    # Get a sample record from the database
    try:
        with Session(engine) as session:
            stmt = select(Record).limit(1)
            record = session.exec(stmt).first()
            
            if not record:
                print("❌ No records found in database. Please create some records first.")
                return None
            
            print(f"📋 Selected record: {record.uid}")
            print(f"   Title: {record.title}")
            print(f"   Media Type: {record.media_type}")
            print(f"   Current File URL: {record.file_url or 'None'}")
            
            # Generate and upload file
            result = await create_file_for_record(
                record_uid=record.uid,
                file_size_kb=25,  # Generate a 25KB file
                update_record=True
            )
            
            if result.get("success"):
                upload_info = result["upload_result"]
                print("\n✅ File generated successfully!")
                print(f"   Generated filename: {upload_info['original_filename']}")
                print(f"   Storage object key: {upload_info['object_key']}")
                print(f"   File size: {upload_info['file_size']} bytes")
                print(f"   Public URL: {upload_info['object_url']}")
                print(f"   Record updated: {result['record_updated']}")
                
                return record.uid
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                return None
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


async def example_custom_file_generation():
    """Example: Generate files with custom specifications."""
    print("\n🎨 Example 2: Custom File Generation")
    print("-" * 50)
    
    generator = RecordFileGenerator()
    
    # Create a custom UUID for demonstration
    custom_uid = UUID('12345678-1234-5678-9012-123456789012')
    
    try:
        # Generate different types of files
        media_types = [MediaType.text, MediaType.audio, MediaType.video, MediaType.image]
        
        for media_type in media_types:
            print(f"\n🎯 Generating {media_type.value} file...")
            
            # Generate sample content
            content = generator.generate_sample_content(media_type, file_size_kb=5)
            filename = generator.generate_filename_from_uid(custom_uid, media_type)
            
            print(f"   Filename: {filename}")
            print(f"   Content size: {len(content)} bytes")
            print(f"   Content preview: {str(content[:50])}...")
            
    except Exception as e:
        print(f"❌ Error in custom generation: {e}")


async def example_bulk_processing():
    """Example: Process multiple records at once."""
    print("\n📦 Example 3: Bulk File Processing")
    print("-" * 50)
    
    try:
        # Get multiple records without files
        generator = RecordFileGenerator()
        record_uids = generator.get_records_without_files(limit=5)
        
        if not record_uids:
            print("✅ All records already have files!")
            return
        
        print(f"📋 Found {len(record_uids)} records without files:")
        for i, uid in enumerate(record_uids, 1):
            print(f"   {i}. {uid}")
        
        # Process them in bulk
        print(f"\n⚡ Processing {len(record_uids)} records...")
        results = await generator.bulk_process_records(
            record_uids=record_uids,
            file_size_kb=20,
            update_records=True
        )
        
        # Show results
        successful = 0
        failed = 0
        
        print("\n📊 Results:")
        for result in results:
            if result.get("success"):
                successful += 1
                upload_info = result["upload_result"]
                print(f"   ✅ {result['record_uid'][:8]}... -> {upload_info['object_key']}")
            else:
                failed += 1
                print(f"   ❌ {result['record_uid'][:8]}... -> {result.get('error', 'Unknown')}")
        
        print(f"\n📈 Summary: {successful} successful, {failed} failed")
        
    except Exception as e:
        print(f"❌ Error in bulk processing: {e}")


async def example_auto_generation():
    """Example: Automatic file generation for pending records."""
    print("\n🤖 Example 4: Automatic File Generation")
    print("-" * 50)
    
    try:
        result = await auto_generate_files_for_pending_records(
            limit=10,  # Process up to 10 records
            file_size_kb=30  # Generate 30KB files
        )
        
        print(f"📊 {result['message']}")
        print(f"   Successful: {result.get('successful', 0)}")
        print(f"   Failed: {result.get('failed', 0)}")
        
        if result.get('results'):
            print("\n📋 Sample results:")
            for res in result['results'][:3]:  # Show first 3
                if res.get('success'):
                    upload_info = res["upload_result"]
                    filename = upload_info['original_filename']
                    print(f"   ✅ Generated: {filename}")
                else:
                    print(f"   ❌ Failed: {res.get('error', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Error in auto generation: {e}")


async def example_filename_patterns():
    """Example: Show different filename patterns."""
    print("\n📁 Example 5: Filename Patterns")
    print("-" * 50)
    
    generator = RecordFileGenerator()
    
    # Sample UUIDs and media types
    sample_uids = [
        UUID('12345678-1234-5678-9012-123456789abc'),
        UUID('87654321-4321-8765-2109-cba987654321'),
        UUID('abcdef12-3456-7890-abcd-ef1234567890')
    ]
    
    media_types = [MediaType.text, MediaType.audio, MediaType.video, MediaType.image]
    
    print("📋 Generated filename patterns:")
    print("   Format: {record_uid}{extension}")
    print()
    
    for i, uid in enumerate(sample_uids, 1):
        print(f"   Record {i}: {uid}")
        for media_type in media_types:
            filename = generator.generate_filename_from_uid(uid, media_type)
            print(f"     {media_type.value:5s} -> {filename}")
        print()


async def main():
    """Run all examples."""
    print("🎯 Record File Generator - Examples with UID-based Filenames")
    print("=" * 70)
    
    # Example 1: Single record
    generated_uid = await example_single_record_file()
    
    # Example 2: Custom generation
    await example_custom_file_generation()
    
    # Example 3: Bulk processing  
    await example_bulk_processing()
    
    # Example 4: Auto generation
    await example_auto_generation()
    
    # Example 5: Filename patterns
    await example_filename_patterns()
    
    print("\n✨ All examples completed!")
    print("\n💡 Tips:")
    print("   • Files are named using the record's UID as the base filename")
    print("   • Files are organized by media type in storage (audio/, video/, etc.)")
    print("   • Each file includes metadata linking it to the record")
    print("   • Records are automatically updated with file information")
    print("\n🚀 Use the command-line script for production:")
    print("   ./generate_record_files.py auto --limit 50 --size 20")


if __name__ == "__main__":
    asyncio.run(main())
