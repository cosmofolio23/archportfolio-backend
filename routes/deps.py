"""Shared auth dependency for all routes"""
from fastapi import HTTPException, status, Header
from firebase_config import verify_firebase_token

def get_current_user(authorization: str = Header(None)):
    """Get current user from Firebase token in Authorization header"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid token")
    token = authorization[7:]
    try:
        decoded = verify_firebase_token(token)
        return {"user_id": decoded.get("uid"), "email": decoded.get("email")}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
