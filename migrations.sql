-- CosmoFolio Database Migrations
-- Phase 1: Multi-Project Portfolio System

-- ==================== PORTFOLIOS TABLE ====================
CREATE TABLE IF NOT EXISTS portfolios (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  architect_name VARCHAR(255) NOT NULL,
  architect_bio TEXT,
  page_size VARCHAR(50) DEFAULT 'a4', -- a4, a3, letter, tabloid, custom
  page_orientation VARCHAR(50) DEFAULT 'portrait', -- portrait, landscape
  margins VARCHAR(50) DEFAULT 'standard', -- compact, standard, generous, custom
  style_id UUID, -- references styles table
  is_published BOOLEAN DEFAULT FALSE,
  view_count INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  CONSTRAINT valid_page_size CHECK (page_size IN ('a4', 'a3', 'letter', 'tabloid', 'custom')),
  CONSTRAINT valid_orientation CHECK (page_orientation IN ('portrait', 'landscape')),
  CONSTRAINT valid_margins CHECK (margins IN ('compact', 'standard', 'generous', 'custom'))
);

CREATE INDEX idx_portfolios_user_id ON portfolios(user_id);
CREATE INDEX idx_portfolios_created_at ON portfolios(created_at DESC);

-- ==================== PROJECTS TABLE (UPDATED) ====================
-- Keep existing table, add new columns for portfolio
ALTER TABLE IF EXISTS projects ADD COLUMN portfolio_id UUID REFERENCES portfolios(id) ON DELETE CASCADE;
ALTER TABLE IF EXISTS projects ADD COLUMN location VARCHAR(255);
ALTER TABLE IF EXISTS projects ADD COLUMN brief TEXT;
ALTER TABLE IF EXISTS projects ADD COLUMN status VARCHAR(50) DEFAULT 'concept';
ALTER TABLE IF EXISTS projects ADD COLUMN year INT;
ALTER TABLE IF EXISTS projects ADD COLUMN "order" INT DEFAULT 0;

-- Create table if it doesn't exist
CREATE TABLE IF NOT EXISTS projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id UUID REFERENCES portfolios(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  project_type VARCHAR(50),
  location VARCHAR(255),
  description TEXT,
  brief TEXT,
  status VARCHAR(50) DEFAULT 'concept',
  year INT,
  "order" INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_projects_portfolio_id ON projects(portfolio_id);
CREATE INDEX idx_projects_user_id ON projects(user_id);

-- ==================== PORTFOLIO_PAGES TABLE ====================
CREATE TABLE IF NOT EXISTS portfolio_pages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
  page_number INT NOT NULL,
  page_type VARCHAR(50) DEFAULT 'content', -- cover, project, content, credits, blank
  layout_id VARCHAR(100) NOT NULL, -- references layout template ID
  title VARCHAR(255),
  description TEXT,
  layout_config JSONB, -- {margins, spacing, image_aspect_ratio, columns}
  asset_ids JSONB DEFAULT '[]'::jsonb, -- array of asset IDs
  asset_positions JSONB, -- position of each asset
  style_override_id UUID, -- optional style override for this page
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  UNIQUE(portfolio_id, page_number),
  CONSTRAINT valid_page_type CHECK (page_type IN ('cover', 'project', 'content', 'credits', 'blank'))
);

CREATE INDEX idx_portfolio_pages_portfolio_id ON portfolio_pages(portfolio_id);
CREATE INDEX idx_portfolio_pages_layout_id ON portfolio_pages(layout_id);

