"""
Portfolio endpoints for multi-project portfolio system
Phase 1: Core portfolio management
"""

from fastapi import APIRouter, HTTPException, status, Header, Depends
from typing import List
from datetime import datetime
from uuid import uuid4
from models import (
    PortfolioCreateRequest,
    PortfolioDetailResponse,
    PortfolioSettingsRequest,
    PortfolioSettingsResponse,
)
from routes.deps import get_current_user
from database import supabase

router = APIRouter()

# ==================== Portfolio CRUD ====================

@router.post("/", response_model=PortfolioDetailResponse)
async def create_portfolio(
    req: PortfolioCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new portfolio"""
    try:
        portfolio_data = {
            "id": str(uuid4()),
            "user_id": current_user["user_id"],
            "title": req.title,
            "architect_name": req.architect_name,
            "architect_bio": req.architect_bio or "",
            "page_size": req.page_size.value,
            "page_orientation": req.page_orientation.value,
            "margins": req.margins.value,
            "is_published": False,
            "view_count": 0,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        response = supabase.table("portfolios").insert(portfolio_data).execute()

        if response.data:
            return response.data[0]

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create portfolio"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{portfolio_id}", response_model=PortfolioDetailResponse)
async def get_portfolio(
    portfolio_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get portfolio details"""
    try:
        response = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )

        portfolio = response.data[0]

        # Check ownership
        if portfolio["user_id"] != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        return portfolio

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/{portfolio_id}", response_model=PortfolioDetailResponse)
async def update_portfolio(
    portfolio_id: str,
    req: PortfolioSettingsRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update portfolio settings"""
    try:
        # Verify ownership
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

        update_data = {
            "title": req.title,
            "description": req.description,
            "architect_name": req.architect_name,
            "architect_bio": req.architect_bio or "",
            "page_size": req.page_size.value,
            "page_orientation": req.page_orientation.value,
            "margins": req.margins.value,
            "style_id": req.style_id,
            "updated_at": datetime.utcnow().isoformat(),
        }

        response = supabase.table("portfolios").update(update_data).eq("id", portfolio_id).execute()

        if response.data:
            return response.data[0]

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update portfolio"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio(
    portfolio_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete portfolio"""
    try:
        # Verify ownership
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

        supabase.table("portfolios").delete().eq("id", portfolio_id).execute()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==================== Portfolio List ====================

@router.get("/", response_model=List[PortfolioDetailResponse])
async def list_user_portfolios(
    current_user: dict = Depends(get_current_user)
):
    """List all portfolios for current user"""
    try:
        response = supabase.table("portfolios").select("*").eq(
            "user_id", current_user["user_id"]
        ).order("created_at", desc=True).execute()

        return response.data or []

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==================== Portfolio Settings ====================

@router.get("/{portfolio_id}/settings", response_model=PortfolioSettingsResponse)
async def get_portfolio_settings(
    portfolio_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all portfolio settings"""
    try:
        response = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )

        portfolio = response.data[0]

        if portfolio["user_id"] != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        return portfolio

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/{portfolio_id}/settings", response_model=PortfolioSettingsResponse)
async def update_portfolio_settings(
    portfolio_id: str,
    req: PortfolioSettingsRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update portfolio settings"""
    try:
        # Verify ownership
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

        update_data = {
            "title": req.title,
            "description": req.description,
            "architect_name": req.architect_name,
            "architect_bio": req.architect_bio or "",
            "page_size": req.page_size.value,
            "page_orientation": req.page_orientation.value,
            "margins": req.margins.value,
            "style_id": req.style_id,
            "updated_at": datetime.utcnow().isoformat(),
        }

        response = supabase.table("portfolios").update(update_data).eq("id", portfolio_id).execute()

        if response.data:
            return response.data[0]

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update settings"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==================== Public Portfolio View ====================

@router.get("/{portfolio_id}/public", response_model=PortfolioDetailResponse)
async def view_public_portfolio(portfolio_id: str):
    """View published portfolio (no auth required)"""
    try:
        response = supabase.table("portfolios").select("*").eq(
            "id", portfolio_id
        ).eq("is_published", True).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found or not published"
            )

        # Increment view count
        portfolio = response.data[0]
        supabase.table("portfolios").update({
            "view_count": (portfolio.get("view_count", 0) or 0) + 1
        }).eq("id", portfolio_id).execute()

        return portfolio

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
