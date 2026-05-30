# CosmoFolio API Documentation - Phase 1
## Complete API Reference & Integration Guide

**Version**: 1.0  
**Last Updated**: 2026-05-30  
**Base URL**: `http://localhost:8000/api` (development)  
**Authentication**: Firebase Bearer Token

---

## 1. Authentication

### Header Format
```
Authorization: Bearer {firebase_token}
```

### Example
```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  http://localhost:8000/api/portfolios
```

---

## 2. Portfolios Endpoints

### POST /portfolios - Create Portfolio
Create a new portfolio with page settings.

**Authentication**: Required (Bearer token)

**Request Body**:
```json
{
  "title": "Spring 2024 Portfolio",
  "architect_name": "Jane Doe",
  "architect_bio": "Architecture student focused on sustainable design",
  "page_size": "a4",
  "page_orientation": "portrait",
  "margins": "standard"
}
```

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user123",
  "title": "Spring 2024 Portfolio",
  "architect_name": "Jane Doe",
  "architect_bio": "Architecture student...",
  "page_size": "a4",
  "page_orientation": "portrait",
  "margins": "standard",
  "is_published": false,
  "view_count": 0,
  "created_at": "2026-05-30T12:00:00Z",
  "updated_at": "2026-05-30T12:00:00Z"
}
```

**Errors**:
- 401: Missing/invalid authentication
- 400: Invalid request data (title/name required)
- 422: Validation error (invalid enum values)

---

### GET /portfolios - List User Portfolios
Get all portfolios for authenticated user.

**Authentication**: Required

**Query Parameters**: None

**Response** (200 OK):
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Spring 2024 Portfolio",
    "architect_name": "Jane Doe",
    "page_size": "a4",
    "is_published": false,
    "view_count": 0,
    "created_at": "2026-05-30T12:00:00Z",
    "updated_at": "2026-05-30T12:00:00Z"
  }
]
```

**Errors**:
- 401: Missing/invalid authentication

---

### GET /portfolios/{id} - Get Portfolio Details
Get specific portfolio (must own or be published).

**Authentication**: Required for private, not required for published

