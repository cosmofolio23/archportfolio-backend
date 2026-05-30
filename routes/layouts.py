from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from models import LayoutResponse, LayoutRecommendation
from routes.deps import get_current_user
import json

router = APIRouter()

# ==================== Layout Catalog ====================

# Load layout definitions from JSON (in production, store in DB)
LAYOUTS_CATALOG = [
    {
        "id": "hero_render",
        "name": "Hero Render",
        "description": "Full-page hero image with title below",
        "pages": [
            {
                "page_num": 1,
                "regions": [
                    {
                        "type": "hero_image",
                        "assets": ["render"],
                        "x": 0, "y": 0, "w": 100, "h": 60,
                        "aspect": "16:9",
                        "position": "cover"
                    },
                    {
                        "type": "text",
                        "content": "title_description",
                        "x": 5, "y": 65, "w": 90, "h": 30,
                        "font_size": "title"
                    }
                ]
            }
        ]
    },
    {
        "id": "split_render_text",
        "name": "Split Render & Text",
        "description": "50/50 render and text layout",
        "pages": [
            {
                "page_num": 1,
                "regions": [
                    {
                        "type": "image",
                        "assets": ["render"],
                        "x": 0, "y": 0, "w": 50, "h": 100,
                        "position": "cover"
                    },
                    {
                        "type": "text",
                        "content": "title_description_details",
                        "x": 55, "y": 10, "w": 40, "h": 80,
                        "font_size": "body"
                    }
                ]
            }
        ]
    },
    {
        "id": "three_render_grid",
        "name": "3 Render Grid",
        "description": "3 renders in grid layout",
        "pages": [
            {
                "page_num": 1,
                "regions": [
                    {
                        "type": "image",
                        "assets": ["render"],
                        "x": 0, "y": 0, "w": 32, "h": 50,
                        "position": "cover"
                    },
                    {
                        "type": "image",
                        "assets": ["render"],
                        "x": 34, "y": 0, "w": 32, "h": 50,
                        "position": "cover"
                    },
                    {
                        "type": "image",
                        "assets": ["render"],
                        "x": 68, "y": 0, "w": 32, "h": 50,
                        "position": "cover"
                    },
                    {
                        "type": "text",
                        "content": "title",
                        "x": 5, "y": 55, "w": 90, "h": 40,
                        "font_size": "title"
                    }
                ]
            }
        ]
    },
    {
        "id": "plan_section_render",
        "name": "Plan + Section + Render",
        "description": "Technical drawing focus with render",
        "pages": [
            {
                "page_num": 1,
                "regions": [
                    {
                        "type": "image",
                        "assets": ["plan"],
                        "x": 0, "y": 0, "w": 33, "h": 100,
                        "position": "contain"
                    },
                    {
                        "type": "image",
                        "assets": ["section"],
                        "x": 34, "y": 0, "w": 33, "h": 100,
                        "position": "contain"
                    },
                    {
                        "type": "image",
                        "assets": ["render"],
                        "x": 68, "y": 0, "w": 32, "h": 100,
                        "position": "cover"
                    }
                ]
            }
        ]
    },
    {
        "id": "diagram_heavy",
        "name": "Diagram Heavy",
        "description": "Focus on diagrams and technical content",
        "pages": [
            {
                "page_num": 1,
                "regions": [
                    {
                        "type": "text",
                        "content": "title",
                        "x": 5, "y": 2, "w": 90, "h": 8,
                        "font_size": "title"
                    },
                    {
                        "type": "image",
                        "assets": ["diagram"],
                        "x": 5, "y": 12, "w": 43, "h": 42,
                        "position": "contain"
                    },
                    {
                        "type": "image",
                        "assets": ["diagram"],
                        "x": 52, "y": 12, "w": 43, "h": 42,
                        "position": "contain"
                    },
                    {
                        "type": "image",
                        "assets": ["diagram"],
                        "x": 5, "y": 56, "w": 90, "h": 39,
                        "position": "contain"
                    }
                ]
            }
        ]
    },
    {
        "id": "competition_board",
        "name": "Competition Board",
        "description": "Poster-style layout for competitions",
        "pages": [
            {
                "page_num": 1,
                "regions": [
                    {
                        "type": "text",
                        "content": "project_title",
                        "x": 5, "y": 2, "w": 90, "h": 10,
                        "font_size": "heading"
                    },
                    {
                        "type": "image",
                        "assets": ["render", "diagram"],
                        "x": 5, "y": 15, "w": 90, "h": 60,
                        "position": "cover"
                    },
                    {
                        "type": "text",
                        "content": "concept_location",
                        "x": 5, "y": 78, "w": 90, "h": 17,
                        "font_size": "caption"
                    }
                ]
            }
        ]
    },
    {
        "id": "timeline_layout",
        "name": "Timeline Layout",
        "description": "Project evolution timeline",
        "pages": [
            {
                "page_num": 1,
                "regions": [
                    {
                        "type": "text",
                        "content": "title",
                        "x": 5, "y": 2, "w": 90, "h": 8,
                        "font_size": "title"
                    },
                    {
                        "type": "image",
                        "assets": ["diagram", "render"],
                        "x": 5, "y": 12, "w": 28, "h": 30,
                        "position": "cover"
                    },
                    {
                        "type": "image",
                        "assets": ["diagram", "render"],
                        "x": 36, "y": 12, "w": 28, "h": 30,
                        "position": "cover"
                    },
                    {
                        "type": "image",
                        "assets": ["diagram", "render"],
                        "x": 67, "y": 12, "w": 28, "h": 30,
                        "position": "cover"
                    },
                    {
                        "type": "text",
                        "content": "timeline_description",
                        "x": 5, "y": 45, "w": 90, "h": 50,
                        "font_size": "body"
                    }
                ]
            }
        ]
    }
]

