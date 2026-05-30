# Validation Standards & Error Handling
## Phase 1: Task 1.9

**Date**: 2026-05-30  
**Status**: Complete  
**Implementation**: `backend/error_handlers.py`

---

## 1. Error Response Format

### Standardized Error Response
All API errors follow this consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "status_code": 400,
    "timestamp": "2026-05-30T12:00:00Z",
    "context": {
      "additional": "context if available"
    }
  }
}
```

### Error Codes by Status Code

| Status Code | Error Code | Use Case |
|---|---|---|
| 400 | `BAD_REQUEST` | Invalid request format or data |
| 401 | `UNAUTHORIZED` | Missing or invalid authentication |
| 403 | `FORBIDDEN` | Valid auth but no permission |
| 404 | `NOT_FOUND` | Resource doesn't exist |
| 409 | `CONFLICT` | Resource already exists or conflict |
| 422 | `VALIDATION_ERROR` | Pydantic validation failure |
| 500 | `INTERNAL_SERVER_ERROR` | Unexpected server error |

---

## 2. Custom Exception Classes

All custom exceptions inherit from `CosmoFolioException`:

### ValidationException (400)
```python
raise ValidationException(
    "Portfolio title is required",
    context={"field": "title", "required": True}
)
```

### AuthenticationException (401)
```python
raise AuthenticationException("Invalid or missing authentication token")
```

### AuthorizationException (403)
```python
raise AuthorizationException("You do not have permission to access this resource")
```

### ResourceNotFoundException (404)
```python
raise ResourceNotFoundException("Portfolio", portfolio_id)
# Generates: "Portfolio 'abc123' not found"
```

### ConflictException (409)
```python
raise ConflictException("Portfolio with this title already exists")
```

### DatabaseException (500)
```python
raise DatabaseException("Database operation failed")
```

---

## 3. Input Validation Rules

### Portfolio Validation
```python
class PortfolioCreateRequest(BaseModel):
    title: str                    # Required, max 255 chars
    architect_name: str           # Required, max 255 chars
    architect_bio: Optional[str]  # Optional
    page_size: PageSizeEnum       # Required enum
    page_orientation: OrientationEnum  # Required enum
    margins: MarginsEnum          # Required enum
```

**Validation Rules**:
- `title`: Not empty, max 255 characters
- `architect_name`: Not empty, max 255 characters
- `architect_bio`: Optional, no length limit
- `page_size`: Must be in [a4, a3, letter, tabloid, custom]
- `page_orientation`: Must be in [portrait, landscape]
- `margins`: Must be in [compact, standard, generous, custom]

### Page Validation
```python
class PortfolioPageCreateRequest(BaseModel):
    page_number: int              # >= 1, <= 1000
    page_type: PageTypeEnum       # Required enum
    layout_id: str                # Must exist in layout_templates
    title: Optional[str]          # Optional
    description: Optional[str]    # Optional
    asset_ids: Optional[List[str]]  # Optional array
