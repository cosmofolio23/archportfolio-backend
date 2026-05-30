from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Header
from typing import List
from datetime import datetime
from models import AssetResponse, AssetListResponse, AssetTypeEnum
from routes.deps import get_current_user
from database import supabase
import uuid
import aiofiles
import os

router = APIRouter()

# ==================== File Upload to Firebase Storage ====================

async def save_uploaded_file(project_id: str, asset_type: str, file: UploadFile) -> tuple:
    """Upload file to Firebase Storage and return public URL"""
    try:
        file_id = str(uuid.uuid4())
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        file_content = await file.read()
        file_size = len(file_content)

        # Try Firebase Storage upload
        try:
            from firebase_admin import storage as fb_storage
            import firebase_admin

            bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET", "cosmo-folio-62c7f.firebasestorage.app")
            bucket = fb_storage.bucket(bucket_name)
            blob_path = f"assets/{project_id}/{asset_type}/{file_id}.{file_extension}"
            blob = bucket.blob(blob_path)

            content_type = file.content_type or "image/jpeg"
            blob.upload_from_string(file_content, content_type=content_type)
            blob.make_public()
            file_url = blob.public_url
            print(f"✅ Uploaded to Firebase Storage: {file_url}")

        except Exception as fb_error:
            print(f"⚠️ Firebase Storage failed ({fb_error}), using local fallback")
            # Fallback: save locally
            upload_dir = f"/tmp/uploads/{project_id}/{asset_type}"
            os.makedirs(upload_dir, exist_ok=True)
            file_path = f"{upload_dir}/{file_id}.{file_extension}"
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(file_content)
            file_url = f"/tmp/{file_path}"

        return file_url, file_size

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File upload failed: {str(e)}")

# ==================== Routes ====================

@router.post("/{project_id}/upload")
async def upload_assets(
    project_id: str,
    asset_type: AssetTypeEnum,
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload multiple assets for a project"""
    try:
        # Verify project ownership
        project_response = supabase.table("projects").select("*").eq("id", project_id).eq("user_id", current_user["user_id"]).execute()
        if not project_response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        uploaded_assets = []

        for idx, file in enumerate(files):
            file_url, file_size = await save_uploaded_file(project_id, asset_type.value, file)

            asset_data = {
                "id": str(uuid.uuid4()),
                "project_id": project_id,
                "asset_type": asset_type.value,
                "file_url": file_url,
                "file_name": file.filename,
                "file_size": file_size,
                "upload_order": idx,
                "analysis": None,
                "created_at": datetime.utcnow().isoformat()
            }

            response = supabase.table("assets").insert(asset_data).execute()
            if response.data:
                uploaded_assets.append(response.data[0])

        return {
            "message": f"Uploaded {len(uploaded_assets)} assets",
            "assets": uploaded_assets
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{project_id}/list", response_model=AssetListResponse)
async def list_assets(project_id: str, current_user: dict = Depends(get_current_user)):
    """List all assets for a project organized by type"""
    try:
        # Verify project ownership
        project_response = supabase.table("projects").select("*").eq("id", project_id).eq("user_id", current_user["user_id"]).execute()
        if not project_response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        response = supabase.table("assets").select("*").eq("project_id", project_id).execute()

        assets_by_type = {
            "render": [],
            "plan": [],
            "section": [],
            "diagram": [],
            "material": [],
            "detail": []
        }

        for asset in response.data:
            asset_type = asset.get("asset_type", "render")
            if asset_type in assets_by_type:
                assets_by_type[asset_type].append(asset)

        return AssetListResponse(**assets_by_type)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{project_id}/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(project_id: str, asset_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a specific asset"""
    try:
        # Verify project ownership
        project_response = supabase.table("projects").select("*").eq("id", project_id).eq("user_id", current_user["user_id"]).execute()
        if not project_response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        response = supabase.table("assets").delete().eq("id", asset_id).eq("project_id", project_id).execute()
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{project_id}/reorder")
async def reorder_assets(
    project_id: str,
    asset_order: List[dict],  # [{"asset_id": "...", "order": 0}, ...]
    current_user: dict = Depends(get_current_user)
):
    """Reorder assets"""
    try:
        # Verify project ownership
        project_response = supabase.table("projects").select("*").eq("id", project_id).eq("user_id", current_user["user_id"]).execute()
        if not project_response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        for item in asset_order:
            supabase.table("assets").update({"upload_order": item["order"]}).eq("id", item["asset_id"]).execute()

        return {"message": "Assets reordered"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{project_id}/analysis")
async def analyze_assets(project_id: str, current_user: dict = Depends(get_current_user)):
    """Analyze project assets for AI layout recommendation"""
    try:
        # Verify project ownership
        project_response = supabase.table("projects").select("*").eq("id", project_id).eq("user_id", current_user["user_id"]).execute()
        if not project_response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        response = supabase.table("assets").select("*").eq("project_id", project_id).execute()

        analysis = {
            "render_count": 0,
            "plan_count": 0,
            "section_count": 0,
            "diagram_count": 0,
            "material_count": 0,
            "detail_count": 0,
            "total_count": len(response.data)
        }

        for asset in response.data:
            asset_type = asset.get("asset_type", "render")
            key = f"{asset_type}_count"
            if key in analysis:
                analysis[key] += 1

        return analysis
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
