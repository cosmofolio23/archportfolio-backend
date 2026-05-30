---
title: ArchPortfolio Generator
emoji: 🏗️
colorFrom: blue
colorTo: indigo
sdk: docker
---

# ArchPortfolio Generator - Backend

FastAPI-based backend for AI-powered architecture portfolio generator.

## Setup

### 1. Prerequisites
- Python 3.11+
- Supabase account (free tier available at supabase.com)
- Replicate account (free tier available at replicate.com)

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Supabase

1. Create a Supabase project at https://supabase.com
2. Copy `.env.example` to `.env` and fill in:
   - `SUPABASE_URL`: Your Supabase URL
   - `SUPABASE_KEY`: Your Supabase anon key
   - `SECRET_KEY`: Generate with: `openssl rand -hex 32`

3. Run the SQL schema in Supabase SQL Editor:
   - See `database.py` for the SQL schema
   - This creates all required tables and indexes

### 4. Run Backend

```bash
python main.py
```

Server will be available at: http://localhost:8000

API Docs available at: http://localhost:8000/docs

## API Routes

### Auth
- `POST /api/auth/signup` - Register user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout

### Projects
- `GET /api/projects` - List user projects
- `POST /api/projects` - Create project
- `GET /api/projects/{id}` - Get project
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project

### Assets
- `POST /api/assets/{project_id}/upload` - Upload assets
- `GET /api/assets/{project_id}/list` - List assets by type
- `DELETE /api/assets/{project_id}/assets/{asset_id}` - Delete asset
- `POST /api/assets/{project_id}/reorder` - Reorder assets
- `GET /api/assets/{project_id}/analysis` - Analyze assets

### Layouts
- `GET /api/layouts` - Get all layouts
- `GET /api/layouts/{layout_id}` - Get layout details
- `POST /api/layouts/recommend` - Get layout recommendation

### Portfolios
- `POST /api/portfolios/{project_id}/generate` - Generate portfolio
- `GET /api/portfolios/{project_id}/list` - List portfolios
- `GET /api/portfolios/{portfolio_id}` - Get portfolio
- `DELETE /api/portfolios/{portfolio_id}` - Delete portfolio
- `GET /api/portfolios/{portfolio_id}/preview` - Get HTML preview

## Architecture

```
backend/
├── main.py                  # FastAPI app entry point
├── config.py                # Configuration & settings
├── database.py              # Supabase client & models
├── models.py                # Pydantic schemas
├── routes/
│   ├── auth.py             # Authentication routes
│   ├── projects.py         # Project CRUD routes
│   ├── assets.py           # Asset upload & management
│   ├── portfolios.py       # Portfolio generation
│   └── layouts.py          # Layout definitions & recommendations
├── services/
│   ├── styles.py           # Design system definitions
│   ├── pdf_generator.py    # PDF export (coming soon)
│   ├── html_generator.py   # HTML export (coming soon)
│   └── ai_generator.py     # Replicate integration (coming soon)
└── requirements.txt         # Python dependencies
```

## Features

### Current
- ✅ User authentication (Supabase Auth)
- ✅ Project management
- ✅ Asset upload & organization (renders, plans, sections, diagrams)
- ✅ Asset analysis (count by type)
- ✅ Layout definitions (7+ layouts)
- ✅ Design systems (7 style packs)
- ✅ Layout recommendation (heuristic-based)
- ✅ Portfolio generation (basic structure)

### Coming
- AI-powered portfolio generation (Replicate + Llama 2)
- HTML & PDF export
- Social media export (Instagram carousels, competition boards)
- Portfolio customization UI
- Batch generation with variations

## Free Tier Info

- **Supabase**: 500MB storage, unlimited read/write
- **Replicate**: Free tier available for Llama 2
- **Firebase Storage**: 1GB/month download
- **Vercel**: 100GB/month bandwidth

## Development

### Debug Mode
Set `DEBUG=True` in `.env` for development logging.

### Reset Database
To reset all data:
1. Go to Supabase Dashboard
2. Project Settings → Database
3. Click "Reset database"

## Next Steps

1. Set up frontend (Next.js)
2. Implement PDF/HTML export
3. Integrate Replicate + Llama 2 for AI generation
4. Add social media export
5. Deploy to Hugging Face Spaces (free)