**URL Parameters**:
- `id` (string, required): Portfolio UUID

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Spring 2024 Portfolio",
  "architect_name": "Jane Doe",
  "architect_bio": "...",
  "page_size": "a4",
  "page_orientation": "portrait",
  "margins": "standard",
  "is_published": true,
  "view_count": 42,
  "created_at": "2026-05-30T12:00:00Z",
  "updated_at": "2026-05-30T12:00:00Z"
}
```

**Errors**:
- 401: Authentication required (for private portfolio)
- 403: Access denied (not owner)
- 404: Portfolio not found

---

### PUT /portfolios/{id} - Update Portfolio
Update portfolio settings.

**Authentication**: Required

**URL Parameters**:
- `id` (string, required): Portfolio UUID

**Request Body**:
```json
{
  "title": "Updated Title",
  "description": "Updated description",
  "architect_name": "Jane Doe",
  "architect_bio": "Updated bio",
  "page_size": "a3",
  "page_orientation": "landscape",
  "margins": "generous"
}
```

**Response** (200 OK): Updated portfolio object

**Errors**:
- 401: Missing/invalid authentication
- 403: Access denied (not owner)
- 404: Portfolio not found

---

### DELETE /portfolios/{id} - Delete Portfolio
Permanently delete portfolio and all contents.

**Authentication**: Required

**URL Parameters**:
- `id` (string, required): Portfolio UUID

**Response** (204 No Content): Empty response

**Errors**:
- 401: Missing/invalid authentication
- 403: Access denied (not owner)
- 404: Portfolio not found

---

### GET /portfolios/{id}/settings - Get Portfolio Settings
Get all settings for a portfolio.

**Authentication**: Required

**Response** (200 OK): Complete portfolio object with all settings

**Errors**:
- 401: Missing/invalid authentication
- 403: Access denied
- 404: Portfolio not found

---

### PUT /portfolios/{id}/settings - Update Settings
Update specific portfolio settings.

**Authentication**: Required

**Request Body**:
```json
{
  "page_size": "a3",
  "page_orientation": "landscape",
  "margins": "generous"
}
```

**Response** (200 OK): Updated portfolio object

---

### GET /portfolios/{id}/public - View Published Portfolio
Access published portfolio without authentication.

**Authentication**: Not required

**Response** (200 OK): Portfolio object (if published)

**Errors**:
- 404: Portfolio not found or not published

---

## 3. Portfolio Pages Endpoints

### POST /portfolios/{portfolio_id}/pages - Create Page
Create a new page in portfolio.

**Authentication**: Required

**URL Parameters**:
- `portfolio_id` (string): Portfolio UUID

**Request Body**:
```json
{
  "page_number": 1,
  "page_type": "cover",
  "layout_id": "hero_section",
  "title": "Cover Page",
  "description": "Portfolio cover",
  "layout_config": {
    "spacing": 40,
    "alignment": "center"
  },
  "asset_ids": [],
  "style_override_id": null
}
```

**Response** (200 OK):
```json
{
  "id": "page-uuid-123",
  "portfolio_id": "portfolio-uuid",
  "page_number": 1,
  "page_type": "cover",
  "layout_id": "hero_section",
  "title": "Cover Page",
  "layout_config": {...},
  "asset_ids": [],
  "created_at": "2026-05-30T12:00:00Z"
}
```

**Errors**:
- 401: Missing/invalid authentication
- 403: Access denied
- 404: Portfolio not found
- 400: Invalid layout_id or page_type

---

### GET /portfolios/{portfolio_id}/pages - List Pages
Get all pages in portfolio, ordered by page number.

**Authentication**: Required

**Response** (200 OK): Array of page objects

---

### GET /portfolios/{portfolio_id}/pages/{page_num} - Get Page
Get specific page.

**Authentication**: Required

**URL Parameters**:
- `portfolio_id` (string): Portfolio UUID
- `page_num` (integer): Page number (1-1000)

**Response** (200 OK): Page object

**Errors**:
- 404: Page not found

---

### PUT /portfolios/{portfolio_id}/pages/{page_num} - Update Page
Update page configuration.

**Authentication**: Required

**Request Body** (all fields optional):
```json
{
  "page_type": "content",
  "layout_id": "grid_3col",
  "title": "Projects Page",
  "description": "Featured projects",
  "layout_config": {...},
  "asset_ids": ["asset-1", "asset-2"],
  "style_override_id": null
}
```

**Response** (200 OK): Updated page object

---

### DELETE /portfolios/{portfolio_id}/pages/{page_num} - Delete Page
Remove page from portfolio.

**Authentication**: Required

**Response** (204 No Content)

---

### PUT /portfolios/{portfolio_id}/pages/order - Reorder Pages
Reorder all pages in portfolio.

**Authentication**: Required

**Request Body**:
```json
{
  "pages": [
    {"page_number": 2, "order": 1},
    {"page_number": 1, "order": 2},
    {"page_number": 3, "order": 3}
  ]
}
```

**Response** (200 OK): Array of updated pages

---

### PUT /portfolios/{portfolio_id}/pages/{page_num}/assets - Assign Assets
Assign and position assets on a page.

**Authentication**: Required

**Request Body**:
```json
{
  "asset_ids": ["asset-1", "asset-2", "asset-3"],
  "asset_positions": {
    "asset-1": {"x": 0, "y": 0, "width": 50, "height": 50},
    "asset-2": {"x": 50, "y": 0, "width": 50, "height": 50}
  }
}
```

**Response** (200 OK): Updated page object

---

## 4. Layouts Endpoints

### GET /layouts/available - List All Layouts
Get all available layout templates.

**Authentication**: Not required

**Response** (200 OK):
```json
{
  "layouts": [
    {
      "id": "hero_section",
      "name": "Hero Section",
      "description": "Full-width image with title overlay",
      "asset_types": ["render"],
      "max_assets": 1,
      "config": {
        "grid_columns": 1,
        "image_aspect_ratio": "cover",
        "spacing": {"top": 0, "bottom": 40}
      }
    },
    {
      "id": "grid_2col",
      "name": "2-Column Grid",
      "description": "2-column equal width grid",
      "asset_types": ["render", "plan", "section"],
      "max_assets": 4,
      "config": {
        "grid_columns": 2,
        "image_aspect_ratio": "auto",
        "spacing": {"gap": 20}
      }
    }
    // ... 10 more layouts
  ],
  "total": 12
}
```

---

### GET /layouts/{layout_id} - Get Layout Details
Get specific layout template details.

**Authentication**: Not required

**URL Parameters**:
- `layout_id` (string): Layout ID (e.g., "grid_3col")

**Response** (200 OK): Single layout object

**Errors**:
- 404: Layout not found

---

## 5. Layout Templates Reference

### Available Layouts

1. **hero_section** - Full-width hero with overlay
   - Max assets: 1
   - Asset types: render
   - Columns: 1
   - Aspect ratio: cover

2. **grid_2col** - 2-column equal width
   - Max assets: 4
   - Asset types: render, plan, section
   - Columns: 2
   - Gap: 20px

3. **grid_3col** - 3-column equal width
   - Max assets: 6
   - Asset types: render, diagram
   - Columns: 3
   - Gap: 20px

4. **grid_4col** - 4-column equal width
   - Max assets: 8
   - Asset types: render, diagram, detail
   - Columns: 4
   - Gap: 15px

5. **plans_layout** - Large plan with secondary
   - Max assets: 2
   - Asset types: plan, section
   - Columns: 1
   - Gap: 30px

6. **sections_layout** - Multiple sections horizontal
   - Max assets: 4
   - Asset types: section, diagram
   - Columns: 2
   - Gap: 20px

7. **comparison_layout** - Side-by-side comparison
   - Max assets: 2
   - Asset types: render, plan
   - Columns: 2
   - Gap: 30px

8. **timeline_layout** - Chronological process
   - Max assets: 6
   - Asset types: render, diagram, detail
   - Columns: 2
   - Gap: 20px

9. **asymmetric_layout** - Dynamic unequal layout
   - Max assets: 5
   - Asset types: render, plan
   - Columns: 3
   - Gap: 20px

10. **single_column** - Large centered image
    - Max assets: 1
    - Asset types: render, plan, section
    - Columns: 1
    - Gap: vertical 40px

11. **mixed_layout** - Image + diagram combo
    - Max assets: 4
    - Asset types: render, diagram
    - Columns: 2
    - Gap: 25px

12. **text_focus** - Text-heavy with image
    - Max assets: 1
    - Asset types: render
    - Columns: 2
    - Gap: 30px

---

## 6. Enum Values Reference

### Page Size (page_size)
- `a4` - A4 (210×297mm)
- `a3` - A3 (297×420mm)
- `letter` - Letter (8.5×11")
- `tabloid` - Tabloid (11×17")
- `custom` - Custom dimensions

### Orientation (page_orientation)
- `portrait` - Vertical orientation
- `landscape` - Horizontal orientation

### Margins (margins)
- `compact` - 10-15mm
- `standard` - 20-25mm (recommended)
- `generous` - 30-40mm

### Page Type (page_type)
- `cover` - Cover/title page
- `project` - Project showcase
- `content` - Content page
- `credits` - Credits/acknowledgments
- `blank` - Blank page

---

## 7. Error Responses

### Format
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "status_code": 400,
    "timestamp": "2026-05-30T12:00:00Z",
    "context": {}
  }
}
```

