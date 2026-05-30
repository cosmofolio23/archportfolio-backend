from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None

    # JWT
    SECRET_KEY: str = "change-me-to-random-secret-key"
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
        "https://frontend-fawn-kappa-36.vercel.app",
        "https://frontend-amobcnb0o-cosmo-atelier-s-projects.vercel.app",
        "https://*.vercel.app",
        "http://localhost",
        "*"
    ]

    # App
    DEBUG: bool = False
    APP_NAME: str = "ArchPortfolio Generator"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
