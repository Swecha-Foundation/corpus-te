from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select

from app.db.session import SessionDep
from app.models.category import Category
from app.models.user import User
from app.core.rbac_fastapi import require_any_role, require_admin

router = APIRouter()

@router.get("/", response_model=List[Category])
def get_categories(
    session: SessionDep,
    current_user: User = Depends(require_any_role())
    ) -> List[Category]:
    """Get all categories."""
    categories = session.exec(select(Category)).all()
    return list(categories)

@router.get("/{category_id}", response_model=Category)
def get_category(
    category_id: str, 
    session: SessionDep,
    current_user: User = Depends(require_any_role())
    ) -> Category:
    """Get a specific category by ID."""
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.post("/", response_model=Category, status_code=201)
def create_category(
    category_data: Category,
    session: SessionDep,
    current_user: User = Depends(require_admin())
) -> Category:
    """Create a new category."""
    # Check if category with same name already exists
    existing = session.exec(
        select(Category).where(Category.name == category_data.name)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category with this name already exists")
    
    # Create new category
    category = Category.model_validate(category_data.model_dump())
    session.add(category)
    session.commit()
    session.refresh(category)
    return category

@router.put("/{category_id}", response_model=Category)
def update_category(
    category_id: str, 
    category_data: Category, 
    session: SessionDep,
    current_user: User = Depends(require_admin())
    ) -> Category:
    """Update a category."""
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check if another category with same name exists
    existing = session.exec(
        select(Category).where(
            Category.name == category_data.name,
            Category.id != category_id
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category with this name already exists")
    
    # Update category
    category.name = category_data.name
    if category_data.description is not None:
        category.description = category_data.description
    
    session.add(category)
    session.commit()
    session.refresh(category)
    return category

@router.delete("/{category_id}")
def delete_category(
    category_id: str, 
    session: SessionDep,
    current_user: User = Depends(require_admin())
    ) -> dict:
    """Delete a category."""
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    session.delete(category)
    session.commit()
    return {"message": "Category deleted successfully"}
