from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.config import settings
from app.core.logging_config import setup_logging
# from app.api.v1 import api_router as api_v1_router # Placeholder for API router
# from app.db.session import engine # Placeholder for DB engine creation
# from app.db.base import Base # Placeholder for DB base for table creation

# Setup logging
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # You can customize the error response format here
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Log the exception here if needed
    # For production, you might want to return a generic error message
    # and log the actual error internally.
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )

@app.on_event("startup")
async def startup_event():
    # Base.metadata.create_all(bind=engine) # Placeholder: Create DB tables if they don't exist
    # This is often handled by Alembic migrations in production, but can be useful for local dev/testing
    pass

@app.on_event("shutdown")
async def shutdown_event():
    pass

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}

# app.include_router(api_v1_router, prefix=settings.API_V1_STR) # Placeholder

# Add a note that python-dotenv should be added to requirements.txt if .env files are to be used by pydantic-settings.