### Common Errors

**401 Unauthorized** - Missing/invalid authentication
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or missing authentication",
    "status_code": 401
  }
}
```

**403 Forbidden** - Access denied
```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Access denied",
    "status_code": 403
  }
}
```

**404 Not Found** - Resource missing
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Portfolio 'abc123' not found",
    "status_code": 404
  }
}
```

**400 Bad Request** - Invalid data
```json
{
  "error": {
    "code": "BAD_REQUEST",
    "message": "Invalid page size. Must be one of: a4, a3, letter, tabloid, custom",
    "status_code": 400,
    "context": {
      "valid_sizes": ["a4", "a3", "letter", "tabloid", "custom"]
    }
  }
}
```

**422 Validation Error** - Pydantic validation failure
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "status_code": 422,
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

---

## 8. Integration Examples

### Example: Create Portfolio Flow
```bash
# 1. Create portfolio
curl -X POST http://localhost:8000/api/portfolios \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Portfolio",
    "architect_name": "Jane Doe",
    "page_size": "a4",
    "page_orientation": "portrait",
    "margins": "standard"
  }'

# Response: Portfolio object with ID

# 2. Create first page
curl -X POST http://localhost:8000/api/portfolios/{portfolio_id}/pages \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "page_number": 1,
    "page_type": "cover",
    "layout_id": "hero_section"
  }'

# 3. Create second page
curl -X POST http://localhost:8000/api/portfolios/{portfolio_id}/pages \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "page_number": 2,
    "page_type": "content",
    "layout_id": "grid_3col"
  }'

# 4. Update portfolio settings
curl -X PUT http://localhost:8000/api/portfolios/{portfolio_id}/settings \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "page_size": "a3",
    "page_orientation": "landscape"
  }'
```

