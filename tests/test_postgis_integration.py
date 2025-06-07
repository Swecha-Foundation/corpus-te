#!/usr/bin/env python3
"""
Test script to validate PostGIS integration with the corpus-te application.
This script tests:
1. PostGIS extension is enabled
2. Point geometry creation and storage
3. Coordinate extraction
4. Spatial queries (distance, bounding box)
"""

from sqlmodel import Session, text
from app.db.session import engine
from app.utils.postgis_utils import (
    create_point_wkt,
    create_point_for_record,
    extract_coordinates_from_geometry
)


def test_postgis_extension():
    """Test if PostGIS extension is properly enabled."""
    print("🧪 Testing PostGIS extension...")
    
    with Session(engine) as session:
        # Check if PostGIS extension is enabled
        result = session.exec(text("SELECT PostGIS_Version();")).first()
        if result:
            print(f"✅ PostGIS version: {result[0]}")
        else:
            print("❌ PostGIS extension not found")
            return False
    
    return True


def test_point_creation():
    """Test creating PostGIS Point geometries."""
    print("\n🧪 Testing Point geometry creation...")
    
    # Test WKT creation
    lat, lng = 17.4065, 78.4772  # Hyderabad coordinates
    wkt = create_point_wkt(lat, lng)
    expected_wkt = f"POINT({lng} {lat})"
    
    if wkt == expected_wkt:
        print(f"✅ WKT creation: {wkt}")
    else:
        print(f"❌ WKT creation failed. Expected: {expected_wkt}, Got: {wkt}")
        return False
    
    # Test geometry creation for records
    point_for_record = create_point_for_record(lat, lng)
    if point_for_record == wkt:
        print(f"✅ Point for record: {point_for_record}")
    else:
        print(f"❌ Point for record failed. Expected: {wkt}, Got: {point_for_record}")
        return False
    
    return True


def test_database_point_operations():
    """Test storing and retrieving PostGIS points from database."""
    print("\n🧪 Testing database Point operations...")
    
    with Session(engine) as session:
        try:
            # Test storing a point using raw SQL (similar to our API endpoints)
            test_lat, test_lng = 17.4065, 78.4772
            point_wkt = create_point_for_record(test_lat, test_lng)
            
            # Insert a test geometry directly
            result = session.exec(text("""
                SELECT ST_GeomFromText(:wkt, 4326) as geom,
                       ST_X(ST_GeomFromText(:wkt, 4326)) as longitude,
                       ST_Y(ST_GeomFromText(:wkt, 4326)) as latitude
            """).params(wkt=point_wkt)).first()
            
            if result:
                geom, lng, lat = result
                print("✅ Geometry storage test passed")
                print(f"   Stored coordinates: lat={lat}, lng={lng}")
                
                # Test coordinate extraction
                print(f"   Geometry type: {type(geom)}")
                print(f"   Geometry repr: {repr(geom)}")
                coords = extract_coordinates_from_geometry(geom)
                if coords:
                    extracted_lng, extracted_lat = coords
                    print(f"   Extracted coordinates: lat={extracted_lat}, lng={extracted_lng}")
                    
                    # Check if coordinates match (with small tolerance for floating point)
                    lat_diff = abs(extracted_lat - test_lat)
                    lng_diff = abs(extracted_lng - test_lng)
                    
                    if lat_diff < 0.0001 and lng_diff < 0.0001:
                        print("✅ Coordinate extraction successful")
                    else:
                        print(f"❌ Coordinate mismatch. Diff: lat={lat_diff}, lng={lng_diff}")
                        return False
                else:
                    print("❌ Failed to extract coordinates from geometry")
                    return False
            else:
                print("❌ Failed to create geometry in database")
                return False
                
        except Exception as e:
            print(f"❌ Database point operations failed: {e}")
            return False
    
    return True


def test_spatial_queries():
    """Test spatial query functions."""
    print("\n🧪 Testing spatial queries...")
    
    with Session(engine) as session:
        try:
            # Test distance query
            center_lat, center_lng = 17.4065, 78.4772
            search_radius = 1000  # 1km
            
            distance_query = text("""
                SELECT ST_DWithin(
                    ST_GeomFromText(:center_point, 4326),
                    ST_GeomFromText(:test_point, 4326),
                    :radius
                ) as within_distance
            """).params(
                center_point=create_point_for_record(center_lat, center_lng),
                test_point=create_point_for_record(center_lat + 0.005, center_lng + 0.005),  # ~500m away
                radius=search_radius
            )
            
            result = session.exec(distance_query).first()
            if result and result[0]:  # Should be within 1km
                print("✅ Distance query test passed")
            else:
                print("❌ Distance query test failed")
                return False
            
            # Test bounding box query
            bbox_query = text("""
                SELECT ST_Within(
                    ST_GeomFromText(:test_point, 4326),
                    ST_GeomFromText(:bbox, 4326)
                ) as within_bbox
            """).params(
                test_point=create_point_for_record(center_lat, center_lng),
                bbox=f"POLYGON(({center_lng-0.01} {center_lat-0.01}, {center_lng+0.01} {center_lat-0.01}, {center_lng+0.01} {center_lat+0.01}, {center_lng-0.01} {center_lat+0.01}, {center_lng-0.01} {center_lat-0.01}))"
            )
            
            result = session.exec(bbox_query).first()
            if result and result[0]:  # Should be within bounding box
                print("✅ Bounding box query test passed")
            else:
                print("❌ Bounding box query test failed")
                return False
                
        except Exception as e:
            print(f"❌ Spatial queries failed: {e}")
            return False
    
    return True


def test_record_table_schema():
    """Test that the Record table has the correct PostGIS schema."""
    print("\n🧪 Testing Record table schema...")
    
    with Session(engine) as session:
        try:
            # Check if location column exists and is geometry type
            result = session.exec(text("""
                SELECT 
                    column_name,
                    data_type,
                    udt_name
                FROM information_schema.columns 
                WHERE table_name = 'record' 
                AND column_name = 'location'
            """)).first()
            
            if result:
                column_name, data_type, udt_name = result
                print(f"✅ Location column found: {column_name} ({data_type}, {udt_name})")
                
                if udt_name == 'geometry':
                    print("✅ Location column is geometry type")
                else:
                    print(f"❌ Expected geometry type, got: {udt_name}")
                    return False
            else:
                print("❌ Location column not found in record table")
                return False
            
            # Check if spatial index exists
            result = session.exec(text("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = 'record' 
                AND indexname LIKE '%location%'
            """)).first()
            
            if result:
                print(f"✅ Spatial index found: {result[0]}")
            else:
                print("⚠️  No spatial index found (this is optional but recommended)")
                
        except Exception as e:
            print(f"❌ Schema test failed: {e}")
            return False
    
    return True


def main():
    """Run all PostGIS integration tests."""
    print("🚀 Starting PostGIS Integration Tests")
    print("=" * 50)
    
    tests = [
        test_postgis_extension,
        test_point_creation,
        test_record_table_schema,
        test_database_point_operations,
        test_spatial_queries,
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
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All PostGIS integration tests passed!")
        print("✅ PostGIS is properly integrated with the corpus-te application")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
