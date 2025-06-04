from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query
from sqlmodel import Session, select
from uuid import UUID
import uuid
import logging

from app.db.session import SessionDep
from app.models.record import Record, MediaType
from app.core.rbac_fastapi import require_any_role, require_admin, create_rbac_dependency
from app.models.user import User
from app.schemas import RecordCreate, RecordUpdate, RecordRead
from app.schemas.geo_schemas import LocationSearch, BoundingBox, Coordinates
from app.utils.postgis_utils import (
    create_point_geometry,
    create_point_for_record,
    extract_coordinates_from_point,
    extract_coordinates_from_geometry,
    distance_query,
    bbox_query
)
from app.utils.hetzner_storage import upload_file_to_hetzner, delete_file_from_hetzner

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[RecordRead])
def get_records(
    session: SessionDep,
    category_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    media_type: Optional[MediaType] = None,
    current_user: User = Depends(create_rbac_dependency(roles=["admin", "reviewer"])),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return")
) -> List[RecordRead]:
    """Get all records with optional filtering and pagination."""
    query = select(Record).offset(skip).limit(limit)
    
    if category_id:
        query = query.where(Record.category_id == category_id)
    if user_id:
        query = query.where(Record.user_id == user_id)
    if media_type:
        query = query.where(Record.media_type == media_type)
    
    records = session.exec(query).all()
    
    # Convert records to read schema with location coordinates
    result = []
    for record in records:
        record_data = RecordRead.model_validate(record)
        if record.location:
            coords = extract_coordinates_from_geometry(record.location)
            if coords:
                # coords is (longitude, latitude) tuple
                record_data.location = Coordinates(latitude=coords[1], longitude=coords[0])
        result.append(record_data)
    
    return result

