# Phase 2: Asset Management System - Implementation Plan

**Phase**: 2 of 7  
**Date**: 2026-05-30  
**Status**: Planning  
**Dependencies**: Phase 1 Complete ✅

---

## 📋 Phase 2 Overview

**Goal**: Implement complete asset management system including upload, storage, optimization, and organization.

**Key Features**:
- Asset upload (images, renderings, plans, diagrams, details)
- Asset organization by project and type
- Image optimization and CDN delivery
- Asset tagging and metadata
- Asset preview generation
- Asset versioning and history
- Bulk operations

---

## 🎯 Phase 2 Tasks (10 tasks, 2-3 weeks)

### Task 2.1: Asset Model & Database Schema
**Duration**: 1-2 days  
**Deliverables**:
- Asset table schema with metadata
- Asset version history table
- Asset tags table (many-to-many)
- File storage configuration
- Pydantic models for asset operations
- Database migrations for asset tables

**Key Tables**:
```
assets:
  - id (UUID)
  - project_id (FK)
  - portfolio_id (FK)
  - file_name
  - file_size
  - file_type (render, plan, section, diagram, detail)
  - mime_type
  - storage_path (S3/storage path)
  - thumb_path (thumbnail)
  - width, height (dimensions)
  - created_at, updated_at

asset_versions:
  - id (UUID)
  - asset_id (FK)
  - version_number
  - file_path
  - file_size
  - created_at

asset_tags:
  - id (UUID)
  - asset_id (FK)
  - tag_name
  - created_at
```

---

### Task 2.2: File Storage Integration
**Duration**: 2-3 days  
**Deliverables**:
- S3/Supabase Storage client setup
- File upload handler
- Virus scanning integration
- Thumbnail generation
- Image optimization (multiple sizes)
- CDN configuration

**Storage Strategy**:
```
s3://cosmfolio-prod/
├── portfolios/{portfolio_id}/
│   ├── assets/{asset_id}/
│   │   ├── original.{ext}
│   │   ├── thumb-250.jpg
│   │   ├── thumb-500.jpg
│   │   ├── preview-1200.jpg
│   │   └── metadata.json
```

---

### Task 2.3: Asset Upload APIs
**Duration**: 2-3 days  
**Deliverables**:
- POST /portfolios/{id}/assets (multipart upload)
- POST /portfolios/{id}/assets/bulk (batch upload)
- GET /portfolios/{id}/assets (list with filters)
- GET /portfolios/{id}/assets/{asset_id} (get metadata)
- PUT /portfolios/{id}/assets/{asset_id} (update metadata/tags)
- DELETE /portfolios/{id}/assets/{asset_id} (delete asset)
- GET /portfolios/{id}/assets/{asset_id}/versions (version history)

**Features**:
- Progress tracking for uploads
- Resumable uploads for large files
- Virus scanning before storage
- Automatic thumbnail generation
- Metadata extraction (EXIF, dimensions)
- Tag management
- Size validation (max 100MB per file)

---

### Task 2.4: Asset Organization & Search
**Duration**: 2 days  
**Deliverables**:
- Asset tagging system
- Filter by type (render, plan, section, diagram, detail)
- Filter by date range
- Search by filename and tags
- Sort by date, size, name
- Collections/folders system (optional)

**Search API**:
```
GET /portfolios/{id}/assets?
  type=render&
  tag=exterior&
  sort=created_at&
  limit=20
```

---

### Task 2.5: Asset Preview & Thumbnails
**Duration**: 1-2 days  
**Deliverables**:
- Automatic thumbnail generation
- Multiple sizes (250px, 500px, 1200px)
- Lazy loading support
- Blur-up placeholder generation
- Preview endpoints

**Endpoints**:
```
GET /assets/{asset_id}/thumb?size=250
GET /assets/{asset_id}/preview?width=1200
GET /assets/{asset_id}/original
```

---

### Task 2.6: Image Optimization
**Duration**: 2 days  
**Deliverables**:
- Auto-resize images to web-friendly sizes
- WebP conversion option
- Compression optimization
- EXIF data handling
- Progressive JPEG support
- Lazy loading implementation

---

### Task 2.7: Asset Versioning
**Duration**: 1 day  
**Deliverables**:
- Version history table
- Replace asset keeping old versions
- Restore previous version
- Download version history
- Auto-cleanup old versions (retention policy)

**Endpoints**:
```
GET /portfolios/{id}/assets/{asset_id}/versions
POST /portfolios/{id}/assets/{asset_id}/versions/{num}/restore
```

---

### Task 2.8: Frontend Asset Manager
**Duration**: 3-4 days  
**Deliverables**:
- Asset upload UI (drag-and-drop)
- Asset list/grid view
- Asset editor (metadata, tags)
- Bulk upload interface
- Progress indicators
- Asset library modal