# ==================== Routes ====================

@router.get("", response_model=List[dict])
async def list_layouts():
    """Get all available layouts"""
    return LAYOUTS_CATALOG

@router.get("/{layout_id}", response_model=dict)
async def get_layout(layout_id: str):
    """Get specific layout details"""
    layout = next((l for l in LAYOUTS_CATALOG if l["id"] == layout_id), None)
    if not layout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Layout not found")
    return layout

@router.post("/recommend")
async def recommend_layout(
    render_count: int,
    plan_count: int,
    section_count: int,
    diagram_count: int,
    current_user: dict = Depends(get_current_user)
) -> LayoutRecommendation:
    """AI-powered layout recommendation based on asset counts"""
    total_assets = render_count + plan_count + section_count + diagram_count

    # Simple heuristic rules for layout recommendation
    if diagram_count >= 3:
        return LayoutRecommendation(
            recommended_layout_id="diagram_heavy",
            reason="Project has many diagrams - diagram heavy layout recommended",
            confidence=0.9
        )

    if plan_count >= 1 and section_count >= 1 and render_count >= 1:
        return LayoutRecommendation(
            recommended_layout_id="plan_section_render",
            reason="Project has plans, sections and renders - technical layout recommended",
            confidence=0.85
        )

    if render_count >= 3:
        return LayoutRecommendation(
            recommended_layout_id="three_render_grid",
            reason="Project has multiple renders - grid layout recommended",
            confidence=0.8
        )

    if render_count >= 1:
        return LayoutRecommendation(
            recommended_layout_id="hero_render",
            reason="Hero render layout recommended for your project",
            confidence=0.75
        )

    if total_assets > 0:
        return LayoutRecommendation(
            recommended_layout_id="competition_board",
            reason="Competition board layout recommended",
            confidence=0.7
        )

    # Default
    return LayoutRecommendation(
        recommended_layout_id="hero_render",
        reason="Default layout - upload more assets for better recommendations",
        confidence=0.5
    )

@router.get("/styles/all")
async def get_all_styles():
    """Get all available style packs"""
    from services.styles import STYLE_PACKS
    return STYLE_PACKS
