from fastapi import APIRouter, HTTPException, status, Header
from datetime import datetime
import json
from firebase_config import verify_firebase_token, firebase_app
from models import UserResponse
from database import supabase

router = APIRouter()

# ==================== Helper Functions ====================

def get_current_user_from_token(authorization: str = None):
    """Extract and verify Firebase token from Authorization header"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")

    token = authorization[7:]
    try:
        decoded_token = verify_firebase_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

# ==================== Routes ====================

@router.post("/signup")
async def signup(
    email: str,
    password: str,
    name: str = None
):
    """
    Register new user with Firebase Auth
    Note: User creation with password should be done on frontend with Firebase SDK
    This endpoint expects the frontend to have already created the Firebase user
    and sent the ID token in the next request
    """
    try:
        if not firebase_app:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Firebase not initialized"
            )

        # Create Firebase user
        user = firebase_app.auth().create_user(
            email=email,
            password=password
        )

        user_id = user.uid

        # Store user info in Supabase database
        if supabase:
            supabase.table("users").insert({
                "id": user_id,
                "email": email,
                "name": name,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).execute()

        return {
            "success": True,
            "message": "User created successfully",
            "user_id": user_id,
            "email": email
        }
    except Exception as e:
        error_msg = str(e)
        if "email-already-exists" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

@router.post("/verify-token")
async def verify_token(token: str):
    """
    Verify Firebase token and return user info
    Frontend calls this after Firebase authentication
    """
    try:
        decoded_token = verify_firebase_token(token)
        user_id = decoded_token.get("uid")
        email = decoded_token.get("email")

        # Get user from database
        if supabase:
            user_data = supabase.table("users").select("*").eq("id", user_id).execute()
            if user_data.data:
                user = user_data.data[0]
                return {
                    "success": True,
                    "user": {
                        "id": user["id"],
                        "email": user["email"],
                        "name": user.get("name"),
                        "created_at": user.get("created_at")
                    }
                }

        # If not in database, create entry
        if supabase:
            supabase.table("users").insert({
                "id": user_id,
                "email": email,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).execute()

        return {
            "success": True,
            "user": {
                "id": user_id,
                "email": email,
                "name": None,
                "created_at": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@router.get("/me")
async def get_current_user(authorization: str = Header(None)):
    """Get current user info from Firebase token"""
    try:
        decoded_token = get_current_user_from_token(authorization)
        user_id = decoded_token.get("uid")
        email = decoded_token.get("email")

        if supabase:
            user_data = supabase.table("users").select("*").eq("id", user_id).execute()
            if user_data.data:
                user = user_data.data[0]
                return UserResponse(
                    id=user["id"],
                    email=user["email"],
                    name=user.get("name"),
                    created_at=datetime.fromisoformat(user.get("created_at"))
                )

        return UserResponse(
            id=user_id,
            email=email,
            name=None,
            created_at=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

@router.post("/logout")
async def logout(authorization: str = Header(None)):
    """Logout (frontend handles token removal)"""
    try:
        get_current_user_from_token(authorization)
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