-- ==================== STYLES TABLE ====================
CREATE TABLE IF NOT EXISTS styles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  portfolio_id UUID REFERENCES portfolios(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  is_custom BOOLEAN DEFAULT TRUE,
  is_ai_generated BOOLEAN DEFAULT FALSE,

  -- Colors JSONB
  colors JSONB NOT NULL DEFAULT '{}'::jsonb, -- {primary, secondary, tertiary, neutral_light, neutral_dark, text_primary, text_secondary, accent}

  -- Typography JSONB
  typography JSONB NOT NULL DEFAULT '{}'::jsonb, -- {heading_font, heading_weight, subheading_font, body_font, caption_font, line_heights}

  -- Design Elements JSONB
  design_elements JSONB NOT NULL DEFAULT '{}'::jsonb, -- {border_style, border_radius, shadow_depth, spacing_scale, texture}

  -- Branding JSONB
  branding JSONB DEFAULT '{}'::jsonb, -- {logo_url, logo_placement, watermark_text, signature_url}

  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_styles_user_id ON styles(user_id);
CREATE INDEX idx_styles_portfolio_id ON styles(portfolio_id);

-- ==================== LAYOUT TEMPLATES TABLE ====================
CREATE TABLE IF NOT EXISTS layout_templates (
  id VARCHAR(100) PRIMARY KEY, -- hero_section, grid_2col, etc.
  name VARCHAR(255) NOT NULL,
  description TEXT,
  asset_types JSONB DEFAULT '[]'::jsonb, -- [render, plan, section, etc.]
  max_assets INT DEFAULT 10,
  preview_image_url TEXT,
  config JSONB NOT NULL DEFAULT '{}'::jsonb, -- {grid_columns, image_aspect_ratio, spacing, component_arrangement}
  created_at TIMESTAMP DEFAULT NOW()
);

-- ==================== PROJECT_TEXT TABLE ====================
CREATE TABLE IF NOT EXISTS project_text (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

  -- Auto-generated sections
  concept_statement TEXT,
  design_brief TEXT,
  design_strategy TEXT,
  project_description TEXT,
  site_context TEXT,
  program_description TEXT,
  key_features JSONB DEFAULT '[]'::jsonb, -- array of feature strings

  -- Specifications
  specifications JSONB DEFAULT '{}'::jsonb, -- {area, budget, timeline, status}

  -- Credits
  team_credits JSONB DEFAULT '{}'::jsonb, -- {name: role}
  consultants JSONB DEFAULT '{}'::jsonb, -- {name: discipline}
  software_used JSONB DEFAULT '[]'::jsonb, -- array of software
  photography_credits VARCHAR(255),

  -- Generation metadata
  ai_tone VARCHAR(50) DEFAULT 'professional', -- academic, professional, creative, technical, marketing
  ai_generation_date TIMESTAMP,
  user_edited BOOLEAN DEFAULT FALSE,

  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_project_text_project_id ON project_text(project_id);

-- ==================== IMAGE_CAPTIONS TABLE ====================
CREATE TABLE IF NOT EXISTS image_captions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
  ai_generated_caption TEXT,
  user_custom_caption TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_image_captions_asset_id ON image_captions(asset_id);

-- ==================== PORTFOLIO_EXPORTS TABLE ====================
CREATE TABLE IF NOT EXISTS portfolio_exports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
  export_type VARCHAR(50) NOT NULL, -- pdf, web, images, social
  export_url TEXT NOT NULL,
  page_size VARCHAR(50), -- A4, A3, etc.
  file_size INT,
  export_date TIMESTAMP DEFAULT NOW(),
  downloaded_count INT DEFAULT 0
);

CREATE INDEX idx_portfolio_exports_portfolio_id ON portfolio_exports(portfolio_id);
CREATE INDEX idx_portfolio_exports_export_date ON portfolio_exports(export_date DESC);

-- ==================== LAYOUT_RECOMMENDATIONS TABLE ====================
CREATE TABLE IF NOT EXISTS layout_recommendations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  asset_counts JSONB NOT NULL DEFAULT '{}'::jsonb, -- {renders, plans, sections, diagrams}
  recommended_layouts JSONB NOT NULL DEFAULT '[]'::jsonb, -- [{layout_id, confidence, reason}]
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_layout_recommendations_project_id ON layout_recommendations(project_id);

-- ==================== ROW LEVEL SECURITY POLICIES ====================

-- Enable RLS on all tables
ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE portfolio_pages ENABLE ROW LEVEL SECURITY;
ALTER TABLE styles ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_text ENABLE ROW LEVEL SECURITY;
ALTER TABLE image_captions ENABLE ROW LEVEL SECURITY;
ALTER TABLE portfolio_exports ENABLE ROW LEVEL SECURITY;
ALTER TABLE layout_recommendations ENABLE ROW LEVEL SECURITY;

-- PORTFOLIOS: Users can only access their own portfolios
CREATE POLICY "Users can create portfolios" ON portfolios
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view their own portfolios" ON portfolios
  FOR SELECT USING (auth.uid() = user_id OR is_published = TRUE);

CREATE POLICY "Users can update their own portfolios" ON portfolios
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own portfolios" ON portfolios
  FOR DELETE USING (auth.uid() = user_id);

-- PROJECTS: Users can only access projects in their portfolios
CREATE POLICY "Users can create projects" ON projects
  FOR INSERT WITH CHECK (
    auth.uid() = user_id AND EXISTS (
      SELECT 1 FROM portfolios WHERE portfolios.id = projects.portfolio_id
      AND portfolios.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can view their project's data" ON projects
  FOR SELECT USING (
    auth.uid() = user_id OR EXISTS (
      SELECT 1 FROM portfolios WHERE portfolios.id = projects.portfolio_id
      AND portfolios.is_published = TRUE
    )
  );

CREATE POLICY "Users can update their projects" ON projects
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their projects" ON projects
  FOR DELETE USING (auth.uid() = user_id);

-- PORTFOLIO_PAGES: Access through portfolio
CREATE POLICY "Users can manage portfolio pages" ON portfolio_pages
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM portfolios WHERE portfolios.id = portfolio_pages.portfolio_id
      AND portfolios.user_id = auth.uid()
    )
  );

-- STYLES: Users can only access their own styles
CREATE POLICY "Users can manage their styles" ON styles
  FOR ALL USING (auth.uid() = user_id);

-- PROJECT_TEXT: Access through project
CREATE POLICY "Users can manage project text" ON project_text
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM projects WHERE projects.id = project_text.project_id
      AND projects.user_id = auth.uid()
    )
  );

