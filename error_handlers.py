"""
Standardized error handling for CosmoFolio APIs
Phase 1: Task 1.9 - Error handling and validation
"""

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# ==================== ERROR RESPONSE MODELS ====================

class APIError:
    """Standardized API error response"""
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        timestamp: Optional[str] = None,
        context: Optional[dict] = None
    ):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code or self._get_error_code(status_code)
        self.timestamp = timestamp or datetime.utcnow().isoformat()
        self.context = context or {}

    def to_dict(self) -> dict:
        """Convert to JSON response"""
        return {
            "error": {
                "code": self.error_code,
                "message": self.detail,
                "status_code": self.status_code,
                "timestamp": self.timestamp,
                "context": self.context if self.context else None
            }
        }

    @staticmethod
    def _get_error_code(status_code: int) -> str:
        """Get standard error code from status code"""
        codes = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            409: "CONFLICT",
            422: "VALIDATION_ERROR",
            500: "INTERNAL_SERVER_ERROR",
            503: "SERVICE_UNAVAILABLE"
        }
        return codes.get(status_code, f"ERROR_{status_code}")


# ==================== CUSTOM EXCEPTIONS ====================

class CosmoFolioException(Exception):
    """Base exception for CosmoFolio"""
    def __init__(
        self,
        detail: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        context: Optional[dict] = None
    ):
        self.detail = detail
        self.status_code = status_code
        self.error_code = error_code
        self.context = context
        super().__init__(self.detail)


class ValidationException(CosmoFolioException):
    """Validation error (400)"""
    def __init__(self, detail: str, context: Optional[dict] = None):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="VALIDATION_ERROR",
            context=context
        )


class AuthenticationException(CosmoFolioException):
    """Authentication error (401)"""
    def __init__(self, detail: str = "Invalid or missing authentication"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="UNAUTHORIZED"
        )


class AuthorizationException(CosmoFolioException):
    """Authorization error (403)"""
    def __init__(self, detail: str = "Access denied"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="FORBIDDEN"
        )


class ResourceNotFoundException(CosmoFolioException):
    """Not found error (404)"""
    def __init__(self, resource: str, resource_id: Optional[str] = None):
        detail = f"{resource} not found"
        if resource_id:
            detail = f"{resource} '{resource_id}' not found"
        super().__init__(
            detail=detail,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND"
        )


class ConflictException(CosmoFolioException):
    """Conflict error (409)"""
    def __init__(self, detail: str):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT"
        )


class DatabaseException(CosmoFolioException):
    """Database operation error (500)"""
    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DATABASE_ERROR"
        )


# ==================== EXCEPTION HANDLERS ====================

def setup_error_handlers(app: FastAPI):
    """Register all error handlers with FastAPI"""

    @app.exception_handler(ValidationException)
    async def validation_exception_handler(request: Request, exc: ValidationException):
        return JSONResponse(
            status_code=exc.status_code,
            content=APIError(
                status_code=exc.status_code,
                detail=exc.detail,
                error_code=exc.error_code,
                context=exc.context
            ).to_dict()
        )

    @app.exception_handler(AuthenticationException)
    async def auth_exception_handler(request: Request, exc: AuthenticationException):
        return JSONResponse(
            status_code=exc.status_code,
            content=APIError(
                status_code=exc.status_code,
                detail=exc.detail,
                error_code=exc.error_code
            ).to_dict()
        )

    @app.exception_handler(AuthorizationException)
    async def authz_exception_handler(request: Request, exc: AuthorizationException):
        return JSONResponse(
            status_code=exc.status_code,
            content=APIError(
                status_code=exc.status_code,
                detail=exc.detail,
                error_code=exc.error_code
            ).to_dict()
        )

    @app.exception_handler(ResourceNotFoundException)
    async def notfound_exception_handler(request: Request, exc: ResourceNotFoundException):
        return JSONResponse(
            status_code=exc.status_code,
            content=APIError(
                status_code=exc.status_code,
                detail=exc.detail,
                error_code=exc.error_code
            ).to_dict()
        )

    @app.exception_handler(ConflictException)
    async def conflict_exception_handler(request: Request, exc: ConflictException):
        return JSONResponse(
            status_code=exc.status_code,
            content=APIError(
                status_code=exc.status_code,
                detail=exc.detail,
                error_code=exc.error_code
            ).to_dict()
        )

    @app.exception_handler(CosmoFolioException)
    async def generic_exception_handler(request: Request, exc: CosmoFolioException):
        return JSONResponse(
            status_code=exc.status_code,
            content=APIError(
                status_code=exc.status_code,
                detail=exc.detail,
                error_code=exc.error_code,
                context=exc.context
            ).to_dict()
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_handler(request: Request, exc: ValidationError):
        errors = []
        for error in exc.errors():
            field = ".".join(str(x) for x in error["loc"][1:])
            errors.append({
                "field": field,
                "message": error["msg"],
                "type": error["type"]
            })
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=APIError(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Request validation failed",
                error_code="VALIDATION_ERROR",
                context={"errors": errors}
            ).to_dict()
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=APIError(
                status_code=exc.status_code,
                detail=exc.detail
            ).to_dict()
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=APIError(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error. Please try again later.",
                error_code="INTERNAL_ERROR"
            ).to_dict()
        )