@router.get("/{record_id}", response_model=RecordRead)
def get_record(
    record_id: str, 
    session: SessionDep,
    current_user: User = Depends(create_rbac_dependency(roles=["admin", "reviewer"]))
    ) -> RecordRead:
    """Get a specific record by ID."""
    try:
        record_uuid = uuid.UUID(record_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid record ID format")
    
    record = session.get(Record, record_uuid)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    # Convert to read schema with coordinates
    result = RecordRead.model_validate(record)
    if record.location:
        coords = extract_coordinates_from_geometry(record.location)
        if coords:
            result.location = Coordinates(latitude=coords[1], longitude=coords[0])
    
    return result

@router.post("/", response_model=RecordRead, status_code=201)
def create_record(
    record_data: RecordCreate, 
    session: SessionDep,
    current_user: User = Depends(require_any_role())
) -> RecordRead:
    """Create a new record."""
    # Validate foreign keys exist
    from app.models.category import Category
    from app.models.user import User
    
    if record_data.category_id:
        category = session.get(Category, record_data.category_id)
        if not category:
            raise HTTPException(status_code=400, detail="Category not found")
    
    if record_data.user_id:
        user = session.get(User, record_data.user_id)
        if not user:
            raise HTTPException(status_code=400, detail="User not found")
    
    # Convert schema data to model data
    record_dict = record_data.model_dump(exclude={'location'})
    
    # Create new record
    record = Record.model_validate(record_dict)
    
    # Handle PostGIS location if provided using SQLAlchemy session
    if record_data.location:
        from sqlalchemy import text
        # Use raw SQL to set the geometry
        session.add(record)
        session.flush()  # Get the ID
        session.execute(
            text("UPDATE record SET location = ST_GeomFromText(:wkt, 4326) WHERE uid = :uid"),
            {
                "wkt": create_point_for_record(record_data.location.latitude, record_data.location.longitude),
                "uid": record.uid
            }
        )
    else:
        session.add(record)
    session.commit()
    session.refresh(record)
    
    # Convert to read schema with coordinates
    result = RecordRead.model_validate(record)
    if record.location:
        coords = extract_coordinates_from_geometry(record.location)
        if coords:
            result.location = Coordinates(latitude=coords[1], longitude=coords[0])
    
    return result

@router.post("/upload", response_model=RecordRead, status_code=201)
async def upload_record(
    session: SessionDep,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    category_id: str = Form(...),
    user_id: str = Form(...),
    media_type: MediaType = Form(...),
    file: UploadFile = File(...),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    current_user: User = Depends(require_any_role())
) -> RecordRead:
    """Upload a file and create a record."""
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Convert string UUIDs to UUID objects
    try:
        category_uuid = uuid.UUID(category_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid category ID format")
    
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    # Upload file to Hetzner Object Storage
    try:
        # Determine prefix based on media type
        prefix = f"{media_type.value}/" if media_type else "misc/"
        metadata = {
            "title": title,
            "user_id": str(user_uuid),
            "category_id": str(category_uuid),
            "media_type": media_type.value if media_type else "unknown"
        }
        
        upload_result = await upload_file_to_hetzner(file, prefix=prefix, metadata=metadata)
        file_url = upload_result["object_url"]
        object_key = upload_result["object_key"]
        actual_file_size = upload_result["file_size"]
        
    except Exception as e:
        logger.error(f"Failed to upload file to Hetzner storage: {e}")
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")
    
    # Validate foreign keys
    from app.models.category import Category
    from app.models.user import User
    
    category = session.get(Category, category_uuid)
    if not category:
        raise HTTPException(status_code=400, detail="Category not found")
    
    user = session.get(User, user_uuid)
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    
    # Create record
    record_data = Record(
        title=title,
        description=description,
        category_id=category_uuid,
        user_id=user_uuid,
        media_type=media_type,
        file_url=file_url,
        file_name=file.filename,
        file_size=actual_file_size,
        status="uploaded"  # Mark as uploaded since file upload succeeded
    )
    
    session.add(record_data)
    
    # Handle PostGIS location if coordinates provided using raw SQL
    if latitude is not None and longitude is not None:
        from sqlalchemy import text
        session.flush()  # Get the ID
        session.execute(
            text("UPDATE record SET location = ST_GeomFromText(:wkt, 4326) WHERE uid = :uid"),
            {
                "wkt": create_point_for_record(latitude, longitude),
                "uid": record_data.uid
            }
        )
    session.commit()
    session.refresh(record_data)
    
    # Convert to read schema with coordinates
    result = RecordRead.model_validate(record_data)
    if record_data.location:
        coords = extract_coordinates_from_geometry(record_data.location)
        if coords:
            result.location = Coordinates(latitude=coords[1], longitude=coords[0])
    
    return result

@router.put("/{record_id}", response_model=RecordRead)
def update_record(
    record_id: str, 
    record_data: RecordUpdate, 
    session: SessionDep,
    current_user: User = Depends(create_rbac_dependency(roles=["admin", "reviewer"]))
    ) -> RecordRead:
    """Update a record."""
    try:
        record_uuid = uuid.UUID(record_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid record ID format")
    
    record = session.get(Record, record_uuid)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    # Update record fields (excluding location for special handling)
    update_data = record_data.model_dump(exclude_unset=True, exclude={'location'})
    for field, value in update_data.items():
        if hasattr(record, field):
            setattr(record, field, value)
    
    # Handle PostGIS location update if provided
    if record_data.location is not None:
        from sqlalchemy import text
        session.flush()  # Ensure record is persisted
        session.execute(
            text("UPDATE record SET location = ST_GeomFromText(:wkt, 4326) WHERE uid = :uid"),
            {
                "wkt": create_point_for_record(record_data.location.latitude, record_data.location.longitude),
                "uid": record.uid
            }
        )
    
    session.commit()
    session.refresh(record)
    
    # Convert to read schema with coordinates
    result = RecordRead.model_validate(record)
    if record.location:
        coords = extract_coordinates_from_geometry(record.location)
        if coords:
            result.location = Coordinates(latitude=coords[1], longitude=coords[0])
    
    return result

@router.delete("/{record_id}")
def delete_record(
    record_id: str, 
    session: SessionDep,
    current_user: User = Depends(require_admin())
) -> dict:
    """Delete a record."""
    try:
        record_uuid = uuid.UUID(record_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid record ID format")
    
    record = session.get(Record, record_uuid)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    # Delete the actual file from Hetzner storage if it exists
    if record.file_url:
        try:
            # Extract object key from file URL
            # Assuming URL format: https://endpoint/bucket/object_key
            url_parts = record.file_url.split('/')
            if len(url_parts) >= 2:
                object_key = '/'.join(url_parts[-2:])  # Get bucket/object_key part
                if '/' in object_key:
                    object_key = object_key.split('/', 1)[1]  # Remove bucket name, keep object key
                    delete_file_from_hetzner(object_key)
                    logger.info(f"Successfully deleted file {object_key} from storage")
        except Exception as e:
            logger.warning(f"Failed to delete file from storage for record {record_id}: {e}")
            # Continue with record deletion even if file deletion fails
    
    session.delete(record)
    session.commit()
    return {"message": "Record deleted successfully"}

# Location-based search endpoints

@router.get("/search/nearby", response_model=List[RecordRead])
def search_records_nearby(
    session: SessionDep,
    latitude: float = Query(..., ge=-90, le=90, description="Latitude coordinate"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude coordinate"),
    distance_meters: float = Query(..., gt=0, le=50000, description="Search radius in meters (max 50km)"),
    category_id: Optional[UUID] = None,
    media_type: Optional[MediaType] = None,
    current_user: User = Depends(create_rbac_dependency(roles=["admin", "reviewer"])),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
) -> List[RecordRead]:
    """Search for records within a specified distance of a point."""
    from sqlalchemy import text
    
    # Build the base query with PostGIS distance calculation
    distance_condition = text(
        "ST_DWithin(location, ST_GeomFromText(:point_wkt, 4326), :distance) AND location IS NOT NULL"
    )
    
    query = select(Record).where(
        distance_condition
    ).params(
        point_wkt=create_point_for_record(latitude, longitude),
        distance=distance_meters
    )
    
    # Add additional filters
    if category_id:
        query = query.where(Record.category_id == category_id)
    if media_type:
        query = query.where(Record.media_type == media_type)
    
    # Add ordering by distance and pagination
    query = query.order_by(
        text("ST_Distance(location, ST_GeomFromText(:point_wkt, 4326))")
    ).offset(skip).limit(limit)
    
    records = session.exec(query).all()
    
    # Convert to read schema with coordinates
    result = []
    for record in records:
        record_data = RecordRead.model_validate(record)
        if record.location:
            coords = extract_coordinates_from_geometry(record.location)
            if coords:
                record_data.location = Coordinates(latitude=coords[1], longitude=coords[0])
        result.append(record_data)
    
    return result

@router.get("/search/bbox", response_model=List[RecordRead])
def search_records_in_bbox(
    session: SessionDep,
    min_lat: float = Query(..., ge=-90, le=90, description="Minimum latitude"),
    min_lng: float = Query(..., ge=-180, le=180, description="Minimum longitude"), 
    max_lat: float = Query(..., ge=-90, le=90, description="Maximum latitude"),
    max_lng: float = Query(..., ge=-180, le=180, description="Maximum longitude"),
    category_id: Optional[UUID] = None,
    media_type: Optional[MediaType] = None,
    current_user: User = Depends(create_rbac_dependency(roles=["admin", "reviewer"])),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
) -> List[RecordRead]:
    """Search for records within a bounding box (rectangular area)."""
    from sqlalchemy import text
    
    # Validate bounding box
    if min_lat >= max_lat or min_lng >= max_lng:
        raise HTTPException(
            status_code=400, 
            detail="Invalid bounding box: min coordinates must be less than max coordinates"
        )
    
    # Create bounding box polygon WKT
    bbox_wkt = f"POLYGON(({min_lng} {min_lat}, {max_lng} {min_lat}, {max_lng} {max_lat}, {min_lng} {max_lat}, {min_lng} {min_lat}))"
    
    # Build query with PostGIS bounding box check
    bbox_condition = text(
        "ST_Within(location, ST_GeomFromText(:bbox_wkt, 4326)) AND location IS NOT NULL"
    )
    
    query = select(Record).where(
        bbox_condition
    ).params(bbox_wkt=bbox_wkt)
    
    # Add additional filters
    if category_id:
        query = query.where(Record.category_id == category_id)
    if media_type:
        query = query.where(Record.media_type == media_type)
    
    # Add pagination
    query = query.offset(skip).limit(limit)
    
    records = session.exec(query).all()
    
    # Convert to read schema with coordinates
    result = []
    for record in records:
        record_data = RecordRead.model_validate(record)
        if record.location:
            coords = extract_coordinates_from_geometry(record.location)
            if coords:
                record_data.location = Coordinates(latitude=coords[1], longitude=coords[0])
        result.append(record_data)
    
    return result

@router.get("/search/distance", response_model=List[dict])
def get_records_with_distances(
    session: SessionDep,
    latitude: float = Query(..., ge=-90, le=90, description="Reference latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Reference longitude"),
    max_distance_meters: Optional[float] = Query(None, gt=0, le=100000, description="Maximum distance in meters"),
    current_user: User = Depends(create_rbac_dependency(roles=["admin", "reviewer"])),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500)
) -> List[dict]:
    """Get records with calculated distances from a reference point."""
    from sqlalchemy import text
    
    # Build query with distance calculation
    distance_expr = text(
        "ST_Distance(location, ST_GeomFromText(:point_wkt, 4326)) as distance_meters"
    )
    
    base_query = select(
        Record,
        distance_expr
    ).where(
        text("location IS NOT NULL")
    ).params(
        point_wkt=create_point_for_record(latitude, longitude)
    )
    
    # Add distance filter if specified
    if max_distance_meters:
        distance_filter = text(
            "ST_DWithin(location, ST_GeomFromText(:point_wkt, 4326), :max_distance)"
        )
        base_query = base_query.where(distance_filter).params(max_distance=max_distance_meters)
    
    # Order by distance and add pagination
    query = base_query.order_by(text("distance_meters")).offset(skip).limit(limit)
    
    results = session.exec(query).all()
    
    # Convert to response format
    response = []
    for record, distance in results:
        record_data = RecordRead.model_validate(record)
        if record.location:
            coords = extract_coordinates_from_geometry(record.location)
            if coords:
                record_data.location = Coordinates(latitude=coords[1], longitude=coords[0])
        
        response.append({
            "record": record_data.model_dump(),
            "distance_meters": float(distance),
            "distance_km": round(float(distance) / 1000, 2)
        })
    
    return response
