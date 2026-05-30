"""
Asset search and organization API endpoints
Phase 2: Task 2.4 - Search, filter, organize assets
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from datetime import datetime

from routes.deps import get_current_user
from services.search import (
    get_search_service,
    SearchFilter,
    SortField,
    SortOrder,
)
from error_handlers import (
    ResourceNotFoundException,
    AuthorizationException,
)
from database import supabase

router = APIRouter()

# ==================== ADVANCED SEARCH ====================

@router.get("/{portfolio_id}/search")
async def search_assets(
    portfolio_id: str,
    q: Optional[str] = Query(None, description="Search query (filename, description)"),
    asset_type: Optional[str] = Query(None, description="Filter by asset type"),
    tag: Optional[str] = Query(None, description="Filter by tag (comma-separated)"),
    created_after: Optional[str] = Query(None, description="ISO date filter"),
    created_before: Optional[str] = Query(None, description="ISO date filter"),
    min_size_kb: Optional[float] = Query(None, description="Minimum file size in KB"),
    max_size_kb: Optional[float] = Query(None, description="Maximum file size in KB"),
    min_ratio: Optional[float] = Query(None, description="Minimum aspect ratio"),
    max_ratio: Optional[float] = Query(None, description="Maximum aspect ratio"),
    sort_by: str = Query("created_at", regex="^(created_at|file_size|file_name|aspect_ratio)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    Advanced search with multiple filters

    Parameters:
    - **q**: Search query for filename or description
    - **asset_type**: Filter by render, plan, section, diagram, detail, material
    - **tag**: Filter by tag (comma-separated for multiple)
    - **created_after/before**: Date range filter (ISO format)
    - **min_size_kb/max_size_kb**: File size range
    - **min_ratio/max_ratio**: Aspect ratio range
    - **sort_by**: Sort field (created_at, file_size, file_name, aspect_ratio)
    - **sort_order**: asc or desc
    - **page/page_size**: Pagination
    """
    try:
        # Verify portfolio ownership
        portfolio = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()

        if not portfolio.data:
            raise ResourceNotFoundException("Portfolio", portfolio_id)

        if portfolio.data[0]["user_id"] != current_user["user_id"]:
            raise AuthorizationException()

        # Parse tags
        tags_list = None
        if tag:
            tags_list = [t.strip() for t in tag.split(",") if t.strip()]

        # Parse dates
        created_after_dt = None
        if created_after:
            created_after_dt = datetime.fromisoformat(created_after.replace("Z", "+00:00"))

        created_before_dt = None
        if created_before:
            created_before_dt = datetime.fromisoformat(created_before.replace("Z", "+00:00"))

        # Parse asset types
        asset_types_list = None
        if asset_type:
            asset_types_list = [t.strip() for t in asset_type.split(",") if t.strip()]

        # Build search filter
        filters = SearchFilter(
            portfolio_id=portfolio_id,
            user_id=current_user["user_id"],
            search_query=q,
            asset_types=asset_types_list,
            tags=tags_list,
            created_after=created_after_dt,
            created_before=created_before_dt,
            min_size_kb=min_size_kb,
            max_size_kb=max_size_kb,
            aspect_ratio_min=min_ratio,
            aspect_ratio_max=max_ratio,
            sort_by=SortField(sort_by),
            sort_order=SortOrder(sort_order),
            page=page,
            page_size=page_size,
        )

        # Execute search
        search_service = get_search_service()
        result = await search_service.search(filters)

        return {
            "items": result.items,
            "total": result.total,
            "page": result.page,
            "page_size": result.page_size,
            "total_pages": result.total_pages,
            "filters": result.filters_applied,
        }

    except (ResourceNotFoundException, AuthorizationException):
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid filter value: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==================== TEXT SEARCH ====================

