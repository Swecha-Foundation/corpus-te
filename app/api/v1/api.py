# app/api/v1/api.py
from fastapi import APIRouter
from app.api.v1.endpoints import users, categories, records, roles, auth

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(roles.router, prefix="/roles", tags=["roles"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(records.router, prefix="/records", tags=["records"])
