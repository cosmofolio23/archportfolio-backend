"""
Design System / Style Packs for Portfolio Generation
7 professional style systems for architecture portfolios
"""

STYLE_PACKS = [
    {
        "id": "minimal_white",
        "name": "Minimal White",
        "description": "Clean, academic, minimal aesthetic",
        "typography": {
            "heading": "Montserrat 36px",
            "subtitle": "Montserrat 18px",
            "body": "Inter 11px",
            "caption": "Inter 9px"
        },
        "spacing": {
            "page_margin": "30mm",
            "section_gap": "20mm",
            "item_gap": "10mm"
        },
        "colors": {
            "background": "#FFFFFF",
            "text": "#000000",
            "accent": "#333333",
            "caption": "#666666"
        },
        "grid": {
            "columns": 12,
            "gutter": "8mm"
        },
        "borders": {
            "width": 0,
            "color": "#000000"
        },
        "page_number": "bottom_right"
    },
    {
        "id": "dark_studio",
        "name": "Dark Studio",
        "description": "Bold, dark, modern studio aesthetic",
        "typography": {
            "heading": "Futura 40px",
            "subtitle": "Futura 20px",
            "body": "Helvetica 11px",
            "caption": "Helvetica 9px"
        },
        "spacing": {
            "page_margin": "25mm",
            "section_gap": "25mm",
            "item_gap": "12mm"
        },
        "colors": {
            "background": "#1a1a1a",
            "text": "#FFFFFF",
            "accent": "#FF6B35",
            "caption": "#CCCCCC"
        },
        "grid": {
            "columns": 12,
            "gutter": "10mm"
        },
        "borders": {
            "width": 1,
            "color": "#FF6B35"
        },
        "page_number": "bottom_right"
    },
    {
        "id": "scandinavian",
        "name": "Scandinavian",
        "description": "Light wood tones, minimalist Nordic style",
        "typography": {
            "heading": "Didot 38px",
            "subtitle": "Didot 19px",
            "body": "Garamond 11px",
            "caption": "Garamond 9px"
        },
        "spacing": {
            "page_margin": "35mm",
            "section_gap": "22mm",
            "item_gap": "11mm"
        },
        "colors": {
            "background": "#FAF8F3",
            "text": "#2C3E50",
            "accent": "#C8A882",
            "caption": "#7F8C8D"
        },
        "grid": {
            "columns": 12,
            "gutter": "9mm"
        },
        "borders": {
            "width": 1,
            "color": "#C8A882"
        },
        "page_number": "bottom_center"
    },
    {
        "id": "architectural_journal",
        "name": "Architectural Journal",
        "description": "Magazine-style, serif typography, editorial",
        "typography": {
            "heading": "Bodoni 44px",
            "subtitle": "Bodoni 22px",
            "body": "Minion 11px",
            "caption": "Minion 8px"
        },
        "spacing": {
            "page_margin": "32mm",
            "section_gap": "18mm",
            "item_gap": "9mm"
        },
        "colors": {
            "background": "#FFFCF5",
            "text": "#1F1F1F",
            "accent": "#A67C52",
            "caption": "#696969"
        },
        "grid": {
            "columns": 12,
            "gutter": "8mm"
        },
        "borders": {
            "width": 2,
            "color": "#A67C52"
        },
        "page_number": "bottom_right"
    },
    {
        "id": "competition_board",
        "name": "Competition Board",
        "description": "Poster-style, bold colors, high contrast",
        "typography": {
            "heading": "Impact 48px",
            "subtitle": "Arial 26px",
            "body": "Arial 12px",
            "caption": "Arial 10px"
        },
        "spacing": {
            "page_margin": "20mm",
            "section_gap": "30mm",
            "item_gap": "15mm"
        },
        "colors": {
            "background": "#000000",
            "text": "#FFFFFF",
            "accent": "#00D9FF",
            "caption": "#FFFF00"
        },
        "grid": {
            "columns": 6,
            "gutter": "12mm"
        },
        "borders": {
            "width": 3,
            "color": "#00D9FF"
        },
        "page_number": "bottom_left"
    },
    {
        "id": "parametric",
        "name": "Parametric",
        "description": "Geometric, grids, monospace, technical",
        "typography": {
            "heading": "IBM Plex Mono 32px",
            "subtitle": "IBM Plex Mono 16px",
            "body": "IBM Plex Mono 10px",
            "caption": "IBM Plex Mono 8px"
        },
        "spacing": {
            "page_margin": "28mm",
            "section_gap": "14mm",
            "item_gap": "7mm"
        },
        "colors": {
            "background": "#F5F5F5",
            "text": "#0A0A0A",
            "accent": "#FF1744",
            "caption": "#424242"
        },
        "grid": {
            "columns": 16,
            "gutter": "6mm"
        },
        "borders": {
            "width": 1,
            "color": "#FF1744"
        },
        "page_number": "top_right"
    },
    {
        "id": "corporate",
        "name": "Corporate",
        "description": "Professional, minimal color, clean hierarchy",
        "typography": {
            "heading": "Roboto 40px",
            "subtitle": "Roboto 20px",
            "body": "Roboto 11px",
            "caption": "Roboto 9px"
        },
        "spacing": {
            "page_margin": "32mm",
            "section_gap": "20mm",
            "item_gap": "10mm"
        },
        "colors": {
            "background": "#FFFFFF",
            "text": "#1E3A5F",
            "accent": "#2E88D0",
            "caption": "#666666"
        },
        "grid": {
            "columns": 12,
            "gutter": "10mm"
        },
        "borders": {
            "width": 0,
            "color": "#2E88D0"
        },
        "page_number": "bottom_center"
    }
]

def get_style_pack(style_id: str):
    """Get specific style pack by ID"""
    return next((s for s in STYLE_PACKS if s["id"] == style_id), STYLE_PACKS[0])
