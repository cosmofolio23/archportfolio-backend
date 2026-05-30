from fastapi import APIRouter, HTTPException, status, Header
from typing import List
from datetime import datetime
import uuid
from models import ProjectCreate, ProjectUpdate, ProjectResponse
from firebase_config import verify_firebase_token
from database import supabase

router = APIRouter()

def get_current_user(authorization: str = None):
    """Get current user from Firebase token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    token = authorization[7:]
    try:
        decoded = verify_firebase_token(token)
        return {"user_id": decoded.get("uid"), "email": decoded.get("email")}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

# ==================== Routes ====================

@router.get("", response_model=List[ProjectResponse])
async def list_projects(authorization: str = Header(None)):
    current_user = get_current_user(authorization)
    try:
        response = supabase.table("projects").select("*").eq("user_id", current_user["user_id"]).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("", response_model=ProjectResponse)
async def create_project(req: ProjectCreate, authorization: str = Header(None)):
    current_user = get_current_user(authorization)
    try:
        project_data = {
            "id": str(uuid.uuid4()),
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
async def get_project(project_id: str, authorization: str = Header(None)):
    current_user = get_current_user(authorization)
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
async def update_project(project_id: str, req: ProjectUpdate, authorization: str = Header(None)):
    current_user = get_current_user(authorization)
    try:
        update_data = req.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow().isoformat()
        if "project_type" in update_data and update_data["project_type"]:
            update_data["project_type"] = update_data["project_type"].value
        response = supabase.table("projects").update(update_data).eq("id", project_id).eq("user_id", current_user["user_id"]).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{project_id}")
async def delete_project(project_id: str, authorization: str = Header(None)):
    current_user = get_current_user(authorization)
    try:
        supabase.table("projects").delete().eq("id", project_id).eq("user_id", current_user["user_id"]).execute()
        return {"message": "Project deleted"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
