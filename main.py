import os
import sys
from dotenv import load_dotenv

# Load environment variables BEFORE importing config
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import settings

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import routes
from routes import auth, projects, assets, portfolios, layouts

def init_database():
    """Create all tables on startup if they don't exist"""
    from database import supabase
    if not supabase:
        print("⚠️ Supabase not initialized, skipping table creation")
        return

    tables_sql = [
        """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            project_type TEXT DEFAULT 'residential',
            status TEXT DEFAULT 'draft',
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS assets (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            asset_type TEXT,
            file_url TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_size INTEGER,
            upload_order INTEGER DEFAULT 0,
            analysis JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS portfolios (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            layout_id TEXT,
            style_pack TEXT,
            page_structure JSONB,
            variant_number INTEGER DEFAULT 1,
            generated_html TEXT,
            pdf_url TEXT,
            status TEXT DEFAULT 'ready',
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
    ]

    for sql in tables_sql:
        try:
            supabase.rpc("exec_sql", {"sql": sql.strip()}).execute()
        except Exception as e:
            print(f"Table creation note: {e}")

    print("✅ Database tables initialized")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting CosmoFolio API...")
    init_database()
    yield
    # Shutdown
    print("Shutting down...")

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered Architecture Portfolio Generator",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware - allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ArchPortfolio API"}

# ==================== Routes ====================

# Auth routes
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])

# Project routes
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])

# Asset routes
app.include_router(assets.router, prefix="/api/assets", tags=["assets"])

# Portfolio routes
app.include_router(portfolios.router, prefix="/api/portfolios", tags=["portfolios"])

# Layout routes
app.include_router(layouts.router, prefix="/api/layouts", tags=["layouts"])

# ==================== Root ====================

@app.get("/")
async def root():
    return {
        "message": "Welcome to ArchPortfolio Generator API",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
