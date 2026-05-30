"""
FastAPI app entry point for Vercel serverless
"""
import sys
import os
from fastapi import FastAPI

# Add parent directory to path so we can import main
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from main import app
except Exception as e:
    # Fallback if main.py fails to import
    print(f"Failed to import main: {e}")
    app = FastAPI()

    @app.get("/health")
    def health():
        return {"status": "healthy", "service": "ArchPortfolio API - Fallback"}

# This is what Vercel calls
__all__ = ["app"]
