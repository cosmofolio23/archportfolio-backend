"""
Portfolio Page endpoints for page layout configuration
Phase 1: Task 1.4 - Page configuration and layout management
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel
from models import (
    PortfolioPageCreateRequest,
    PortfolioPageUpdateRequest,
    PortfolioPageResponse,
)
from routes.deps import get_current_user
from database import supabase

router = APIRouter()

# ==================== Portfolio Page CRUD ====================

@router.post("/{portfolio_id}/pages", response_model=PortfolioPageResponse)
async def create_portfolio_page(
    portfolio_id: str,
    req: PortfolioPageCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new page in portfolio"""
    try:
        # Verify portfolio ownership
        portfolio = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()

        if not portfolio.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )

        if portfolio.data[0]["user_id"] != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Verify layout exists
        layout = supabase.table("layout_templates").select("*").eq("id", req.layout_id).execute()

        if not layout.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Layout '{req.layout_id}' not found"
            )

        page_data = {
            "id": str(uuid4()),
            "portfolio_id": portfolio_id,
            "page_number": req.page_number,
            "page_type": req.page_type.value,
            "layout_id": req.layout_id,
            "title": req.title,
            "description": req.description,
            "layout_config": req.layout_config.model_dump() if req.layout_config else None,
            "asset_ids": req.asset_ids or [],
            "style_override_id": req.style_override_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        response = supabase.table("portfolio_pages").insert(page_data).execute()

        if response.data:
            return response.data[0]

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create page"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{portfolio_id}/pages", response_model=List[PortfolioPageResponse])
async def list_portfolio_pages(
    portfolio_id: str,
    current_user: dict = Depends(get_current_user)
):
    """List all pages in a portfolio"""
    try:
        # Verify portfolio ownership
        portfolio = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()

        if not portfolio.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )

        if portfolio.data[0]["user_id"] != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        response = supabase.table("portfolio_pages").select("*").eq(
            "portfolio_id", portfolio_id
        ).order("page_number", desc=False).execute()

        return response.data or []

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{portfolio_id}/pages/{page_num}", response_model=PortfolioPageResponse)
async def get_portfolio_page(
    portfolio_id: str,
    page_num: int,
    current_user: dict = Depends(get_current_user)
):
    """Get specific portfolio page"""
    try:
        # Verify portfolio ownership
        portfolio = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()

        if not portfolio.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )

        if portfolio.data[0]["user_id"] != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Get page
        response = supabase.table("portfolio_pages").select("*").eq(
            "portfolio_id", portfolio_id
        ).eq("page_number", page_num).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Page {page_num} not found"
            )

        return response.data[0]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/{portfolio_id}/pages/{page_num}", response_model=PortfolioPageResponse)
async def update_portfolio_page(
    portfolio_id: str,
    page_num: int,
    req: PortfolioPageUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update portfolio page"""
    try:
        # Verify portfolio ownership
        portfolio = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()

        if not portfolio.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )

        if portfolio.data[0]["user_id"] != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Get existing page
        page = supabase.table("portfolio_pages").select("*").eq(
            "portfolio_id", portfolio_id
        ).eq("page_number", page_num).execute()

        if not page.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Page {page_num} not found"
            )

        # Verify layout if updating
        if req.layout_id:
            layout = supabase.table("layout_templates").select("*").eq("id", req.layout_id).execute()

            if not layout.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Layout '{req.layout_id}' not found"
                )

        update_data = {
            "page_type": req.page_type.value if req.page_type else page.data[0]["page_type"],
            "layout_id": req.layout_id or page.data[0]["layout_id"],
            "title": req.title if req.title is not None else page.data[0]["title"],
            "description": req.description if req.description is not None else page.data[0]["description"],
            "layout_config": req.layout_config.model_dump() if req.layout_config else page.data[0].get("layout_config"),
            "asset_ids": req.asset_ids if req.asset_ids is not None else page.data[0].get("asset_ids", []),
            "style_override_id": req.style_override_id if req.style_override_id is not None else page.data[0].get("style_override_id"),
            "updated_at": datetime.utcnow().isoformat(),
        }

        response = supabase.table("portfolio_pages").update(update_data).eq(
            "portfolio_id", portfolio_id
        ).eq("page_number", page_num).execute()

        if response.data:
            return response.data[0]

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update page"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{portfolio_id}/pages/{page_num}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio_page(
    portfolio_id: str,
    page_num: int,
    current_user: dict = Depends(get_current_user)
):
    """Delete portfolio page"""
    try:
        # Verify portfolio ownership
        portfolio = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()

        if not portfolio.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )

        if portfolio.data[0]["user_id"] != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Delete page
        supabase.table("portfolio_pages").delete().eq(
            "portfolio_id", portfolio_id
        ).eq("page_number", page_num).execute()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==================== Page Ordering ====================

class PageOrderRequest(BaseModel):
    """Request body for reordering pages"""
    pages: List[dict]  # [{page_number: int, order: int}, ...]

@router.put("/{portfolio_id}/pages/order", response_model=List[PortfolioPageResponse])
async def reorder_portfolio_pages(
    portfolio_id: str,
    req: PageOrderRequest,
    current_user: dict = Depends(get_current_user)
):
    """Reorder pages in portfolio"""
    try:
        # Verify portfolio ownership
        portfolio = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()

        if not portfolio.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )

        if portfolio.data[0]["user_id"] != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Update page numbers based on new order
        for idx, page_info in enumerate(req.pages, 1):
            old_page_num = page_info.get("page_number")
            if old_page_num:
                supabase.table("portfolio_pages").update({
                    "page_number": idx
                }).eq("portfolio_id", portfolio_id).eq(
                    "page_number", old_page_num
                ).execute()

        # Return updated pages
        response = supabase.table("portfolio_pages").select("*").eq(
            "portfolio_id", portfolio_id
        ).order("page_number", desc=False).execute()

        return response.data or []

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==================== Layout Information ====================

@router.get("/layouts/available")
async def get_available_layouts():
    """Get all available layout templates"""
    try:
        response = supabase.table("layout_templates").select("*").execute()

        return {
            "layouts": response.data or [],
            "total": len(response.data or [])
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/layouts/{layout_id}")
async def get_layout_details(layout_id: str):
    """Get specific layout template details"""
    try:
        response = supabase.table("layout_templates").select("*").eq("id", layout_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Layout '{layout_id}' not found"
            )

        return response.data[0]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==================== Asset Assignment ====================

class AssetAssignmentRequest(BaseModel):
    """Request body for assigning assets to page"""
    asset_ids: List[str]
    asset_positions: dict = None  # Optional positioning info

@router.put("/{portfolio_id}/pages/{page_num}/assets", response_model=PortfolioPageResponse)
async def assign_assets_to_page(
    portfolio_id: str,
    page_num: int,
    req: AssetAssignmentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Assign assets to portfolio page"""
    try:
        # Verify portfolio ownership
        portfolio = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()

        if not portfolio.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )

        if portfolio.data[0]["user_id"] != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Get page
        page = supabase.table("portfolio_pages").select("*").eq(
            "portfolio_id", portfolio_id
        ).eq("page_number", page_num).execute()

        if not page.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Page {page_num} not found"
            )

        # Update assets
        update_data = {
            "asset_ids": req.asset_ids,
            "asset_positions": req.asset_positions,
            "updated_at": datetime.utcnow().isoformat(),
        }

        response = supabase.table("portfolio_pages").update(update_data).eq(
            "portfolio_id", portfolio_id
        ).eq("page_number", page_num).execute()

        if response.data:
            return response.data[0]

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to assign assets"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