@router.get("/{portfolio_id}/search/by-filename")
async def search_by_filename(
    portfolio_id: str,
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Search assets by filename"""
    try:
        # Verify portfolio ownership
        portfolio = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()

        if not portfolio.data:
            raise ResourceNotFoundException("Portfolio", portfolio_id)

        if portfolio.data[0]["user_id"] != current_user["user_id"]:
            raise AuthorizationException()

        search_service = get_search_service()
        result = await search_service.search_by_filename(
            portfolio_id,
            current_user["user_id"],
            q,
            page=page,
            page_size=page_size
        )

        return {
            "items": result.items,
            "total": result.total,
            "page": result.page,
            "page_size": result.page_size,
            "total_pages": result.total_pages,
        }

    except (ResourceNotFoundException, AuthorizationException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==================== TAG SEARCH ====================

@router.get("/{portfolio_id}/search/by-tags")
async def search_by_tags(
    portfolio_id: str,
    tags: str = Query(..., description="Comma-separated tags"),
    match_all: bool = Query(False, description="Must have all tags (AND) vs any tag (OR)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Search assets by tags"""
    try:
        # Verify portfolio ownership
        portfolio = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()

        if not portfolio.data:
            raise ResourceNotFoundException("Portfolio", portfolio_id)

        if portfolio.data[0]["user_id"] != current_user["user_id"]:
            raise AuthorizationException()

        # Parse tags
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

        search_service = get_search_service()
        result = await search_service.search_by_tag(
            portfolio_id,
            current_user["user_id"],
            tag_list,
            match_all=match_all,
            page=page,
            page_size=page_size
        )

        return {
            "items": result.items,
            "total": result.total,
            "page": result.page,
            "page_size": result.page_size,
            "total_pages": result.total_pages,
        }

    except (ResourceNotFoundException, AuthorizationException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==================== TYPE FILTER ====================

@router.get("/{portfolio_id}/search/by-type")
async def filter_by_type(
    portfolio_id: str,
    types: str = Query(..., description="Comma-separated asset types"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Filter assets by type"""
    try:
        # Verify portfolio ownership
        portfolio = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()

        if not portfolio.data:
            raise ResourceNotFoundException("Portfolio", portfolio_id)

        if portfolio.data[0]["user_id"] != current_user["user_id"]:
            raise AuthorizationException()

        # Parse types
        type_list = [t.strip() for t in types.split(",") if t.strip()]

        search_service = get_search_service()
        result = await search_service.filter_by_type(
            portfolio_id,
            current_user["user_id"],
            type_list,
            page=page,
            page_size=page_size
        )

        return {
            "items": result.items,
            "total": result.total,
            "page": result.page,
            "page_size": result.page_size,
            "total_pages": result.total_pages,
        }

    except (ResourceNotFoundException, AuthorizationException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==================== DATE RANGE FILTER ====================

@router.get("/{portfolio_id}/search/by-date")
async def filter_by_date(
    portfolio_id: str,
    after: str = Query(..., description="Start date (ISO format)"),
    before: str = Query(..., description="End date (ISO format)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Filter assets by date range"""
    try:
        # Verify portfolio ownership
        portfolio = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()

        if not portfolio.data:
            raise ResourceNotFoundException("Portfolio", portfolio_id)

        if portfolio.data[0]["user_id"] != current_user["user_id"]:
            raise AuthorizationException()

        # Parse dates
        try:
            after_dt = datetime.fromisoformat(after.replace("Z", "+00:00"))
            before_dt = datetime.fromisoformat(before.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use ISO 8601 format (e.g., 2026-05-30T00:00:00Z)"
            )

        search_service = get_search_service()
        result = await search_service.filter_by_date_range(
            portfolio_id,
            current_user["user_id"],
            after_dt,
            before_dt,
            page=page,
            page_size=page_size
        )

        return {
            "items": result.items,
            "total": result.total,
            "page": result.page,
            "page_size": result.page_size,
            "total_pages": result.total_pages,
        }

    except (ResourceNotFoundException, AuthorizationException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==================== SIZE FILTER ====================

@router.get("/{portfolio_id}/search/by-size")
async def filter_by_size(
    portfolio_id: str,
    min_kb: float = Query(..., ge=0),
    max_kb: float = Query(..., ge=0),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Filter assets by file size"""
    try:
        # Verify portfolio ownership
        portfolio = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()

        if not portfolio.data:
            raise ResourceNotFoundException("Portfolio", portfolio_id)

        if portfolio.data[0]["user_id"] != current_user["user_id"]:
            raise AuthorizationException()

        search_service = get_search_service()
        result = await search_service.filter_by_size(
            portfolio_id,
            current_user["user_id"],
            min_kb,
            max_kb,
            page=page,
            page_size=page_size
        )

        return {
            "items": result.items,
            "total": result.total,
            "page": result.page,
            "page_size": result.page_size,
            "total_pages": result.total_pages,
        }

    except (ResourceNotFoundException, AuthorizationException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==================== ASPECT RATIO FILTER ====================

@router.get("/{portfolio_id}/search/by-aspect-ratio")
async def filter_by_aspect_ratio(
    portfolio_id: str,
    min_ratio: float = Query(..., ge=0.1),
    max_ratio: float = Query(..., ge=0.1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Filter assets by aspect ratio"""
    try:
        # Verify portfolio ownership
        portfolio = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()

        if not portfolio.data:
            raise ResourceNotFoundException("Portfolio", portfolio_id)

        if portfolio.data[0]["user_id"] != current_user["user_id"]:
            raise AuthorizationException()

        search_service = get_search_service()
        result = await search_service.filter_by_aspect_ratio(
            portfolio_id,
            current_user["user_id"],
            min_ratio,
            max_ratio,
            page=page,
            page_size=page_size
        )

        return {
            "items": result.items,
            "total": result.total,
            "page": result.page,
            "page_size": result.page_size,
            "total_pages": result.total_pages,
        }

    except (ResourceNotFoundException, AuthorizationException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==================== TAGS ====================

@router.get("/{portfolio_id}/tags")
async def get_all_tags(
    portfolio_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all tags in portfolio with usage counts"""
    try:
        # Verify portfolio ownership
        portfolio = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()

        if not portfolio.data:
            raise ResourceNotFoundException("Portfolio", portfolio_id)

        if portfolio.data[0]["user_id"] != current_user["user_id"]:
            raise AuthorizationException()

        search_service = get_search_service()
        tags = await search_service.get_all_tags(portfolio_id)

        return {
            "tags": tags,
            "total": len(tags),
        }

    except (ResourceNotFoundException, AuthorizationException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{portfolio_id}/tags/popular")
async def get_popular_tags(
    portfolio_id: str,
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get most popular tags in portfolio"""
    try:
        # Verify portfolio ownership
        portfolio = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()

        if not portfolio.data:
            raise ResourceNotFoundException("Portfolio", portfolio_id)

        if portfolio.data[0]["user_id"] != current_user["user_id"]:
            raise AuthorizationException()

        search_service = get_search_service()
        tags = await search_service.get_popular_tags(portfolio_id, limit=limit)

        return {
            "tags": tags,
            "total": len(tags),
        }

    except (ResourceNotFoundException, AuthorizationException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==================== COLLECTIONS ====================

@router.get("/{portfolio_id}/collections")
async def get_collections(
    portfolio_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get asset collections organized by type"""
    try:
        # Verify portfolio ownership
        portfolio = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()

        if not portfolio.data:
            raise ResourceNotFoundException("Portfolio", portfolio_id)

        if portfolio.data[0]["user_id"] != current_user["user_id"]:
            raise AuthorizationException()

        search_service = get_search_service()
        collections = await search_service.get_asset_collections(portfolio_id)

        return {
            "collections": collections,
            "total": len(collections),
        }

    except (ResourceNotFoundException, AuthorizationException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==================== STATISTICS ====================

@router.get("/{portfolio_id}/statistics")
async def get_statistics(
    portfolio_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get portfolio asset statistics"""
    try:
        # Verify portfolio ownership
        portfolio = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()

        if not portfolio.data:
            raise ResourceNotFoundException("Portfolio", portfolio_id)

        if portfolio.data[0]["user_id"] != current_user["user_id"]:
            raise AuthorizationException()

        search_service = get_search_service()
        stats = await search_service.get_collection_stats(portfolio_id)

        return stats

    except (ResourceNotFoundException, AuthorizationException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==================== SEARCH SUGGESTIONS ====================

@router.get("/{portfolio_id}/search/suggestions")
async def get_suggestions(
    portfolio_id: str,
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    """Get search suggestions based on query"""
    try:
        # Verify portfolio ownership
        portfolio = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()

        if not portfolio.data:
            raise ResourceNotFoundException("Portfolio", portfolio_id)

        if portfolio.data[0]["user_id"] != current_user["user_id"]:
            raise AuthorizationException()

        search_service = get_search_service()
        suggestions = await search_service.get_search_suggestions(
            portfolio_id,
            current_user["user_id"],
            q,
            limit=limit
        )

        return suggestions

    except (ResourceNotFoundException, AuthorizationException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
