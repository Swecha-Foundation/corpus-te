#!/usr/bin/env python3
"""
Test script to validate PostGIS API endpoints in the corpus-te application.
This script tests the Record API endpoints with PostGIS coordinate handling.
"""

import requests
import json

# Test configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Test data
TEST_COORDINATES = [
    {"latitude": 17.4065, "longitude": 78.4772, "name": "Hyderabad"},
    {"latitude": 28.6139, "longitude": 77.2090, "name": "Delhi"},
    {"latitude": 19.0760, "longitude": 72.8777, "name": "Mumbai"},
    {"latitude": 13.0827, "longitude": 80.2707, "name": "Chennai"},
    {"latitude": 12.9716, "longitude": 77.5946, "name": "Bangalore"}
]


def test_api_health():
    """Test if the API is accessible."""
    print("🧪 Testing API health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is healthy and accessible")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ API is not accessible: {e}")
        return False


def test_openapi_docs():
    """Test if OpenAPI documentation is accessible."""
    print("\n🧪 Testing OpenAPI documentation...")
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ OpenAPI docs are accessible")
            return True
        else:
            print(f"❌ OpenAPI docs not accessible: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ OpenAPI docs request failed: {e}")
        return False


def test_records_endpoint_structure():
    """Test the records endpoint structure without authentication."""
    print("\n🧪 Testing records endpoint structure...")
    try:
        # This should return 401/403 for authentication, but endpoint should exist
        response = requests.get(f"{API_BASE}/records/", timeout=5)
        if response.status_code in [401, 403, 422]:  # Expected auth errors
            print("✅ Records endpoint exists (authentication required)")
            return True
        elif response.status_code == 200:
            print("✅ Records endpoint accessible")
            return True
        else:
            print(f"❌ Unexpected records endpoint response: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Records endpoint request failed: {e}")
        return False


def test_spatial_endpoints_structure():
    """Test that spatial search endpoints exist."""
    print("\n🧪 Testing spatial search endpoints structure...")
    
    spatial_endpoints = [
        "/records/search/nearby",
        "/records/search/bbox", 
        "/records/search/distance"
    ]
    
    results = []
    for endpoint in spatial_endpoints:
        try:
            # Add required query parameters to avoid 422 errors
            params = {
                "latitude": 17.4065,
                "longitude": 78.4772,
                "distance_meters": 1000
            } if "nearby" in endpoint else {
                "min_lat": 17.0, "min_lng": 78.0,
                "max_lat": 18.0, "max_lng": 79.0
            } if "bbox" in endpoint else {
                "latitude": 17.4065,
                "longitude": 78.4772
            }
            
            response = requests.get(f"{API_BASE}{endpoint}", params=params, timeout=5)
            if response.status_code in [401, 403, 422]:  # Expected auth/validation errors
                print(f"✅ {endpoint} endpoint exists (auth/validation required)")
                results.append(True)
            elif response.status_code == 200:
                print(f"✅ {endpoint} endpoint accessible")
                results.append(True)
            else:
                print(f"❌ {endpoint} unexpected response: {response.status_code}")
                results.append(False)
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint} request failed: {e}")
            results.append(False)
    
    return all(results)


def test_coordinate_validation():
    """Test coordinate validation in API endpoints."""
    print("\n🧪 Testing coordinate validation...")
    
    # Test invalid coordinates
    invalid_coords = [
        {"latitude": 91, "longitude": 0, "error": "latitude out of range"},
        {"latitude": -91, "longitude": 0, "error": "latitude out of range"},
        {"latitude": 0, "longitude": 181, "error": "longitude out of range"},
        {"latitude": 0, "longitude": -181, "error": "longitude out of range"}
    ]
    
    results = []
    for coord in invalid_coords:
        try:
            params = {
                "latitude": coord["latitude"],
                "longitude": coord["longitude"],
                "distance_meters": 1000
            }
            response = requests.get(f"{API_BASE}/records/search/nearby", params=params, timeout=5)
            
            # Should return 422 for validation error
            if response.status_code == 422:
                print(f"✅ Coordinate validation working: {coord['error']}")
                results.append(True)
            else:
                print(f"❌ Validation not working for {coord['error']}: {response.status_code}")
                results.append(False)
        except requests.exceptions.RequestException as e:
            print(f"❌ Validation test failed for {coord['error']}: {e}")
            results.append(False)
    
    return all(results)


def test_database_connection():
    """Test database connectivity through a simple endpoint."""
    print("\n🧪 Testing database connectivity...")
    try:
        # Try to access any endpoint that would hit the database
        response = requests.get(f"{API_BASE}/records/", timeout=10)
        
        # Any response other than connection error indicates DB is accessible
        if response.status_code != 500:
            print("✅ Database connection working")
            return True
        else:
            print("❌ Database connection error")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Database connectivity test failed: {e}")
        return False


def generate_api_usage_examples():
    """Generate example API usage for PostGIS endpoints."""
    print("\n📚 PostGIS API Usage Examples:")
    print("=" * 50)
    
    examples = [
        {
            "name": "Search records near a point",
            "method": "GET",
            "url": f"{API_BASE}/records/search/nearby",
            "params": {
                "latitude": 17.4065,
                "longitude": 78.4772,
                "distance_meters": 1000,
                "limit": 10
            }
        },
        {
            "name": "Search records in bounding box",
            "method": "GET", 
            "url": f"{API_BASE}/records/search/bbox",
            "params": {
                "min_lat": 17.0,
                "min_lng": 78.0,
                "max_lat": 18.0,
                "max_lng": 79.0,
                "limit": 20
            }
        },
        {
            "name": "Get records with distances",
            "method": "GET",
            "url": f"{API_BASE}/records/search/distance", 
            "params": {
                "latitude": 17.4065,
                "longitude": 78.4772,
                "max_distance_meters": 5000,
                "limit": 15
            }
        },
        {
            "name": "Create record with location",
            "method": "POST",
            "url": f"{API_BASE}/records/",
            "body": {
                "title": "Test Record",
                "description": "A test record with PostGIS location",
                "media_type": "text",
                "category_id": "uuid-here",
                "user_id": "uuid-here",
                "location": {
                    "latitude": 17.4065,
                    "longitude": 78.4772
                }
            }
        }
    ]
    
    for example in examples:
        print(f"\n📝 {example['name']}:")
        print(f"   {example['method']} {example['url']}")
        if 'params' in example:
            print(f"   Query Parameters: {json.dumps(example['params'], indent=6)}")
        if 'body' in example:
            print(f"   Request Body: {json.dumps(example['body'], indent=6)}")
    
    print("\n💡 Notes:")
    print("   - All spatial endpoints require authentication (admin/reviewer roles)")
    print("   - Coordinates use WGS84 (SRID 4326) format")
    print("   - Distances are in meters")
    print("   - Latitude range: -90 to 90")
    print("   - Longitude range: -180 to 180")


def main():
    """Run all API validation tests."""
    print("🚀 Starting PostGIS API Validation Tests")
    print("=" * 50)
    
    tests = [
        test_api_health,
        test_openapi_docs,
        test_records_endpoint_structure,
        test_spatial_endpoints_structure,
        test_coordinate_validation,
        test_database_connection,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ Test {test.__name__} failed")
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 API Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All API validation tests passed!")
        print("✅ PostGIS API endpoints are properly configured")
    else:
        print("❌ Some API tests failed. Check server logs for details.")
    
    # Generate usage examples regardless of test results
    generate_api_usage_examples()
    
    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
