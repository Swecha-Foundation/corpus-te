from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlmodel import Session, select
from uuid import UUID
import uuid

from app.db.session import SessionDep
from app.models.record import Record, MediaType

router = APIRouter()

@router.get("/", response_model=List[Record])
def get_records(
    session: SessionDep,
    category_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    media_type: Optional[MediaType] = None
) -> List[Record]:
    """Get all records with optional filtering."""
    query = select(Record)
    
    if category_id:
        query = query.where(Record.category_id == category_id)
    if user_id:
        query = query.where(Record.user_id == user_id)
    if media_type:
        query = query.where(Record.media_type == media_type)
    
    records = session.exec(query).all()
    return list(records)

@router.get("/{record_id}", response_model=Record)
def get_record(record_id: str, session: SessionDep) -> Record:
    """Get a specific record by ID."""
    try:
        record_uuid = uuid.UUID(record_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid record ID format")
    
    record = session.get(Record, record_uuid)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record

@router.post("/", response_model=Record, status_code=201)
def create_record(record_data: Record, session: SessionDep) -> Record:
    """Create a new record."""
    # Validate foreign keys exist
    from app.models.category import Category
    from app.models.user import User
    
    if record_data.category_id:
        # Convert string UUID to UUID object if needed
        category_uuid = record_data.category_id
        if isinstance(category_uuid, str):
            category_uuid = uuid.UUID(category_uuid)
        category = session.get(Category, category_uuid)
        if not category:
            raise HTTPException(status_code=400, detail="Category not found")
    
    if record_data.user_id:
        # Convert string UUID to UUID object if needed
        user_uuid = record_data.user_id
        if isinstance(user_uuid, str):
            user_uuid = uuid.UUID(user_uuid)
        user = session.get(User, user_uuid)
        if not user:
            raise HTTPException(status_code=400, detail="User not found")
    
    # Create new record
    record = Record.model_validate(record_data.model_dump())
    session.add(record)
    session.commit()
    session.refresh(record)
    return record

@router.post("/upload", response_model=Record, status_code=201)
async def upload_record(
    session: SessionDep,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    category_id: str = Form(...),
    user_id: str = Form(...),
    media_type: MediaType = Form(...),
    file: UploadFile = File(...)
) -> Record:
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
    
    # TODO: Implement file upload to MinIO/S3
    # For now, just create the record without actual file upload
    file_url = f"/uploads/{file.filename}"  # Placeholder
    
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
        file_size=file.size if file.size else 0
    )
    
    session.add(record_data)
    session.commit()
    session.refresh(record_data)
    return record_data

@router.put("/{record_id}", response_model=Record)
def update_record(record_id: str, record_data: Record, session: SessionDep) -> Record:
    """Update a record."""
    try:
        record_uuid = uuid.UUID(record_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid record ID format")
    
    record = session.get(Record, record_uuid)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    # Validate foreign keys if they're being updated
    from app.models.category import Category
    from app.models.user import User
    
    if record_data.category_id and record_data.category_id != record.category_id:
        # Convert string UUID to UUID object if needed
        category_uuid = record_data.category_id
        if isinstance(category_uuid, str):
            try:
                category_uuid = uuid.UUID(category_uuid)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid category ID format")
        category = session.get(Category, category_uuid)
        if not category:
            raise HTTPException(status_code=400, detail="Category not found")
    
    if record_data.user_id and record_data.user_id != record.user_id:
        # Convert string UUID to UUID object if needed
        user_uuid = record_data.user_id
        if isinstance(user_uuid, str):
            try:
                user_uuid = uuid.UUID(user_uuid)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid user ID format")
        user = session.get(User, user_uuid)
        if not user:
            raise HTTPException(status_code=400, detail="User not found")
    
    # Update record fields
    update_data = record_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(record, field):
            # Convert string UUIDs to UUID objects for foreign key fields
            if field in ['category_id', 'user_id'] and value and isinstance(value, str):
                try:
                    value = uuid.UUID(value)
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid {field} format")
            setattr(record, field, value)
    
    session.add(record)
    session.commit()
    session.refresh(record)
    return record

@router.delete("/{record_id}")
def delete_record(record_id: str, session: SessionDep) -> dict:
    """Delete a record."""
    try:
        record_uuid = uuid.UUID(record_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid record ID format")
    
    record = session.get(Record, record_uuid)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    # TODO: Also delete the actual file from MinIO/S3
    
    session.delete(record)
    session.commit()
    return {"message": "Record deleted successfully"}
