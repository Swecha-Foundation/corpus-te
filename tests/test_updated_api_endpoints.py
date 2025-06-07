"""
Test script for updated Records API endpoints with UID-based file generation
"""
import requests
import json
import tempfile
import os

API_BASE = "http://localhost:8000/api/v1"

# Test user credentials for authentication
TEST_USER = {
    "phone": "9999999999",
    "password": "testpass123",
    "name": "Test User",
    "email": "test@example.com"
}

def get_auth_token():
    """Get authentication token for API requests"""
    # Try to login first
    login_response = requests.post(f"{API_BASE}/auth/login", json={
        "phone": TEST_USER["phone"],
        "password": TEST_USER["password"]
    })
    
    if login_response.status_code == 200:
        return login_response.json()["access_token"]
    
    # If login fails, try to register the user first
    register_response = requests.post(f"{API_BASE}/users/", json={
        "phone": TEST_USER["phone"],
        "password": TEST_USER["password"],
        "name": TEST_USER["name"],
        "email": TEST_USER["email"],
        "role_ids": [1]  # Assuming role ID 1 exists (admin or user)
    })
    
    if register_response.status_code in [200, 201]:
        # Now try to login
        login_response = requests.post(f"{API_BASE}/auth/login", json={
            "phone": TEST_USER["phone"],
            "password": TEST_USER["password"]
        })
        
        if login_response.status_code == 200:
            return login_response.json()["access_token"]
    
    return None

def get_auth_headers():
    """Get authentication headers for API requests"""
    token = get_auth_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

