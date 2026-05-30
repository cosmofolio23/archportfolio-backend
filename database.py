from supabase import create_client
from sqlalchemy import create_engine, Column, String, DateTime, Enum, Integer, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid
from config import settings

# Supabase Client - try to initialize, but don't fail if credentials are missing
supabase = None
print(f"📋 Config check:")
print(f"  SUPABASE_URL: {settings.SUPABASE_URL[:20] if settings.SUPABASE_URL else 'NOT SET'}...")
print(f"  SUPABASE_KEY: {settings.SUPABASE_KEY[:20] if settings.SUPABASE_KEY else 'NOT SET'}...")

try:
    if settings.SUPABASE_URL and settings.SUPABASE_KEY:
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        print("✅ Supabase initialized successfully")
    else:
        print("❌ SUPABASE_URL or SUPABASE_KEY not configured")
except Exception as e:
    print(f"❌ Supabase initialization failed: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

Base = declarative_base()

# ==================== Models ====================

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    project_type = Column(String, default="residential")  # cultural_center, residential, office, etc.
    status = Column(String, default="draft")  # draft, generating, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Asset(Base):
    __tablename__ = "assets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, nullable=False, index=True)
    asset_type = Column(String)  # render, plan, section, diagram, material, detail
    file_url = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    analysis = Column(JSON, nullable=True)  # color_palette, composition, etc.
    upload_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, nullable=False, index=True)
    layout_id = Column(String, nullable=False)
    style_pack = Column(String, default="minimal_white")  # design system name
    page_structure = Column(JSON)  # array of page objects
    grid_mode = Column(String, default="strict")  # strict or flexible
    font_pair = Column(String, default="sans_serif")
    color_override = Column(JSON, nullable=True)
    variant_number = Column(Integer, default=1)
    generated_html = Column(String, nullable=True)
    pdf_url = Column(String, nullable=True)
    web_url = Column(String, nullable=True)
    status = Column(String, default="generating")  # generating, ready, failed
    created_at = Column(DateTime, default=datetime.utcnow)


class ExportLog(Base):
    __tablename__ = "export_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    portfolio_id = Column(String, nullable=False, index=True)
    export_type = Column(String)  # pdf, web, social
    status = Column(String, default="pending")
    file_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ==================== Supabase SQL (run manually) ====================

SQL_SCHEMA = """
-- Create tables if not exists
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    project_type VARCHAR(50) DEFAULT 'residential',
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    asset_type VARCHAR(50),
    file_url TEXT NOT NULL,
    file_name VARCHAR(255),
    file_size INTEGER,
    width INTEGER,
    height INTEGER,
    analysis JSONB,
    upload_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS portfolios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    layout_id VARCHAR(100) NOT NULL,
    style_pack VARCHAR(50) DEFAULT 'minimal_white',
    page_structure JSONB,
    grid_mode VARCHAR(20) DEFAULT 'strict',
    font_pair VARCHAR(50) DEFAULT 'sans_serif',
    color_override JSONB,
    variant_number INTEGER DEFAULT 1,
    generated_html TEXT,
    pdf_url TEXT,
    web_url TEXT,
    status VARCHAR(50) DEFAULT 'generating',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS export_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    export_type VARCHAR(50),
    status VARCHAR(50) DEFAULT 'pending',
    file_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_assets_project_id ON assets(project_id);
CREATE INDEX IF NOT EXISTS idx_portfolios_project_id ON portfolios(project_id);
CREATE INDEX IF NOT EXISTS idx_export_logs_portfolio_id ON export_logs(portfolio_id);
"""

def init_supabase():
    """Initialize Supabase tables - run this once"""
    print("Run the SQL schema above in Supabase dashboard first!")
    pass


def get_db():
    """Dependency for database session"""
    # For Supabase, we use the client directly
    return supabase
