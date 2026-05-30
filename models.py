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
    layout_id: str = "hero_render"
    style_pack: str = "minimal_white"
    grid_mode: str = "strict"
    font_pair: Optional[str] = None
    variant_count: int = Field(1, ge=1, le=10)
    variant_number: Optional[int] = None

class PortfolioResponse(BaseModel):
    id: str
    project_id: str
    layout_id: str
    style_pack: str
    page_structure: Optional[Dict[str, Any]] = None
    grid_mode: Optional[str] = None
    variant_number: int
    status: str
    pdf_url: Optional[str] = None
    web_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True, "extra": "ignore"}

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

# ==================== NEW: Multi-Project Portfolio System ====================

# Page Size & Layout Enums
class PageSizeEnum(str, Enum):
    a4 = "a4"
    a3 = "a3"
    letter = "letter"
    tabloid = "tabloid"
    custom = "custom"

class OrientationEnum(str, Enum):
    portrait = "portrait"
    landscape = "landscape"

class MarginsEnum(str, Enum):
    compact = "compact"
    standard = "standard"
    generous = "generous"
    custom = "custom"

class PageTypeEnum(str, Enum):
    cover = "cover"
    project = "project"
    content = "content"
    credits = "credits"
    blank = "blank"

class AiToneEnum(str, Enum):
    academic = "academic"
    professional = "professional"
    creative = "creative"
    technical = "technical"
    marketing = "marketing"

# ==================== Portfolio Models ====================

class PortfolioSettingsRequest(BaseModel):
    title: str
    description: Optional[str] = None
    architect_name: str
    architect_bio: Optional[str] = None
    page_size: PageSizeEnum = PageSizeEnum.a4
    page_orientation: OrientationEnum = OrientationEnum.portrait
    margins: MarginsEnum = MarginsEnum.standard
    style_id: Optional[str] = None

class PortfolioSettingsResponse(BaseModel):
    id: str
    user_id: str
    title: str
    description: Optional[str]
    architect_name: str
    architect_bio: Optional[str]
    page_size: str
    page_orientation: str
    margins: str
    style_id: Optional[str]
    created_at: datetime
    updated_at: datetime

class PortfolioCreateRequest(BaseModel):
    title: str
    architect_name: str
    architect_bio: Optional[str] = None
    page_size: PageSizeEnum = PageSizeEnum.a4
    page_orientation: OrientationEnum = OrientationEnum.portrait
    margins: MarginsEnum = MarginsEnum.standard

class PortfolioDetailResponse(BaseModel):
    id: str
    user_id: str
    title: str
    architect_name: str
    architect_bio: Optional[str]
    page_size: str
    page_orientation: str
    margins: str
    style_id: Optional[str]
    is_published: bool
    view_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "extra": "ignore"}

# ==================== Project Models (Updated) ====================

class ProjectCreateRequest(BaseModel):
    portfolio_id: str
    title: str
    project_type: ProjectTypeEnum
    location: Optional[str] = None
    description: Optional[str] = None
    brief: Optional[str] = None
    status: Optional[str] = "concept"
    year: Optional[int] = None

class ProjectDetailResponse(BaseModel):
    id: str
    portfolio_id: str
    user_id: str
    title: str
    project_type: str
    location: Optional[str]
    description: Optional[str]
    brief: Optional[str]
    status: str
    year: Optional[int]
    order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "extra": "ignore"}

# ==================== Portfolio Page Models ====================

class LayoutConfigRequest(BaseModel):
    margins: Optional[Dict[str, int]] = None
    spacing: Optional[Dict[str, int]] = None
    image_aspect_ratio: Optional[str] = "cover"
    columns: Optional[int] = None

class PortfolioPageCreateRequest(BaseModel):
    page_number: int
    page_type: PageTypeEnum = PageTypeEnum.content
    layout_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    layout_config: Optional[LayoutConfigRequest] = None
    asset_ids: Optional[List[str]] = None
    style_override_id: Optional[str] = None

class PortfolioPageUpdateRequest(BaseModel):
    page_type: Optional[PageTypeEnum] = None
    layout_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    layout_config: Optional[LayoutConfigRequest] = None
    asset_ids: Optional[List[str]] = None
    style_override_id: Optional[str] = None

class PortfolioPageResponse(BaseModel):
    id: str
    portfolio_id: str
    page_number: int
    page_type: str
    layout_id: str
    title: Optional[str]
    description: Optional[str]
    layout_config: Optional[Dict[str, Any]]
    asset_ids: Optional[List[str]]
    style_override_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "extra": "ignore"}

# ==================== Style Models ====================

class ColorScheme(BaseModel):
    primary: str
    secondary: str
    tertiary: str
    neutral_light: str
    neutral_dark: str
    text_primary: str
    text_secondary: str
    accent: str

class TypographyConfig(BaseModel):
    heading_font: str
    heading_weight: str
    subheading_font: str
    subheading_weight: str
    body_font: str
    body_weight: str
    caption_font: str
    caption_weight: str