**Components**:
- AssetUploader (drag-drop, file picker)
- AssetGrid (thumbnail grid view)
- AssetList (table view)
- AssetModal (preview and metadata)
- TagInput (tag management)

---

### Task 2.9: Asset Caching & CDN
**Duration**: 1-2 days  
**Deliverables**:
- CDN URL generation
- Cache headers optimization
- CloudFront/Cloudflare integration
- Cache invalidation on delete/update
- Bandwidth monitoring

---

### Task 2.10: Phase 2 Testing & Documentation
**Duration**: 2 days  
**Deliverables**:
- Test suite for all asset operations
- API documentation
- Upload flow testing
- Storage integration testing
- Performance benchmarking
- User guide for asset management

---

## 📊 Phase 2 Architecture

```
Frontend (React)
├── Pages
│   └── AssetLibrary
│       ├── AssetUploader
│       ├── AssetGrid/List
│       ├── AssetFilters
│       └── AssetModal
└── Hooks
    └── useAssets (upload, list, delete)

Backend (FastAPI)
├── routes/assets.py (9 endpoints)
├── services/storage.py (S3 integration)
├── services/image.py (optimization)
├── models/asset.py (Pydantic models)
└── utils/files.py (helpers)

Database (Supabase)
├── assets (main table)
├── asset_versions (history)
├── asset_tags (many-to-many)
└── Indexes on type, created_at, tags
```

---

## 🔄 Data Flow

### Upload Flow
```
User selects file
    ↓
Frontend validates (size, type)
    ↓
Generate presigned S3 URL
    ↓
Upload to S3 with progress
    ↓
Generate thumbnail & preview
    ↓
Extract metadata (EXIF, dimensions)
    ↓
Save to database
    ↓
Return asset object to UI
```

### Retrieval Flow
```
User requests asset list
    ↓
Query with filters (type, tags, date)
    ↓
Return paginated results with thumbnails
    ↓
Frontend displays grid/list
    ↓
On click → Load full asset modal
    ↓
Show preview, metadata, versions
```

---

## 🎯 Success Criteria

✅ Upload files up to 100MB  
✅ Automatic thumbnail generation  
✅ Search and filter working  
✅ Versioning functional  
✅ CDN delivery optimized  
✅ Upload progress visible  
✅ 90%+ frontend test coverage  
✅ <500ms API responses  
✅ Complete documentation  
✅ Security verified (virus scan, access control)  

---

## 📦 Dependencies

- **Backend**: Pillow (image processing), boto3 (S3), async file handling
- **Frontend**: react-dropzone (drag-drop), sharp.js (thumbnails)
- **Infrastructure**: S3/Supabase Storage, CDN, image processing service

---

## 🗓️ Timeline

| Task | Duration | Start | End |
|------|----------|-------|-----|
| 2.1: Models | 1-2d | May 30 | Jun 1 |
| 2.2: Storage | 2-3d | Jun 1 | Jun 4 |
| 2.3: APIs | 2-3d | Jun 4 | Jun 7 |
| 2.4: Search | 2d | Jun 7 | Jun 9 |
| 2.5: Previews | 1-2d | Jun 9 | Jun 11 |
| 2.6: Optimization | 2d | Jun 11 | Jun 13 |
| 2.7: Versioning | 1d | Jun 13 | Jun 14 |
| 2.8: Frontend | 3-4d | Jun 14 | Jun 18 |
| 2.9: CDN | 1-2d | Jun 18 | Jun 20 |
| 2.10: Testing | 2d | Jun 20 | Jun 22 |

**Total**: ~2-3 weeks

---

## 🔐 Security Considerations

- ✅ File type validation (whitelist only image types)
- ✅ Virus scanning on upload
- ✅ File size limits (100MB max)
- ✅ Access control (only portfolio owner can upload)
- ✅ Secure URLs with expiration
- ✅ No direct file access (through API only)
- ✅ EXIF data sanitization
- ✅ Storage encryption at rest

---

## 💾 Storage Estimates

Assuming 100 projects × 20 assets × 2MB average:
- **Raw storage**: ~4GB
- **With thumbnails**: ~6GB
- **With backups**: ~12GB
- **Monthly cost**: ~$50 (S3/Supabase)

---

## Next Steps

1. Create Asset model and Pydantic definitions
2. Design database schema for assets and versions
3. Set up S3/Storage client
4. Implement file upload handler
5. Create API endpoints for CRUD operations

**Ready to begin Task 2.1!** 🚀

---

**Phase 2 Plan Version**: 1.0  
**Last Updated**: 2026-05-30  
**Status**: Ready to Implement