def test_upload_endpoint_with_uid_filename():
    """Test the /upload endpoint with use_uid_filename=True"""
    print("=" * 60)
    print("Testing /upload endpoint with UID-based filename")
    print("=" * 60)
    
    headers = get_auth_headers()
    if not headers:
        print("❌ Could not authenticate - skipping test")
        return None
    
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
        temp_file.write("This is a test file for UID-based upload testing.\nGenerated automatically for API testing.")
        temp_file_path = temp_file.name
    
    try:
        # Use actual UUIDs from the database
        record_data = {
            "title": "Test Upload with UID Filename",
            "description": "Testing the new UID-based filename feature",
            "media_type": "text",
            "category_id": "c36fee46-3ee5-40f7-bf7d-90cf3d459808",  # stories category
            "user_id": "5cb9390e-f30d-420e-ad04-27c65afd25f3",     # test user
            "location": "POINT(78.4867 17.3850)"  # Hyderabad coordinates
        }
        
        # Prepare the multipart form data
        with open(temp_file_path, 'rb') as f:
            files = {
                'file': ('test_file.txt', f, 'text/plain')
            }
            
            data = {
                **record_data,
                'use_uid_filename': 'true'  # Enable UID-based filename
            }
            
            response = requests.post(f"{API_BASE}/records/upload", files=files, data=data, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 201:  # Fixed: 201 is success for upload
            record = response.json()
            print("✅ Upload successful!")
            print(f"Record UID: {record['uid']}")
            print(f"File URL: {record['file_url']}")
            print(f"Status: {record['status']}")
            
            # Verify the filename matches the UID pattern
            if record['file_url'] and record['uid'] in record['file_url']:
                print("✅ Filename correctly uses record UID!")
            else:
                print("❌ Filename doesn't match UID pattern")
                
            return record
        else:
            print(f"❌ Upload failed: {response.text}")
            return None
            
    finally:
        # Clean up temp file
        os.unlink(temp_file_path)

def test_create_endpoint_with_file_generation():
    """Test the / endpoint (POST) with generate_file=True"""
    print("\n" + "=" * 60)
    print("Testing /records/ (POST) endpoint with file generation")
    print("=" * 60)
    
    headers = get_auth_headers()
    if not headers:
        print("❌ Could not authenticate - skipping test")
        return None
    
    # Test data for the record - use actual UUIDs
    record_data = {
        "title": "Test Create with Generated File",
        "description": "Testing the new file generation feature",
        "media_type": "audio",
        "category_id": "62f73989-81e5-4ba8-ad3c-7dd39d403061",  # songs category
        "user_id": "5cb9390e-f30d-420e-ad04-27c65afd25f3",      # test user
        "location": {
            "latitude": 12.9716,
            "longitude": 77.5946
        }  # Bangalore coordinates as object
    }
    
    # Add file generation parameters
    params = {
        "generate_file": "true",
        "file_size_kb": "20"
    }
    
    response = requests.post(f"{API_BASE}/records/", json=record_data, params=params, headers=headers)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 201:
        record = response.json()
        print("✅ Create with file generation successful!")
        print(f"Record UID: {record['uid']}")
        print(f"File URL: {record.get('file_url', 'None')}")
        print(f"File Name: {record.get('file_name', 'None')}")
        print(f"Status: {record['status']}")
        
        # Verify the filename matches the UID pattern
        if record.get('file_url') and record['uid'] in record['file_url']:
            print("✅ Generated filename correctly uses record UID!")
        else:
            print("❌ Generated filename doesn't match UID pattern")
            
        return record
    else:
        print(f"❌ Create with file generation failed: {response.text}")
        return None

def test_regular_upload_endpoint():
    """Test the /upload endpoint without UID filename (backward compatibility)"""
    print("\n" + "=" * 60)
    print("Testing /upload endpoint (backward compatibility)")
    print("=" * 60)
    
    headers = get_auth_headers()
    if not headers:
        print("❌ Could not authenticate - skipping test")
        return None
    
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
        temp_file.write("This is a test file for regular upload testing.\nTesting backward compatibility.")
        temp_file_path = temp_file.name
    
    try:
        # Test data for the record - use actual UUIDs
        record_data = {
            "title": "Test Regular Upload",
            "description": "Testing backward compatibility",
            "media_type": "text",
            "category_id": "c36fee46-3ee5-40f7-bf7d-90cf3d459808",  # stories category
            "user_id": "5cb9390e-f30d-420e-ad04-27c65afd25f3",     # test user
            "location": "POINT(80.2707 13.0827)"  # Chennai coordinates
        }
        
        # Prepare the multipart form data (use_uid_filename defaults to False)
        with open(temp_file_path, 'rb') as f:
            files = {
                'file': ('regular_test_file.txt', f, 'text/plain')
            }
            
            response = requests.post(f"{API_BASE}/records/upload", files=files, data=record_data, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 201:  # Fixed: 201 is success for upload
            record = response.json()
            print("✅ Regular upload successful!")
            print(f"Record UID: {record['uid']}")
            print(f"File URL: {record['file_url']}")
            print(f"Status: {record['status']}")
            
            # Verify the filename uses original name (not UID)
            if record['file_url'] and 'regular_test_file' in record['file_url']:
                print("✅ Filename correctly uses original file name!")
            else:
                print("⚠️  Filename pattern might have changed")
                
            return record
        else:
            print(f"❌ Regular upload failed: {response.text}")
            return None
            
    finally:
        # Clean up temp file
        os.unlink(temp_file_path)

def test_regular_create_endpoint():
    """Test the / endpoint (POST) without file generation (backward compatibility)"""
    print("\n" + "=" * 60)
    print("Testing /records/ (POST) endpoint (backward compatibility)")
    print("=" * 60)
    
    headers = get_auth_headers()
    if not headers:
        print("❌ Could not authenticate - skipping test")
        return None
    
    # Test data for the record - use actual UUIDs
    record_data = {
        "title": "Test Regular Create",
        "description": "Testing backward compatibility without file generation",
        "media_type": "image",
        "category_id": "62f73989-81e5-4ba8-ad3c-7dd39d403061",  # songs category
        "user_id": "5cb9390e-f30d-420e-ad04-27c65afd25f3",      # test user
        "location": {
            "latitude": 19.0760,
            "longitude": 72.8777
        }  # Mumbai coordinates as object
    }
    
    response = requests.post(f"{API_BASE}/records/", json=record_data, headers=headers)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 201:
        record = response.json()
        print("✅ Regular create successful!")
        print(f"Record UID: {record['uid']}")
        print(f"File URL: {record.get('file_url', 'None')}")
        print(f"Status: {record['status']}")
        
        # Verify no file was generated
        if not record.get('file_url'):
            print("✅ No file generated as expected!")
        else:
            print("⚠️  Unexpected file generation")
            
        return record
    else:
        print(f"❌ Regular create failed: {response.text}")
        return None

def main():
    """Run all tests"""
    print("🚀 Starting API endpoint tests...")
    
    # Test new features
    uploaded_record = test_upload_endpoint_with_uid_filename()
    generated_record = test_create_endpoint_with_file_generation()
    
    # Test backward compatibility
    regular_upload_record = test_regular_upload_endpoint()
    regular_create_record = test_regular_create_endpoint()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    tests = [
        ("Upload with UID filename", uploaded_record is not None),
        ("Create with file generation", generated_record is not None),
        ("Regular upload (backward compatibility)", regular_upload_record is not None),
        ("Regular create (backward compatibility)", regular_create_record is not None)
    ]
    
    for test_name, passed in tests:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(passed for _, passed in tests)
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
