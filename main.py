from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import settings
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import routes
from routes import auth, projects, assets, portfolios, layouts

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting ArchPortfolio Generator API...")
    yield
    # Shutdown
    print("Shutting down...")

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered Architecture Portfolio Generator",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
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