class DesignElements(BaseModel):
    border_style: str
    border_radius: int
    shadow_depth: int
    spacing_scale: str
    texture: Optional[str] = None

class BrandingConfig(BaseModel):
    logo_url: Optional[str] = None
    logo_placement: Optional[str] = None
    watermark_text: Optional[str] = None
    signature_url: Optional[str] = None

class StyleCreateRequest(BaseModel):
    name: str
    colors: ColorScheme
    typography: TypographyConfig
    design_elements: DesignElements
    branding: Optional[BrandingConfig] = None

class StyleResponse(BaseModel):
    id: str
    user_id: str
    portfolio_id: Optional[str]
    name: str
    is_custom: bool
    is_ai_generated: bool
    colors: ColorScheme
    typography: TypographyConfig
    design_elements: DesignElements
    branding: Optional[BrandingConfig]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "extra": "ignore"}

# ==================== Layout Template Models ====================

class LayoutConfig(BaseModel):
    grid_columns: int
    image_aspect_ratio: str
    spacing: Dict[str, int]
    component_arrangement: List[str]

class LayoutCreateRequest(BaseModel):
    id: str
    name: str
    description: str
    asset_types: List[str]
    max_assets: int
    preview_image_url: str
    config: LayoutConfig

class LayoutTemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    asset_types: List[str]
    max_assets: int
    preview_image_url: str
    config: Dict[str, Any]

    model_config = {"from_attributes": True, "extra": "ignore"}

# ==================== Project Text Models ====================

class ProjectTextCreateRequest(BaseModel):
    concept_statement: Optional[str] = None
    design_brief: Optional[str] = None
    design_strategy: Optional[str] = None
    project_description: Optional[str] = None
    site_context: Optional[str] = None
    program_description: Optional[str] = None
    key_features: Optional[List[str]] = None
    team_credits: Optional[Dict[str, str]] = None
    consultants: Optional[Dict[str, str]] = None
    software_used: Optional[List[str]] = None
    photography_credits: Optional[str] = None

class ProjectTextResponse(BaseModel):
    id: str
    project_id: str
    concept_statement: Optional[str]
    design_brief: Optional[str]
    design_strategy: Optional[str]
    project_description: Optional[str]
    site_context: Optional[str]
    program_description: Optional[str]
    key_features: Optional[List[str]]
    team_credits: Optional[Dict[str, str]]
    consultants: Optional[Dict[str, str]]
    software_used: Optional[List[str]]
    photography_credits: Optional[str]
    ai_tone: Optional[str]
    ai_generation_date: Optional[datetime]
    user_edited: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "extra": "ignore"}

# ==================== Image Caption Models ====================

class ImageCaptionResponse(BaseModel):
    id: str
    asset_id: str
    ai_generated_caption: Optional[str]
    user_custom_caption: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True, "extra": "ignore"}

# ==================== Export Models ====================

class PortfolioExportRequest(BaseModel):
    export_type: str  # pdf, web, images, social

class PortfolioExportResponse(BaseModel):
    id: str
    portfolio_id: str
    export_type: str
    export_url: str
    page_size: str
    file_size: int
    export_date: datetime
    downloaded_count: int

    model_config = {"from_attributes": True, "extra": "ignore"}

# ==================== Layout Recommendation Models ====================

class LayoutRecommendationRequest(BaseModel):
    render_count: int
    plan_count: int
    section_count: int
    diagram_count: int

class LayoutRecommendationResponse(BaseModel):
    layout_id: str
    confidence: float
    reason: str

# ==================== Asset Models (Phase 2) ====================

class AssetUploadRequest(BaseModel):
    asset_type: AssetTypeEnum
    file_name: str
    tags: Optional[List[str]] = None
    description: Optional[str] = None

class AssetMetadataRequest(BaseModel):
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    asset_type: Optional[AssetTypeEnum] = None

class AssetResponse(BaseModel):
    id: str
    project_id: Optional[str]
    portfolio_id: str
    file_name: str
    file_size: int
    file_type: str
    mime_type: str
    asset_type: str
    storage_path: str
    thumb_path: Optional[str]
    preview_url: Optional[str]
    width: Optional[int]
    height: Optional[int]
    description: Optional[str]
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    version: int

    model_config = {"from_attributes": True, "extra": "ignore"}

class AssetListResponse(BaseModel):
    items: List[AssetResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class AssetVersionResponse(BaseModel):
    id: str
    asset_id: str
    version_number: int
    file_path: str
    file_size: int
    created_at: datetime

    model_config = {"from_attributes": True, "extra": "ignore"}

class AssetVersionListResponse(BaseModel):
    asset_id: str
    versions: List[AssetVersionResponse]
    total_versions: int

class AssetTagResponse(BaseModel):
    id: str
    asset_id: str
    tag_name: str
    created_at: datetime

class BulkAssetUploadResponse(BaseModel):
    uploaded: int
    failed: int
    total: int
    errors: Optional[List[Dict[str, Any]]]