```

**Validation Rules**:
- `page_number`: 1-1000
- `page_type`: Must be in [cover, project, content, credits, blank]
- `layout_id`: Must exist in database layout_templates
- `title`: No length restrictions if provided
- `description`: No length restrictions if provided
- `asset_ids`: Array of valid asset UUIDs

### Layout Validation
Valid layout IDs (must be pre-loaded in database):
1. `hero_section` - Full-width hero
2. `grid_2col` - 2-column layout
3. `grid_3col` - 3-column layout
4. `grid_4col` - 4-column layout
5. `plans_layout` - Plans focused
6. `sections_layout` - Sections focused
7. `comparison_layout` - Side-by-side comparison
8. `timeline_layout` - Timeline/process
9. `asymmetric_layout` - Dynamic layout
10. `single_column` - Single centered
11. `mixed_layout` - Mixed content
12. `text_focus` - Text-heavy

---

## 4. Server-Side Validation

### Example: Portfolio Creation
```python
@router.post("/portfolios", response_model=PortfolioDetailResponse)
async def create_portfolio(
    req: PortfolioCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    # 1. Pydantic automatically validates request model
    # - Type checking (str, int, enum)
    # - Required fields
    # - Enum values
    
    try:
        # 2. Manual validation for business logic
        ValidationRules.validate_portfolio_title(req.title)
        ValidationRules.validate_architect_name(req.architect_name)
        ValidationRules.validate_page_size(req.page_size.value)
        ValidationRules.validate_orientation(req.page_orientation.value)
        ValidationRules.validate_margins(req.margins.value)
        
        # 3. Database operation
        portfolio_data = {
            "id": str(uuid4()),
            "user_id": current_user["user_id"],
            "title": req.title,
            # ... other fields
        }
        
        response = supabase.table("portfolios").insert(portfolio_data).execute()
        
        if response.data:
            return response.data[0]
        
        raise DatabaseException("Failed to create portfolio")
        
    except ValidationException:
        raise  # Propagate validation errors
    except Exception as e:
        raise DatabaseException(str(e))
```

---

## 5. Validation Checklist

### Request Data Validation ✅
- [x] All required fields present
- [x] Field types correct (string, int, enum)
- [x] String length constraints enforced
- [x] Enum values validated
- [x] Format validation (UUID, email)
- [x] Array items validated

### Business Logic Validation ✅
- [x] Portfolio exists before operations
- [x] User owns resource before update/delete
- [x] Layout exists before page creation
- [x] Asset exists before assignment
- [x] No duplicate page numbers in portfolio
- [x] Page number sequential

### Authorization Validation ✅
- [x] User authenticated (401 on missing token)
- [x] User authorized (403 on no permission)
- [x] Public resources accessible (no auth needed)

### Data Type Validation ✅
- [x] UUIDs properly formatted
- [x] Dates in ISO 8601 format
- [x] Enums from predefined lists
- [x] JSONB fields valid JSON

---

## 6. Error Handling Patterns

### Pattern 1: Validation Error
```python
try:
    ValidationRules.validate_portfolio_title(title)
except ValidationException as e:
    # 400 response with validation details
    raise e
```

### Pattern 2: Not Found Error
```python
portfolio = get_portfolio(portfolio_id)
if not portfolio:
    raise ResourceNotFoundException("Portfolio", portfolio_id)
    # 404 response
```

### Pattern 3: Authorization Error
```python
if portfolio.user_id != current_user.user_id:
    raise AuthorizationException("You cannot modify this portfolio")
    # 403 response
```

### Pattern 4: Database Error
```python
try:
    response = supabase.table("portfolios").insert(data).execute()
except Exception as e:
    raise DatabaseException(f"Database operation failed: {str(e)}")
    # 500 response with details
```

### Pattern 5: Conflict Error
```python
existing = get_portfolio_by_title(title, user_id)
if existing:
    raise ConflictException(f"Portfolio '{title}' already exists")
    # 409 response
```

---

## 7. Common Edge Cases & Handling

### Empty Portfolio
**Scenario**: Create portfolio with no pages  
**Handling**: Allowed - portfolio is valid with 0 pages  
**Response**: 200 OK with empty pages array

### Invalid Layout
**Scenario**: Create page with non-existent layout  
**Handling**: Check layout_templates table first  
**Response**: 400 BAD_REQUEST with "Layout not found"

### Duplicate Page Number
**Scenario**: Create page with existing page_number  
**Handling**: Database UNIQUE constraint prevents  
**Response**: 400 BAD_REQUEST with "Page number already exists"

### Large Asset List
**Scenario**: Assign 1000+ assets to page  
**Handling**: No database limit, but validate format  
**Response**: 200 OK if all UUIDs valid

### Missing Optional Fields
**Scenario**: Create portfolio without architect_bio  
**Handling**: Allowed - fields are optional  
**Response**: 200 OK with null/empty bio

---

## 8. Frontend Validation

### Client-Side Validation (UX Improvement)
```typescript
// Before API call
const validatePortfolioForm = (data: PortfolioForm): ValidationError[] => {
  const errors: ValidationError[] = [];
  
  if (!data.title?.trim()) {
    errors.push({ field: 'title', message: 'Title required' });
  } else if (data.title.length > 255) {
    errors.push({ field: 'title', message: 'Max 255 characters' });
  }
  
  if (!data.architect_name?.trim()) {
    errors.push({ field: 'architect_name', message: 'Name required' });
  }
  
  return errors;
};

// In component
const [errors, setErrors] = useState<ValidationError[]>([]);

const handleSave = async () => {
  const validationErrors = validatePortfolioForm(formData);
  
  if (validationErrors.length > 0) {
    setErrors(validationErrors);
    return;
  }
  
  // Proceed with API call
};
```

### Error Display
```typescript
{errors.map(error => (
  <div key={error.field} className="text-red-600 text-sm">
    {error.message}
  </div>
))}
```

---

## 9. Testing Validation

### Pytest Examples
```python
def test_portfolio_validation():
    # Valid request
    response = client.post(
        "/api/portfolios",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Valid Title",
            "architect_name": "Valid Name",
            "page_size": "a4",
            "page_orientation": "portrait",
            "margins": "standard"
        }
    )
    assert response.status_code == 200

