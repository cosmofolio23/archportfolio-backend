from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from datetime import datetime
from models import ProjectCreate, ProjectUpdate, ProjectResponse
from routes.auth import verify_token
from database import supabase

router = APIRouter()

# ==================== Routes ====================

@router.get("", response_model=List[ProjectResponse])
async def list_projects(current_user: dict = Depends(verify_token)):
    """List all projects for current user"""
    try:
        response = supabase.table("projects").select("*").eq("user_id", current_user["user_id"]).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("", response_model=ProjectResponse)
async def create_project(req: ProjectCreate, current_user: dict = Depends(verify_token)):
    """Create new project"""
    try:
        project_data = {
            "user_id": current_user["user_id"],
            "title": req.title,
            "description": req.description,
            "project_type": req.project_type.value,
            "status": "draft",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        response = supabase.table("projects").insert(project_data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, current_user: dict = Depends(verify_token)):
    """Get project details"""
    try:
        response = supabase.table("projects").select("*").eq("id", project_id).eq("user_id", current_user["user_id"]).execute()
        if response.data:
            return response.data[0]
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, req: ProjectUpdate, current_user: dict = Depends(verify_token)):
    """Update project"""
    try:
        update_data = req.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow().isoformat()
        if "project_type" in update_data:
            update_data["project_type"] = update_data["project_type"].value

        response = supabase.table("projects").update(update_data).eq("id", project_id).eq("user_id", current_user["user_id"]).execute()
        if response.data:
            return response.data[0]
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str, current_user: dict = Depends(verify_token)):
    """Delete project"""
    try:
        response = supabase.table("projects").delete().eq("id", project_id).eq("user_id", current_user["user_id"]).execute()
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
