from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from typing import List
from datetime import datetime
from models import GeneratePortfolioRequest, PortfolioResponse
from routes.deps import get_current_user
from database import supabase
import uuid
import json

router = APIRouter()

# ==================== Portfolio Generation ====================

def generate_portfolio_structure(
    project_id: str,
    layout_id: str,
    style_id: str,
    assets: dict
) -> dict:
    """
    Generate portfolio structure (page layout and content assignment).
    In production, this would call Llama 2 via Replicate.
    For now, use heuristic rules.
    """

    # Simple heuristic page generation
    pages = []

    # Page 1: Cover
    pages.append({
        "page_num": 1,
        "title": "Cover",
        "components": [
            {
                "type": "title",
                "content": "Project Title"
            },
            {
                "type": "render",
                "asset_id": assets.get("renders", [None])[0],
                "position": "hero"
            }
        ]
    })

    # Page 2: Concept
    if assets.get("diagrams"):
        pages.append({
            "page_num": 2,
            "title": "Concept",
            "components": [
                {
                    "type": "text",
                    "content": "Concept & Approach"
                },
                {
                    "type": "diagram",
                    "asset_id": assets.get("diagrams", [None])[0],
                    "position": "main"
                }
            ]
        })

    # Page 3: Plans
    if assets.get("plans"):
        pages.append({
            "page_num": 3,
            "title": "Plans",
            "components": [
                {
                    "type": "text",
                    "content": "Floor Plans"
                },
                {
                    "type": "plan",
                    "asset_id": assets.get("plans", [None])[0],
                    "position": "main"
                }
            ]
        })

    # Page 4: Sections
    if assets.get("sections"):
        pages.append({
            "page_num": 4,
            "title": "Sections",
            "components": [
                {
                    "type": "text",
                    "content": "Building Sections"
                },
                {
                    "type": "section",
                    "asset_id": assets.get("sections", [None])[0],
                    "position": "main"
                }
            ]
        })

    # Pages 5+: Renders
    render_idx = 5
    for render_id in assets.get("renders", []):
        if render_idx == 1:
            continue  # Skip first render (used as cover)
        pages.append({
            "page_num": render_idx,
            "title": f"Render {render_idx - 4}",
            "components": [
                {
                    "type": "render",
                    "asset_id": render_id,
                    "position": "hero"
                }
            ]
        })
        render_idx += 1

    return {"pages": pages, "total_pages": len(pages)}

# ==================== Routes ====================

@router.post("/{project_id}/generate")
async def generate_portfolio(
    project_id: str,
    req: GeneratePortfolioRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Generate one or more portfolio variants"""
    try:
        # Verify project ownership
        project_response = supabase.table("projects").select("*").eq("id", project_id).eq("user_id", current_user["user_id"]).execute()
        if not project_response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        # Get project assets
        assets_response = supabase.table("assets").select("*").eq("project_id", project_id).execute()

        assets_by_type = {
            "renders": [],
            "plans": [],
            "sections": [],
            "diagrams": []
        }

        for asset in assets_response.data:
            asset_type = asset.get("asset_type", "render")
            if asset_type == "render":
                assets_by_type["renders"].append(asset["id"])
            elif asset_type == "plan":
                assets_by_type["plans"].append(asset["id"])
            elif asset_type == "section":
                assets_by_type["sections"].append(asset["id"])
            elif asset_type == "diagram":
                assets_by_type["diagrams"].append(asset["id"])

        # Generate portfolio variants
        generated_portfolios = []

        variant_count = req.variant_count if req.variant_number is None else 1
        start_variant = req.variant_number if req.variant_number else 1

        for variant_num in range(variant_count):
            portfolio_data = {
                "id": str(uuid.uuid4()),
                "project_id": project_id,
                "layout_id": req.layout_id,
                "style_pack": req.style_pack,
                "status": "ready",
                "variant_number": start_variant + variant_num,
                "created_at": datetime.utcnow().isoformat()
            }

            # Generate page structure
            page_structure = generate_portfolio_structure(
                project_id,
                req.layout_id,
                req.style_pack,
                assets_by_type
            )

            portfolio_data["page_structure"] = page_structure

            # Insert portfolio
            response = supabase.table("portfolios").insert(portfolio_data).execute()
            if response.data:
                portfolio = response.data[0]
                portfolio["status"] = "ready"
                generated_portfolios.append(portfolio)

                # Schedule async HTML/PDF generation
                # background_tasks.add_task(generate_portfolio_files, portfolio["id"])

        return {
            "message": f"Generated {len(generated_portfolios)} portfolio variants",
            "portfolios": generated_portfolios
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{project_id}/list")
async def list_portfolios(project_id: str, current_user: dict = Depends(get_current_user)):
    """List all portfolios for a project"""
    try:
        response = supabase.table("portfolios").select("*").eq("project_id", project_id).order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{portfolio_id}")
async def get_portfolio(portfolio_id: str, current_user: dict = Depends(get_current_user)):
    """Get portfolio details"""
    try:
        response = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()
        if response.data:
            portfolio = response.data[0]
            # Verify user ownership through project
            project = supabase.table("projects").select("*").eq("id", portfolio["project_id"]).eq("user_id", current_user["user_id"]).execute()
            if project.data:
                return portfolio
            else:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't own this portfolio")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Portfolio {portfolio_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio(portfolio_id: str, current_user: dict = Depends(get_current_user)):
    """Delete portfolio"""
    try:
        response = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()
        if response.data:
            portfolio = response.data[0]
            # Verify user ownership
            project = supabase.table("projects").select("*").eq("id", portfolio["project_id"]).eq("user_id", current_user["user_id"]).execute()
            if project.data:
                supabase.table("portfolios").delete().eq("id", portfolio_id).execute()
                return

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{portfolio_id}/preview")
async def get_portfolio_preview(portfolio_id: str, current_user: dict = Depends(get_current_user)):
    """Get portfolio HTML preview"""
    try:
        response = supabase.table("portfolios").select("*").eq("id", portfolio_id).execute()
        if response.data:
            portfolio = response.data[0]
            # Verify user ownership
            project = supabase.table("projects").select("*").eq("id", portfolio["project_id"]).eq("user_id", current_user["user_id"]).execute()
            if project.data:
                return {
                    "portfolio_id": portfolio_id,
                    "html": portfolio.get("generated_html") or "<p>Portfolio HTML will be generated here</p>"
                }
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
