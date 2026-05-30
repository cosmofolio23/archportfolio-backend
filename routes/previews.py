"""
Asset preview and thumbnail API endpoints
Phase 2: Task 2.5 - Preview generation, thumbnails, lazy loading
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query, Header
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional
from io import BytesIO

from routes.deps import get_current_user
from services.preview import get_preview_service
from services.storage import get_storage_client
from error_handlers import ResourceNotFoundException, AuthorizationException
from database import supabase

router = APIRouter()

# ==================== THUMBNAIL ENDPOINTS ====================

@router.get("/{portfolio_id}/assets/{asset_id}/preview")
async def get_asset_preview(
    portfolio_id: str,
    asset_id: str,
    size: str = Query("preview-1200", regex="^(thumb-250|thumb-500|preview-1200|original)$"),
    format: Optional[str] = Query(None, regex="^(webp|jpeg|png)$"),
    accept: Optional[str] = Header(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Get asset preview/thumbnail

    Parameters:
    - **size**: thumb-250, thumb-500, preview-1200, original
    - **format**: webp (default), jpeg, png
    - **accept**: Accept header for format negotiation
    """
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

        asset = asset_response.data[0]

        # Determine storage path based on size
        if size == "original":
            storage_path = asset.get("storage_path")
        elif size == "thumb-250":
            storage_path = asset.get("thumb_path")
        elif size == "thumb-500":
            # Assume thumb-500 follows same naming pattern
            storage_path = asset.get("storage_path", "").replace("original", "thumb-500")
            if "original" not in asset.get("storage_path", ""):
                storage_path = asset.get("thumb_path")  # Fallback
        else:  # preview-1200
            storage_path = asset.get("preview_path")

        if not storage_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Preview not available for size: {size}"
            )

        # Get storage client
        storage_client = get_storage_client()

        # Get presigned URL
        url = await storage_client.get_asset_url(storage_path, expiration_hours=24)

        # Get cache headers
        preview_service = get_preview_service()
        cache_headers = preview_service.get_cache_headers(immutable=True)

        return JSONResponse(
            content={
                "asset_id": asset_id,
                "size": size,
                "url": url,
                "width": asset.get("width"),
                "height": asset.get("height"),
                "aspect_ratio": asset.get("aspect_ratio"),
            },
            headers=cache_headers
        )

    except (ResourceNotFoundException, AuthorizationException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==================== BLUR PLACEHOLDER ====================

@router.get("/{portfolio_id}/assets/{asset_id}/blur")
async def get_blur_placeholder(
    portfolio_id: str,
    asset_id: str,
    quality: int = Query(60, ge=20, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    Get blur-up placeholder (data URL)

    Parameters:
    - **quality**: Compression quality (20-100)
    """
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

        asset = asset_response.data[0]

        # Get asset file data (would need to fetch from storage)
        # For now, return metadata-based placeholder
        preview_service = get_preview_service()
        metadata = await preview_service.get_preview_metadata(asset_id, portfolio_id)

        return JSONResponse(
            content={
                "asset_id": asset_id,
                "blur_data_url": None,  # Would be generated from actual image
                "dominant_color": metadata["dominant_color"],
                "aspect_ratio": metadata["aspect_ratio"],
                "width": metadata["width"],
                "height": metadata["height"],
            },
            headers=preview_service.get_cache_headers(immutable=True)
        )

    except (ResourceNotFoundException, AuthorizationException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==================== PREVIEW METADATA ====================

@router.get("/{portfolio_id}/assets/{asset_id}/preview-metadata")
async def get_preview_metadata(
    portfolio_id: str,
    asset_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get comprehensive preview metadata

    Returns: width, height, aspect_ratio, dominant_color, preview_urls, srcset
    """
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

        preview_service = get_preview_service()
        metadata = await preview_service.get_preview_metadata(asset_id, portfolio_id)

        return JSONResponse(
            content=metadata,
            headers=preview_service.get_cache_headers()
        )

    except (ResourceNotFoundException, AuthorizationException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==================== RESPONSIVE IMAGE CONFIG ====================

@router.get("/{portfolio_id}/assets/{asset_id}/responsive-config")
async def get_responsive_config(
    portfolio_id: str,
    asset_id: str,
    base_url: str = Query(..., description="Base URL for image paths"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get responsive image configuration for React/HTML

    Returns: src, srcSet, sizes, alt, loading, width, height
    """
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

        preview_service = get_preview_service()
        config = await preview_service.get_responsive_image_config(
            asset_id,
            portfolio_id,
            base_url
        )

        return JSONResponse(
            content=config,
            headers=preview_service.get_cache_headers()
        )

    except (ResourceNotFoundException, AuthorizationException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==================== THUMBNAIL VARIANTS ====================

@router.get("/{portfolio_id}/assets/{asset_id}/variants")
async def get_thumbnail_variants(
    portfolio_id: str,
    asset_id: str,
    base_url: str = Query(..., description="Base URL for image paths"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all thumbnail variants with metadata

    Returns: Dictionary of size -> {url, width, height, quality}
    """
    try:
        # Verify portfolio ownership
        portfolio = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()

        if not portfolio.data:
            raise ResourceNotFoundException("Portfolio", portfolio_id)

        if portfolio.data[0]["user_id"] != current_user["user_id"]:
            raise AuthorizationException()

        # Get asset (just to verify it exists)
        asset_response = supabase.table("assets").select("*").eq(
            "id", asset_id
        ).eq("portfolio_id", portfolio_id).execute()

        if not asset_response.data:
            raise ResourceNotFoundException("Asset", asset_id)

        preview_service = get_preview_service()
        variants = await preview_service.get_thumbnail_variants(asset_id, base_url)

        return JSONResponse(
            content=variants,
            headers=preview_service.get_cache_headers()
        )

    except (ResourceNotFoundException, AuthorizationException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==================== PREVIEW STATISTICS ====================

@router.get("/{portfolio_id}/preview-stats")
async def get_preview_statistics(
    portfolio_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get preview generation statistics for portfolio

    Returns: total_assets, thumbnail_status breakdown, storage estimates
    """
    try:
        # Verify portfolio ownership
        portfolio = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()

        if not portfolio.data:
            raise ResourceNotFoundException("Portfolio", portfolio_id)

        if portfolio.data[0]["user_id"] != current_user["user_id"]:
            raise AuthorizationException()

        preview_service = get_preview_service()
        stats = await preview_service.get_preview_stats(portfolio_id)

        return JSONResponse(
            content=stats,
            headers=preview_service.get_cache_headers()
        )

    except (ResourceNotFoundException, AuthorizationException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==================== SRCSET GENERATION ====================

@router.get("/{portfolio_id}/assets/{asset_id}/srcset")
async def get_srcset(
    portfolio_id: str,
    asset_id: str,
    base_url: str = Query(..., description="Base URL for image paths"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get HTML srcset for responsive images

    Format: url 250w, url 500w, url 1200w
    """
    try:
        # Verify portfolio ownership
        portfolio = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()

        if not portfolio.data:
            raise ResourceNotFoundException("Portfolio", portfolio_id)

        if portfolio.data[0]["user_id"] != current_user["user_id"]:
            raise AuthorizationException()

        # Get asset (just to verify it exists)
        asset_response = supabase.table("assets").select("*").eq(
            "id", asset_id
        ).eq("portfolio_id", portfolio_id).execute()

        if not asset_response.data:
            raise ResourceNotFoundException("Asset", asset_id)

        preview_service = get_preview_service()
        srcset = await preview_service.generate_srcset(asset_id, base_url)

        return JSONResponse(
            content={
                "asset_id": asset_id,
                "srcset": srcset,
                "sizes": "(max-width: 600px) 100vw, (max-width: 1200px) 50vw, 33vw",
            },
            headers=preview_service.get_cache_headers()
        )

    except (ResourceNotFoundException, AuthorizationException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==================== DOMINANT COLOR ====================

@router.get("/{portfolio_id}/assets/{asset_id}/color")
async def get_dominant_color(
    portfolio_id: str,
    asset_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get dominant color from asset for placeholder background

    Returns: {color: "#RRGGBB", rgb: (r, g, b), hex: "RRGGBB"}
    """
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

        # Return default for now (would be computed from actual image)
        preview_service = get_preview_service()

        return JSONResponse(
            content={
                "asset_id": asset_id,
                "color": "#808080",
                "rgb": (128, 128, 128),
                "hex": "808080",
            },
            headers=preview_service.get_cache_headers()
        )

    except (ResourceNotFoundException, AuthorizationException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==================== BATCH PREVIEW METADATA ====================

@router.post("/{portfolio_id}/assets/preview-batch")
async def get_batch_preview_metadata(
    portfolio_id: str,
    asset_ids: list = Query(..., description="List of asset IDs"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get preview metadata for multiple assets at once

    Useful for loading multiple assets on a page
    """
    try:
        # Verify portfolio ownership
        portfolio = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()

        if not portfolio.data:
            raise ResourceNotFoundException("Portfolio", portfolio_id)

        if portfolio.data[0]["user_id"] != current_user["user_id"]:
            raise AuthorizationException()

        preview_service = get_preview_service()
        results = {}

        for asset_id in asset_ids:
            try:
                metadata = await preview_service.get_preview_metadata(asset_id, portfolio_id)
                results[asset_id] = metadata
            except Exception as e:
                results[asset_id] = {"error": str(e)}

        return JSONResponse(
            content=results,
            headers=preview_service.get_cache_headers()
        )

    except (ResourceNotFoundException, AuthorizationException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