# ==================== VALIDATION UTILITIES ====================

class ValidationRules:
    """Standard validation rules for CosmoFolio"""

    @staticmethod
    def validate_portfolio_title(title: str) -> bool:
        """Validate portfolio title"""
        if not title or len(title) == 0:
            raise ValidationException("Portfolio title is required")
        if len(title) > 255:
            raise ValidationException("Portfolio title must be less than 255 characters")
        return True

    @staticmethod
    def validate_architect_name(name: str) -> bool:
        """Validate architect name"""
        if not name or len(name) == 0:
            raise ValidationException("Architect name is required")
        if len(name) > 255:
            raise ValidationException("Architect name must be less than 255 characters")
        return True

    @staticmethod
    def validate_page_size(page_size: str) -> bool:
        """Validate page size"""
        valid_sizes = ['a4', 'a3', 'letter', 'tabloid', 'custom']
        if page_size not in valid_sizes:
            raise ValidationException(
                f"Invalid page size. Must be one of: {', '.join(valid_sizes)}",
                context={"valid_sizes": valid_sizes}
            )
        return True

    @staticmethod
    def validate_orientation(orientation: str) -> bool:
        """Validate page orientation"""
        valid_orientations = ['portrait', 'landscape']
        if orientation not in valid_orientations:
            raise ValidationException(
                f"Invalid orientation. Must be one of: {', '.join(valid_orientations)}",
                context={"valid_orientations": valid_orientations}
            )
        return True

    @staticmethod
    def validate_margins(margins: str) -> bool:
        """Validate margins"""
        valid_margins = ['compact', 'standard', 'generous', 'custom']
        if margins not in valid_margins:
            raise ValidationException(
                f"Invalid margins. Must be one of: {', '.join(valid_margins)}",
                context={"valid_margins": valid_margins}
            )
        return True

    @staticmethod
    def validate_layout_id(layout_id: str) -> bool:
        """Validate layout ID"""
        valid_layouts = [
            'hero_section', 'grid_2col', 'grid_3col', 'grid_4col',
            'plans_layout', 'sections_layout', 'comparison_layout',
            'timeline_layout', 'asymmetric_layout', 'single_column',
            'mixed_layout', 'text_focus'
        ]
        if layout_id not in valid_layouts:
            raise ValidationException(
                f"Invalid layout. Must be one of: {', '.join(valid_layouts)}",
                context={"valid_layouts": valid_layouts}
            )
        return True

    @staticmethod
    def validate_page_number(page_number: int) -> bool:
        """Validate page number"""
        if page_number < 1:
            raise ValidationException("Page number must be at least 1")
        if page_number > 1000:
            raise ValidationException("Page number cannot exceed 1000")
        return True

    @staticmethod
    def validate_uuid(value: str, field_name: str = "ID") -> bool:
        """Validate UUID format"""
        try:
            import uuid
            uuid.UUID(value)
            return True
        except ValueError:
            raise ValidationException(f"Invalid {field_name} format")

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValidationException("Invalid email format")
        return True


# ==================== EXAMPLE USAGE ====================
"""
In route handlers, use these patterns:

1. Simple validation:
    try:
        ValidationRules.validate_portfolio_title(req.title)
    except ValidationException as e:
        raise e

2. Custom error:
    if not portfolio:
        raise ResourceNotFoundException("Portfolio", portfolio_id)

3. Authorization check:
    if portfolio.user_id != current_user.user_id:
        raise AuthorizationException()

4. Database error:
    try:
        response = supabase.table("portfolios").insert(data).execute()
    except Exception as e:
        raise DatabaseException(str(e))

5. With context:
    raise ValidationException(
        "Invalid page configuration",
        context={
            "max_pages": 1000,
            "provided": page_number
        }
    )
"""
