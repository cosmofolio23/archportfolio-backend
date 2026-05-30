from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from datetime import datetime, timedelta
import jwt
from config import settings
from models import SignUpRequest, LoginRequest, AuthResponse, UserResponse
from database import supabase

router = APIRouter()
security = HTTPBearer()

# ==================== JWT Utilities ====================

def create_access_token(user_id: str, email: str):
    """Create JWT token"""
    to_encode = {
        "sub": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthCredentials = Depends(security)):
    """Verify JWT token"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        email = payload.get("email")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        return {"user_id": user_id, "email": email}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# ==================== Routes ====================

@router.post("/signup", response_model=AuthResponse)
async def signup(req: SignUpRequest):
    """Register new user"""
    try:
        # Use Supabase Auth
        response = supabase.auth.sign_up({
            "email": req.email,
            "password": req.password,
        })

        if response.user:
            user_id = response.user.id

            # Store additional user info
            supabase.table("users").insert({
                "id": user_id,
                "email": req.email,
                "name": req.name,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).execute()

            token = create_access_token(user_id, req.email)
            return AuthResponse(
                access_token=token,
                user=UserResponse(
                    id=user_id,
                    email=req.email,
                    name=req.name,
                    created_at=datetime.utcnow()
                )
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    """Login user"""
    try:
        response = supabase.auth.sign_in_with_password({
            "email": req.email,
            "password": req.password,
        })

        if response.user:
            user_id = response.user.id

            # Get user info
            user_data = supabase.table("users").select("*").eq("id", user_id).execute()
            user = user_data.data[0] if user_data.data else {}

            token = create_access_token(user_id, req.email)
            return AuthResponse(
                access_token=token,
                user=UserResponse(
                    id=user_id,
                    email=req.email,
                    name=user.get("name"),
                    created_at=datetime.fromisoformat(user.get("created_at", datetime.utcnow().isoformat()))
                )
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user(current_user: dict = Depends(verify_token)):
    """Get current user info"""
    try:
        user_data = supabase.table("users").select("*").eq("id", current_user["user_id"]).execute()
        if user_data.data:
            user = user_data.data[0]
            return UserResponse(
                id=user["id"],
                email=user["email"],
                name=user.get("name"),
                created_at=datetime.fromisoformat(user.get("created_at"))
            )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

@router.post("/logout")
async def logout(current_user: dict = Depends(verify_token)):
    """Logout user"""
    try:
        supabase.auth.sign_out()
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