---

## 9. Rate Limiting

Currently no rate limiting implemented in Phase 1.  
Recommended for Phase 2: 100 requests/minute per user

---

## 10. CORS Configuration

### Allowed Origins
- `http://localhost:3000` (development)
- `http://localhost:3001` (development)

### Allowed Methods
- GET, POST, PUT, DELETE, OPTIONS

### Allowed Headers
- Content-Type
- Authorization

---

## 11. Pagination (Future Phase)

Not implemented in Phase 1.  
Recommended structure for Phase 2:

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

---

## 12. Deployment

### Environment Variables
```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=xxxx
FIREBASE_CREDENTIALS_JSON={...}
```

### Docker
```bash
docker build -t cosmfolio-api .
docker run -p 8000:8000 cosmfolio-api
```

### Health Check
```bash
curl http://localhost:8000/health
```

---

## API Summary Table

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /portfolios | ✓ | Create portfolio |
| GET | /portfolios | ✓ | List user portfolios |
| GET | /portfolios/{id} | ✓ | Get portfolio |
| PUT | /portfolios/{id} | ✓ | Update portfolio |
| DELETE | /portfolios/{id} | ✓ | Delete portfolio |
| GET | /portfolios/{id}/settings | ✓ | Get settings |
| PUT | /portfolios/{id}/settings | ✓ | Update settings |
| GET | /portfolios/{id}/public | ✗ | View published |
| POST | /portfolios/{id}/pages | ✓ | Create page |
| GET | /portfolios/{id}/pages | ✓ | List pages |
| GET | /portfolios/{id}/pages/{num} | ✓ | Get page |
| PUT | /portfolios/{id}/pages/{num} | ✓ | Update page |
| DELETE | /portfolios/{id}/pages/{num} | ✓ | Delete page |
| PUT | /portfolios/{id}/pages/order | ✓ | Reorder pages |
| PUT | /portfolios/{id}/pages/{num}/assets | ✓ | Assign assets |
| GET | /layouts/available | ✗ | List layouts |
| GET | /layouts/{id} | ✗ | Get layout |

---

**Documentation Version**: 1.0  
**Last Updated**: 2026-05-30  
**Status**: Complete for Phase 1
