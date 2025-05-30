from fastapi import HTTPException, status

# Example custom exceptions (can be added as needed)
class DetailedHTTPException(HTTPException):
    def __init__(self, status_code: int, detail: any = None, headers: dict = None):
        super().__init__(status_code=status_code, detail=detail, headers=headers)

class PermissionDeniedException(DetailedHTTPException):
    def __init__(self, detail: any = "Permission denied"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

class NotFoundException(DetailedHTTPException):
    def __init__(self, detail: any = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

# You can add more specific exceptions like UserNotFound, CategoryNotFound, etc.