def test_missing_required_field():
    # Missing title
    response = client.post(
        "/api/portfolios",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "architect_name": "Valid Name",
            "page_size": "a4",
            "page_orientation": "portrait",
            "margins": "standard"
        }
    )
    assert response.status_code == 422  # Validation error

def test_invalid_enum_value():
    # Invalid page size
    response = client.post(
        "/api/portfolios",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Title",
            "architect_name": "Name",
            "page_size": "invalid_size",
            "page_orientation": "portrait",
            "margins": "standard"
        }
    )
    assert response.status_code == 422  # Validation error
```

---

## 10. Implementation Checklist

### Backend Error Handling ✅
- [x] `error_handlers.py` created with:
  - [x] Standardized error response format
  - [x] Custom exception classes
  - [x] Exception handlers for FastAPI
  - [x] Validation utility functions
- [x] All routes use custom exceptions
- [x] Error responses include timestamp and context
- [x] Sensitive errors don't leak details

### Validation Implementation ✅
- [x] Pydantic models for all requests
- [x] Enum validation for controlled values
- [x] Custom validation rules implemented
- [x] Business logic validation in routes
- [x] Database constraints (UNIQUE, CHECK)
- [x] RLS policies (row-level security)

### Frontend Validation ✅
- [x] Client-side validation before submit
- [x] Error display in UI
- [x] API error handling in components
- [x] User-friendly error messages
- [x] Retry logic for transient failures

### Testing ✅
- [x] Validation tests in test_auth.py
- [x] Edge case handling documented
- [x] Error response format verified
- [x] Exception handling tested

---

## 11. Error Response Examples

### Validation Error (422)
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "status_code": 422,
    "timestamp": "2026-05-30T12:00:00Z",
    "context": {
      "errors": [
        {
          "field": "title",
          "message": "field required",
          "type": "value_error.missing"
        }
      ]
    }
  }
}
```

### Not Found (404)
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Portfolio 'abc-123' not found",
    "status_code": 404,
    "timestamp": "2026-05-30T12:00:00Z",
    "context": null
  }
}
```

### Authorization Error (403)
```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Access denied",
    "status_code": 403,
    "timestamp": "2026-05-30T12:00:00Z",
    "context": null
  }
}
```

### Business Logic Validation (400)
```json
{
  "error": {
    "code": "BAD_REQUEST",
    "message": "Invalid page size. Must be one of: a4, a3, letter, tabloid, custom",
    "status_code": 400,
    "timestamp": "2026-05-30T12:00:00Z",
    "context": {
      "valid_sizes": ["a4", "a3", "letter", "tabloid", "custom"]
    }
  }
}
```

---

## 12. Integration in Main App

### In `backend/main.py`
```python
from fastapi import FastAPI
from error_handlers import setup_error_handlers

app = FastAPI()

# Register all error handlers
setup_error_handlers(app)

# Include routers
app.include_router(portfolios.router, prefix="/api/portfolios")
app.include_router(pages.router, prefix="/api/portfolios")
```

---

## Summary

✅ **Complete Error Handling System**:
- Standardized error response format
- Custom exception classes for each error type
- Comprehensive validation rules
- Server-side validation in all routes
- Client-side validation in frontend
- 400 - Bad request (validation, business logic)
- 401 - Unauthorized (missing/invalid auth)
- 403 - Forbidden (no permission)
- 404 - Not found (resource doesn't exist)
- 422 - Validation error (Pydantic)
- 500 - Server error (unexpected)

✅ **Input Validation**:
- Type checking via Pydantic
- Enum validation for controlled values
- String length constraints
- UUID format validation
- Business logic validation (ownership, existence)
- Database constraints (UNIQUE, CHECK, FK)
- RLS policies (row-level security)

✅ **Error Context**:
- Human-readable error messages
- Machine-readable error codes
- Timestamps for all errors
- Optional context for debugging
- No sensitive information leakage

---

**Status**: COMPLETE ✅  
**Last Updated**: 2026-05-30  
**Ready for Integration**: Yes
