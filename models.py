from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# ==================== Enums ====================

class ProjectTypeEnum(str, Enum):
    cultural_center = "cultural_center"
    residential = "residential"
    office = "office"
    retail = "retail"
    hospitality = "hospitality"
    educational = "educational"
    mixed_use = "mixed_use"
    other = "other"

class AssetTypeEnum(str, Enum):
    render = "render"
    plan = "plan"
    section = "section"
    diagram = "diagram"
    material = "material"
    detail = "detail"

class StylePackEnum(str, Enum):
    minimal_white = "minimal_white"
    dark_studio = "dark_studio"
    scandinavian = "scandinavian"
    architectural_journal = "architectural_journal"
    competition_board = "competition_board"
    parametric = "parametric"
    corporate = "corporate"

class GridModeEnum(str, Enum):
    strict = "strict"
    flexible = "flexible"

# ==================== Auth ====================

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str]
    created_at: datetime

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# ==================== Projects ====================

class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    project_type: ProjectTypeEnum = ProjectTypeEnum.residential

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    project_type: Optional[ProjectTypeEnum] = None
    status: Optional[str] = None

class ProjectResponse(BaseModel):
    id: str
    user_id: str
    title: str
    description: Optional[str]
    project_type: str
    status: str
    created_at: datetime
    updated_at: datetime

# ==================== Assets ====================

class AssetAnalysis(BaseModel):
    colors: Optional[List[str]] = None
    composition: Optional[str] = None
    quality: Optional[float] = None
    content_type: Optional[str] = None

class AssetCreate(BaseModel):
    asset_type: AssetTypeEnum
    file_name: str
    file_size: int

class AssetResponse(BaseModel):
    id: str
    project_id: str
    asset_type: str
    file_url: str
    file_name: str
    file_size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    analysis: Optional[Dict[str, Any]] = None
    upload_order: Optional[int] = 0
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True, "extra": "ignore"}

class AssetListResponse(BaseModel):
    render: List[AssetResponse] = []
    plan: List[AssetResponse] = []
    section: List[AssetResponse] = []
    diagram: List[AssetResponse] = []
    material: List[AssetResponse] = []
    detail: List[AssetResponse] = []

# ==================== Layouts ====================

class LayoutRegion(BaseModel):
    type: str  # hero_image, grid, text, etc.
    assets: Optional[List[str]] = None
    x: float
    y: float
    w: float
    h: float
    aspect: Optional[str] = None
    position: Optional[str] = None  # cover, contain, etc.

class LayoutPage(BaseModel):
    page_num: int
    regions: List[LayoutRegion]

class LayoutDefinition(BaseModel):
    id: str
    name: str
    description: str
    pages: List[LayoutPage]
    thumbnail: Optional[str] = None

class LayoutResponse(BaseModel):
    layout: LayoutDefinition
    recommended: bool = False

# ==================== Design Systems ====================

class Typography(BaseModel):
    heading: str
    subtitle: str
    body: str
    caption: str

class Spacing(BaseModel):
    page_margin: str
    section_gap: str
    item_gap: str

class Colors(BaseModel):
    background: str
    text: str
    accent: str
    caption: str

class Grid(BaseModel):
    columns: int
    gutter: str

class StylePack(BaseModel):
    id: str
    name: str
    typography: Typography
    spacing: Spacing
    colors: Colors
    grid: Grid
    borders: Dict[str, Any]
    page_number: str

# ==================== Portfolio Generation ====================

class PortfolioPageComponent(BaseModel):
    type: str  # render, plan, section, diagram, text, etc.
    asset_id: Optional[str] = None
    content: Optional[str] = None
    position: Optional[str] = None

class PortfolioPage(BaseModel):
    page_num: int
    title: Optional[str] = None
    components: List[PortfolioPageComponent]
    notes: Optional[str] = None

class GeneratePortfolioRequest(BaseModel):
    layout_id: str
    style_pack: StylePackEnum
    grid_mode: GridModeEnum = GridModeEnum.strict
    font_pair: Optional[str] = None
    variant_count: int = Field(1, ge=1, le=10)

class PortfolioResponse(BaseModel):
    id: str
    project_id: str
    layout_id: str
    style_pack: str
    page_structure: List[PortfolioPage]
    grid_mode: str
    variant_number: int
    status: str
    pdf_url: Optional[str]
    web_url: Optional[str]
    created_at: datetime

# ==================== Export ====================

class ExportRequest(BaseModel):
    export_type: str  # pdf, web, social

class ExportResponse(BaseModel):
    export_type: str
    status: str
    file_url: Optional[str]
    created_at: datetime

# ==================== Recommendations ====================

class AssetCountAnalysis(BaseModel):
    render_count: int
    plan_count: int
    section_count: int
    diagram_count: int

class LayoutRecommendation(BaseModel):
    recommended_layout_id: str
    reason: str
    confidence: float
