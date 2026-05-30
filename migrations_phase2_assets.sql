-- CosmoFolio Database Migrations - Phase 2: Asset Management
-- Asset upload, storage, versioning, and organization

-- ==================== ASSETS TABLE ====================
CREATE TABLE IF NOT EXISTS assets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,

  -- File information
  file_name VARCHAR(255) NOT NULL,
  original_file_name VARCHAR(255),
  file_size INT NOT NULL, -- bytes
  mime_type VARCHAR(50) DEFAULT 'image/jpeg', -- image/jpeg, image/png, image/webp, etc.

  -- Asset classification
  asset_type VARCHAR(50) NOT NULL, -- render, plan, section, diagram, detail, material

  -- Storage paths
  storage_path TEXT NOT NULL, -- s3://bucket/path/to/file
  thumb_path TEXT, -- s3://bucket/path/to/thumb.jpg (250px)
  preview_path TEXT, -- s3://bucket/path/to/preview.jpg (1200px)

  -- Image metadata
  width INT, -- image width in pixels
  height INT, -- image height in pixels
  aspect_ratio DECIMAL(5,2), -- width/height

  -- Additional metadata
  description TEXT,
  exif_data JSONB DEFAULT '{}'::jsonb, -- camera, lens, settings, etc.
  custom_metadata JSONB DEFAULT '{}'::jsonb, -- user-defined metadata

  -- Status
  upload_status VARCHAR(50) DEFAULT 'completed', -- uploading, completed, failed, processing
  thumbnail_status VARCHAR(50) DEFAULT 'pending', -- pending, generating, completed, failed

  -- Versioning
  version INT DEFAULT 1,
  is_latest BOOLEAN DEFAULT TRUE,

  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  deleted_at TIMESTAMP,

  CONSTRAINT valid_asset_type CHECK (asset_type IN ('render', 'plan', 'section', 'diagram', 'detail', 'material')),
  CONSTRAINT valid_upload_status CHECK (upload_status IN ('uploading', 'completed', 'failed', 'processing')),
  CONSTRAINT valid_thumbnail_status CHECK (thumbnail_status IN ('pending', 'generating', 'completed', 'failed'))
);

CREATE INDEX idx_assets_user_id ON assets(user_id);
CREATE INDEX idx_assets_portfolio_id ON assets(portfolio_id);
CREATE INDEX idx_assets_project_id ON assets(project_id);
CREATE INDEX idx_assets_asset_type ON assets(asset_type);
CREATE INDEX idx_assets_created_at ON assets(created_at DESC);
CREATE INDEX idx_assets_is_latest ON assets(is_latest) WHERE is_latest = TRUE;
CREATE INDEX idx_assets_deleted_at ON assets(deleted_at) WHERE deleted_at IS NULL;

-- ==================== ASSET_VERSIONS TABLE ====================
CREATE TABLE IF NOT EXISTS asset_versions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,

  -- Version tracking
  version_number INT NOT NULL,

  -- File information
  file_name VARCHAR(255) NOT NULL,
  file_size INT NOT NULL,
  mime_type VARCHAR(50),

  -- Storage paths
  file_path TEXT NOT NULL, -- s3://bucket/path/to/file_v2.jpg
  thumb_path TEXT,
  preview_path TEXT,

  -- Metadata for this version
  width INT,
  height INT,
  exif_data JSONB DEFAULT '{}'::jsonb,

  -- Change info
  change_reason VARCHAR(255),
  changed_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,

  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW(),

  CONSTRAINT unique_version UNIQUE(asset_id, version_number)
);

CREATE INDEX idx_asset_versions_asset_id ON asset_versions(asset_id);
CREATE INDEX idx_asset_versions_created_at ON asset_versions(created_at DESC);

-- ==================== ASSET_TAGS TABLE ====================
CREATE TABLE IF NOT EXISTS asset_tags (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,

  -- Tag information
  tag_name VARCHAR(100) NOT NULL,

  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW(),

  CONSTRAINT unique_tag_per_asset UNIQUE(asset_id, tag_name)
);

CREATE INDEX idx_asset_tags_asset_id ON asset_tags(asset_id);
CREATE INDEX idx_asset_tags_tag_name ON asset_tags(tag_name);

-- ==================== ASSET_USES TABLE ====================
-- Track where assets are used (which pages, in which layouts)
CREATE TABLE IF NOT EXISTS asset_uses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
  portfolio_page_id UUID NOT NULL REFERENCES portfolio_pages(id) ON DELETE CASCADE,

  -- Position information
  position_index INT, -- order in asset_ids array
  layout_position JSONB DEFAULT '{}'::jsonb, -- {x, y, width, height, rotation}

  -- Metadata
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  CONSTRAINT unique_asset_page_position UNIQUE(asset_id, portfolio_page_id, position_index)
);

CREATE INDEX idx_asset_uses_asset_id ON asset_uses(asset_id);
CREATE INDEX idx_asset_uses_portfolio_page_id ON asset_uses(portfolio_page_id);

-- ==================== ROW LEVEL SECURITY POLICIES ====================

-- Enable RLS on all asset tables
ALTER TABLE assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE asset_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE asset_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE asset_uses ENABLE ROW LEVEL SECURITY;

-- ASSETS: Users can only access their own portfolio's assets
CREATE POLICY "Users can upload assets to their portfolios" ON assets
  FOR INSERT WITH CHECK (
    auth.uid() = user_id AND EXISTS (
      SELECT 1 FROM portfolios WHERE portfolios.id = assets.portfolio_id
      AND portfolios.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can view their assets" ON assets
  FOR SELECT USING (
    auth.uid() = user_id OR EXISTS (
      SELECT 1 FROM portfolios WHERE portfolios.id = assets.portfolio_id
      AND portfolios.is_published = TRUE
    )
  );

CREATE POLICY "Users can update their assets" ON assets
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their assets" ON assets
  FOR DELETE USING (auth.uid() = user_id);

-- ASSET_VERSIONS: Access through asset ownership
CREATE POLICY "Users can manage asset versions" ON asset_versions
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM assets WHERE assets.id = asset_versions.asset_id
      AND assets.user_id = auth.uid()
    )
  );

-- ASSET_TAGS: Access through asset ownership
CREATE POLICY "Users can manage asset tags" ON asset_tags
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM assets WHERE assets.id = asset_tags.asset_id
      AND assets.user_id = auth.uid()
    )
  );

-- ASSET_USES: Access through portfolio ownership
CREATE POLICY "Users can manage asset uses" ON asset_uses
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM portfolio_pages
      INNER JOIN portfolios ON portfolios.id = portfolio_pages.portfolio_id
      WHERE portfolio_pages.id = asset_uses.portfolio_page_id
      AND portfolios.user_id = auth.uid()
    )
  );

-- ==================== MIGRATION COMPLETE ====================
-- All asset management tables created with proper constraints and RLS policies