-- IMAGE_CAPTIONS: Access through asset
CREATE POLICY "Users can manage image captions" ON image_captions
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM assets WHERE assets.id = image_captions.asset_id
    )
  );

-- PORTFOLIO_EXPORTS: Access through portfolio
CREATE POLICY "Users can manage exports" ON portfolio_exports
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM portfolios WHERE portfolios.id = portfolio_exports.portfolio_id
      AND portfolios.user_id = auth.uid()
    )
  );

-- LAYOUT_RECOMMENDATIONS: Access through project
CREATE POLICY "Users can view layout recommendations" ON layout_recommendations
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM projects WHERE projects.id = layout_recommendations.project_id
      AND projects.user_id = auth.uid()
    )
  );

-- ==================== INSERT DEFAULT LAYOUT TEMPLATES ====================

INSERT INTO layout_templates (id, name, description, asset_types, max_assets, config) VALUES
  ('hero_section', 'Hero Section', 'Full-width image with title overlay', '["render"]'::jsonb, 1, '{"grid_columns":1,"image_aspect_ratio":"cover","spacing":{"top":0,"bottom":40}}'),
  ('grid_2col', '2-Column Grid', '2-column equal width grid', '["render","plan","section"]'::jsonb, 4, '{"grid_columns":2,"image_aspect_ratio":"auto","spacing":{"gap":20}}'),
  ('grid_3col', '3-Column Grid', '3-column equal width grid', '["render","diagram"]'::jsonb, 6, '{"grid_columns":3,"image_aspect_ratio":"auto","spacing":{"gap":20}}'),
  ('grid_4col', '4-Column Grid', '4-column equal width grid', '["render","diagram","detail"]'::jsonb, 8, '{"grid_columns":4,"image_aspect_ratio":"square","spacing":{"gap":15}}'),
  ('plans_layout', 'Plans Layout', 'Large plan with secondary details', '["plan","section"]'::jsonb, 2, '{"grid_columns":1,"image_aspect_ratio":"auto","spacing":{"gap":30}}'),
  ('sections_layout', 'Sections Layout', 'Multiple sections arranged horizontally', '["section","diagram"]'::jsonb, 4, '{"grid_columns":2,"image_aspect_ratio":"auto","spacing":{"gap":20}}'),
  ('comparison_layout', 'Comparison Layout', 'Side-by-side comparison', '["render","plan"]'::jsonb, 2, '{"grid_columns":2,"image_aspect_ratio":"auto","spacing":{"gap":30}}'),
  ('timeline_layout', 'Timeline Layout', 'Chronological process', '["render","diagram","detail"]'::jsonb, 6, '{"grid_columns":2,"image_aspect_ratio":"auto","spacing":{"gap":20}}'),
  ('asymmetric_layout', 'Asymmetric Layout', 'Dynamic unequal layout', '["render","plan"]'::jsonb, 5, '{"grid_columns":3,"image_aspect_ratio":"auto","spacing":{"gap":20}}'),
  ('single_column', 'Single Column', 'One large centered image', '["render","plan","section"]'::jsonb, 1, '{"grid_columns":1,"image_aspect_ratio":"auto","spacing":{"top":40,"bottom":40}}'),
  ('mixed_layout', 'Mixed Layout', 'Combination of images and diagrams', '["render","diagram"]'::jsonb, 4, '{"grid_columns":2,"image_aspect_ratio":"auto","spacing":{"gap":25}}'),
  ('text_focus', 'Text Focus', 'Text-heavy with accent image', '["render"]'::jsonb, 1, '{"grid_columns":2,"image_aspect_ratio":"auto","spacing":{"gap":30}}')
ON CONFLICT (id) DO NOTHING;

-- ==================== MIGRATION COMPLETE ====================
-- All tables created successfully with proper constraints and RLS policies
