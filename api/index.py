"""
FastAPI app entry point for Vercel serverless
"""
import sys
import os

# Add parent directory to path so we can import main
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

# This is what Vercel calls
__all__ = ["app"]
