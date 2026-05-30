"""
Asset management API endpoints
Phase 2: Task 2.3 - Upload, list, update, delete assets
"""

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Query, Form
from typing import List, Optional
from datetime import datetime
from uuid import uuid4

from models import (
    AssetUploadRequest,
    AssetMetadataRequest,
    AssetResponse,
    AssetListResponse,
    AssetVersionResponse,
    AssetVersionListResponse,
    BulkAssetUploadResponse,
)
from routes.deps import get_current_user
from services.storage import get_storage_client
from services.upload import get_upload_manager
from database import supabase
from error_handlers import (
    ResourceNotFoundException,
    AuthorizationException,
    ValidationException,
    DatabaseException,
)

router = APIRouter()

# ==================== ASSET UPLOAD ====================

@router.post("/{portfolio_id}/assets", response_model=AssetResponse)
async def upload_asset(
    portfolio_id: str,
    file: UploadFile = File(...),
    asset_type: str = Form("render"),
    tags: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """Upload single asset file"""
    try:
        # Verify portfolio ownership
        portfolio = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()

        if not portfolio.data:
            raise ResourceNotFoundException("Portfolio", portfolio_id)

        if portfolio.data[0]["user_id"] != current_user["user_id"]:
            raise AuthorizationException()

        # Validate asset type
        valid_types = ["render", "plan", "section", "diagram", "detail", "material"]
        if asset_type not in valid_types:
            raise ValidationException(
                f"Invalid asset_type. Must be one of: {', '.join(valid_types)}",
                context={"valid_types": valid_types}
            )

        # Generate asset ID
        asset_id = str(uuid4())
        upload_manager = get_upload_manager()

        # Upload file
        upload_result = await upload_manager.upload_file(
            file,
            portfolio_id,
            asset_id,
            asset_type
        )

        # Parse tags
        tag_list = []
        if tags:
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]

        # Create asset record
        asset_data = {
            "id": asset_id,
            "user_id": current_user["user_id"],
            "portfolio_id": portfolio_id,
            "file_name": file.filename,
            "original_file_name": file.filename,
            "file_size": upload_result["file_size"],
            "mime_type": upload_result["mime_type"],
            "asset_type": asset_type,
            "storage_path": upload_result["storage_path"],
            "thumb_path": upload_result["thumb_path"],
            "preview_path": upload_result["preview_path"],
            "width": upload_result["width"],
            "height": upload_result["height"],
            "aspect_ratio": upload_result["aspect_ratio"],
            "description": description,
            "exif_data": upload_result["metadata"].get("exif", {}),
            "upload_status": "completed",
            "thumbnail_status": "completed",
            "version": 1,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Insert asset
        response = supabase.table("assets").insert(asset_data).execute()

        if not response.data:
            raise DatabaseException("Failed to create asset record")

        asset = response.data[0]

        # Insert tags
        if tag_list:
            tag_data = [
                {
                    "id": str(uuid4()),
                    "asset_id": asset_id,
                    "tag_name": tag,
                    "created_at": datetime.utcnow().isoformat(),
                }
                for tag in tag_list
            ]
            supabase.table("asset_tags").insert(tag_data).execute()

        # Return asset with tags
        return {
            **asset,
            "tags": tag_list,
            "preview_url": upload_result["storage_path"],
        }

    except (ResourceNotFoundException, AuthorizationException, ValidationException, DatabaseException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==================== BATCH UPLOAD ====================

@router.post("/{portfolio_id}/assets/bulk", response_model=BulkAssetUploadResponse)
async def bulk_upload_assets(
    portfolio_id: str,
    files: List[UploadFile] = File(...),
    asset_type: str = Form("render"),
    current_user: dict = Depends(get_current_user)
):
    """Upload multiple assets at once"""
    try:
        # Verify portfolio ownership
        portfolio = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()

        if not portfolio.data:
            raise ResourceNotFoundException("Portfolio", portfolio_id)

        if portfolio.data[0]["user_id"] != current_user["user_id"]:
            raise AuthorizationException()

        # Upload batch
        upload_manager = get_upload_manager()
        results = await upload_manager.upload_batch(files, portfolio_id, asset_type)

        return BulkAssetUploadResponse(
            uploaded=results["uploaded"],
            failed=results["failed"],
            total=results["total"],
            errors=results["errors"] if results["errors"] else None,
        )

    except (ResourceNotFoundException, AuthorizationException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==================== LIST ASSETS ====================

@router.get("/{portfolio_id}/assets", response_model=AssetListResponse)
async def list_assets(
    portfolio_id: str,
    asset_type: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    sort_by: str = Query("created_at", regex="^(created_at|file_size|file_name)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """List portfolio assets with filtering and sorting"""
    try:
        # Verify portfolio ownership
        portfolio = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()

        if not portfolio.data:
            raise ResourceNotFoundException("Portfolio", portfolio_id)

        if portfolio.data[0]["user_id"] != current_user["user_id"]:
            raise AuthorizationException()

        # Build query
        query = supabase.table("assets").select("*").eq("portfolio_id", portfolio_id)

        # Apply filters
        if asset_type:
            query = query.eq("asset_type", asset_type)

        # Apply sorting
        is_desc = sort_order == "desc"
        query = query.order(sort_by, desc=is_desc)

        # Get total count
        count_response = supabase.table("assets").select("id", count="exact").eq(
            "portfolio_id", portfolio_id
        ).execute()
        total = count_response.count

        # Paginate
        offset = (page - 1) * page_size
        response = query.range(offset, offset + page_size - 1).execute()

        assets = response.data or []

        # Get tags for each asset
        for asset in assets:
            tags_response = supabase.table("asset_tags").select("tag_name").eq(
                "asset_id", asset["id"]
            ).execute()
            asset["tags"] = [t["tag_name"] for t in tags_response.data]

        # Filter by tag if specified
        if tag:
            assets = [a for a in assets if tag in a.get("tags", [])]

        total_pages = (total + page_size - 1) // page_size

        return AssetListResponse(
            items=assets,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    except (ResourceNotFoundException, AuthorizationException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==================== GET ASSET ====================

@router.get("/{portfolio_id}/assets/{asset_id}", response_model=AssetResponse)
async def get_asset(
    portfolio_id: str,
    asset_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get asset details with metadata and tags"""
    try:
        # Verify portfolio ownership
        portfolio = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()

        if not portfolio.data:
            raise ResourceNotFoundException("Portfolio", portfolio_id)

        if portfolio.data[0]["user_id"] != current_user["user_id"]:
            raise AuthorizationException()

        # Get asset
        response = supabase.table("assets").select("*").eq(
            "id", asset_id
        ).eq("portfolio_id", portfolio_id).execute()

        if not response.data:
            raise ResourceNotFoundException("Asset", asset_id)

        asset = response.data[0]

        # Get tags
        tags_response = supabase.table("asset_tags").select("tag_name").eq(
            "asset_id", asset_id
        ).execute()
        asset["tags"] = [t["tag_name"] for t in tags_response.data]

        # Get preview URL
        storage_client = get_storage_client()
        asset["preview_url"] = await storage_client.get_public_url(asset["preview_path"])

        return asset

    except (ResourceNotFoundException, AuthorizationException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==================== UPDATE ASSET ====================

@router.put("/{portfolio_id}/assets/{asset_id}", response_model=AssetResponse)
async def update_asset(
    portfolio_id: str,
    asset_id: str,
    req: AssetMetadataRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update asset metadata and tags"""
    try:
        # Verify portfolio ownership
        portfolio = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()

        if not portfolio.data:
            raise ResourceNotFoundException("Portfolio", portfolio_id)

        if portfolio.data[0]["user_id"] != current_user["user_id"]:
            raise AuthorizationException()

        # Get asset
        response = supabase.table("assets").select("*").eq(
            "id", asset_id
        ).eq("portfolio_id", portfolio_id).execute()

        if not response.data:
            raise ResourceNotFoundException("Asset", asset_id)

        # Build update data
        update_data = {
            "updated_at": datetime.utcnow().isoformat(),
        }

        if req.description is not None:
            update_data["description"] = req.description

        if req.asset_type is not None:
            valid_types = ["render", "plan", "section", "diagram", "detail", "material"]
            if req.asset_type.value not in valid_types:
                raise ValidationException(f"Invalid asset_type: {req.asset_type}")
            update_data["asset_type"] = req.asset_type.value

        # Update asset
        update_response = supabase.table("assets").update(update_data).eq(
            "id", asset_id
        ).execute()

        if not update_response.data:
            raise DatabaseException("Failed to update asset")

        asset = update_response.data[0]

        # Update tags if provided
        if req.tags is not None:
            # Delete existing tags
            supabase.table("asset_tags").delete().eq("asset_id", asset_id).execute()

            # Insert new tags
            if req.tags:
                tag_data = [
                    {
                        "id": str(uuid4()),
                        "asset_id": asset_id,
                        "tag_name": tag,
                        "created_at": datetime.utcnow().isoformat(),
                    }
                    for tag in req.tags
                ]
                supabase.table("asset_tags").insert(tag_data).execute()

            asset["tags"] = req.tags
        else:
            # Get existing tags
            tags_response = supabase.table("asset_tags").select("tag_name").eq(
                "asset_id", asset_id
            ).execute()
            asset["tags"] = [t["tag_name"] for t in tags_response.data]

        return asset

    except (ResourceNotFoundException, AuthorizationException, ValidationException, DatabaseException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==================== DELETE ASSET ====================

@router.delete("/{portfolio_id}/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    portfolio_id: str,
    asset_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete asset and all associated files"""
    try:
        # Verify portfolio ownership
        portfolio = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()

        if not portfolio.data:
            raise ResourceNotFoundException("Portfolio", portfolio_id)

        if portfolio.data[0]["user_id"] != current_user["user_id"]:
            raise AuthorizationException()

        # Get asset
        response = supabase.table("assets").select("*").eq(
            "id", asset_id
        ).eq("portfolio_id", portfolio_id).execute()

        if not response.data:
            raise ResourceNotFoundException("Asset", asset_id)

        # Delete from storage
        storage_client = get_storage_client()
        await storage_client.delete_asset(portfolio_id, asset_id)

        # Delete from database (soft delete)
        supabase.table("assets").update({
            "deleted_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", asset_id).execute()

        # Delete tags
        supabase.table("asset_tags").delete().eq("asset_id", asset_id).execute()

        # Delete uses
        supabase.table("asset_uses").delete().eq("asset_id", asset_id).execute()

    except (ResourceNotFoundException, AuthorizationException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==================== ASSET VERSIONS ====================

@router.get("/{portfolio_id}/assets/{asset_id}/versions", response_model=AssetVersionListResponse)
async def get_asset_versions(
    portfolio_id: str,
    asset_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get version history for asset"""
    try:
        # Verify portfolio ownership
        portfolio = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()

        if not portfolio.data:
            raise ResourceNotFoundException("Portfolio", portfolio_id)

        if portfolio.data[0]["user_id"] != current_user["user_id"]:
            raise AuthorizationException()

        # Get asset
        asset_response = supabase.table("assets").select("*").eq(
            "id", asset_id
        ).eq("portfolio_id", portfolio_id).execute()

        if not asset_response.data:
            raise ResourceNotFoundException("Asset", asset_id)

        # Get versions
        versions_response = supabase.table("asset_versions").select("*").eq(
            "asset_id", asset_id
        ).order("version_number", desc=True).execute()

        versions = versions_response.data or []

        return AssetVersionListResponse(
            asset_id=asset_id,
            versions=versions,
            total_versions=len(versions),
        )

    except (ResourceNotFoundException, AuthorizationException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==================== RESTORE VERSION ====================

@router.post("/{portfolio_id}/assets/{asset_id}/versions/{version_num}/restore")
async def restore_asset_version(
    portfolio_id: str,
    asset_id: str,
    version_num: int,
    current_user: dict = Depends(get_current_user)
):
    """Restore asset to previous version"""
    try:
        # Verify portfolio ownership
        portfolio = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()

        if not portfolio.data:
            raise ResourceNotFoundException("Portfolio", portfolio_id)

        if portfolio.data[0]["user_id"] != current_user["user_id"]:
            raise AuthorizationException()

        # Get asset
        asset_response = supabase.table("assets").select("*").eq(
            "id", asset_id
        ).eq("portfolio_id", portfolio_id).execute()

        if not asset_response.data:
            raise ResourceNotFoundException("Asset", asset_id)

        # Get version
        version_response = supabase.table("asset_versions").select("*").eq(
            "asset_id", asset_id
        ).eq("version_number", version_num).execute()

        if not version_response.data:
            raise ResourceNotFoundException("Asset version", f"{asset_id}:v{version_num}")

        version = version_response.data[0]

        # Update asset with version data
        update_data = {
            "storage_path": version["file_path"],
            "thumb_path": version["thumb_path"],
            "preview_path": version["preview_path"],
            "width": version["width"],
            "height": version["height"],
            "file_size": version["file_size"],
            "version": version_num,
            "updated_at": datetime.utcnow().isoformat(),
        }

        update_response = supabase.table("assets").update(update_data).eq(
            "id", asset_id
        ).execute()

        if not update_response.data:
            raise DatabaseException("Failed to restore version")

        return {
            "asset_id": asset_id,
            "restored_to_version": version_num,
            "message": f"Asset restored to version {version_num}",
        }

    except (ResourceNotFoundException, AuthorizationException, DatabaseException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==================== UPLOAD PROGRESS ====================

@router.get("/{portfolio_id}/assets/upload/{upload_id}/progress")
async def get_upload_progress(
    portfolio_id: str,
    upload_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get upload progress"""
    try:
        # Verify portfolio ownership
        portfolio = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()

        if not portfolio.data:
            raise ResourceNotFoundException("Portfolio", portfolio_id)

        if portfolio.data[0]["user_id"] != current_user["user_id"]:
            raise AuthorizationException()

        upload_manager = get_upload_manager()
        progress = upload_manager.get_upload_progress(upload_id)

        if not progress:
            raise ResourceNotFoundException("Upload", upload_id)

        return progress

    except (ResourceNotFoundException, AuthorizationException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
