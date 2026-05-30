from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None

    # JWT
    SECRET_KEY: str = "default-secret-key-change-this"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Firebase/Cloudinary
    FIREBASE_API_KEY: Optional[str] = None
    CLOUDINARY_NAME: Optional[str] = None

    # Replicate (Llama 2)
    REPLICATE_API_TOKEN: Optional[str] = None

    # HuggingFace
    HF_API_KEY: Optional[str] = None

    # CORS
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://localhost:3000",
        "https://*.vercel.app"
    ]

    # App
    DEBUG: bool = False
    APP_NAME: str = "ArchPortfolio Generator"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()