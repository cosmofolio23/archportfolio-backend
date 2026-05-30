"""
Asset preview and thumbnail service
Phase 2: Task 2.5 - Preview generation, thumbnails, lazy loading
"""

import logging
import asyncio
from typing import Optional, Dict, Any, Tuple
from io import BytesIO
from datetime import datetime, timedelta
import base64

from PIL import Image, ImageFilter, ImageDraw
import httpx

from database import supabase

logger = logging.getLogger(__name__)

# ==================== CONFIGURATION ====================

class PreviewConfig:
    """Preview configuration"""
    # Thumbnail sizes
    THUMBNAIL_SIZES = {
        "thumb-250": (250, 250),
        "thumb-500": (500, 500),
        "preview-1200": (1200, 1200),
    }

    # Blur-up placeholder settings
    BLUR_SIZE = (40, 40)
    BLUR_RADIUS = 20
    BLUR_QUALITY = 60

    # Cache control
    CACHE_DURATION_DAYS = 365
    BROWSER_CACHE_SECONDS = 31536000  # 1 year

    # Format preferences
    PREFERRED_FORMAT = "webp"
    FALLBACK_FORMAT = "jpeg"
    QUALITY_LEVELS = {
        "low": 60,
        "medium": 75,
        "high": 85,
    }


# ==================== PREVIEW SERVICE ====================

class AssetPreviewService:
    """Handle asset previews, thumbnails, and lazy loading"""

    def __init__(self):
        """Initialize preview service"""
        self.config = PreviewConfig()
        self.supabase = supabase

    # ==================== BLUR-UP PLACEHOLDERS ====================

    async def generate_blur_placeholder(
        self,
        image_data: bytes,
        format: str = "webp",
        quality: int = 60
    ) -> bytes:
        """
        Generate low-quality placeholder for blur-up loading

        Returns: Image bytes (data URL ready)
        """
        try:
            # Open image
            image = Image.open(BytesIO(image_data))

            # Convert to RGB if needed
            if image.mode in ("RGBA", "LA", "P"):
                rgb_image = Image.new("RGB", image.size, (255, 255, 255))
                rgb_image.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
                image = rgb_image

            # Resize to small size
            image.thumbnail(self.config.BLUR_SIZE, Image.Resampling.LANCZOS)

            # Apply blur filter
            image = image.filter(ImageFilter.GaussianBlur(radius=self.config.BLUR_RADIUS))

            # Save to bytes
            output = BytesIO()
            image.save(
                output,
                format=format.upper() if format.lower() != "jpg" else "JPEG",
                quality=quality,
                optimize=True
            )
            output.seek(0)
            return output.getvalue()

        except Exception as e:
            logger.error(f"Error generating blur placeholder: {str(e)}")
            raise

    async def generate_blur_data_url(
        self,
        image_data: bytes,
        quality: int = 60
    ) -> str:
        """
        Generate data URL for blur-up placeholder

        Format: data:image/webp;base64,...
        """
        try:
            blur_bytes = await self.generate_blur_placeholder(
                image_data,
                format="webp",
                quality=quality
            )
            b64_data = base64.b64encode(blur_bytes).decode("utf-8")
            return f"data:image/webp;base64,{b64_data}"

        except Exception as e:
            logger.error(f"Error generating blur data URL: {str(e)}")
            raise

    # ==================== DOMINANT COLOR ====================

    async def get_dominant_color(
        self,
        image_data: bytes,
        size: Tuple[int, int] = (50, 50)
    ) -> Dict[str, Any]:
        """
        Get dominant color from image for placeholder

        Returns: {color: "#RRGGBB", rgb: (r, g, b), hex: "RRGGBB"}
        """
        try:
            image = Image.open(BytesIO(image_data))

            # Convert to RGB
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Resize for performance
            image.thumbnail(size)

            # Get colors
            colors = image.getcolors(maxcolors=256)
            if not colors:
                return {"color": "#808080", "rgb": (128, 128, 128), "hex": "808080"}

            # Get most common color
            most_common = max(colors, key=lambda x: x[0])[1]

            # Format
            hex_color = "%02x%02x%02x" % most_common
            return {
                "color": f"#{hex_color}",
                "rgb": most_common,
                "hex": hex_color,
            }

        except Exception as e:
            logger.error(f"Error getting dominant color: {str(e)}")
            return {"color": "#808080", "rgb": (128, 128, 128), "hex": "808080"}

    # ==================== SRCSET GENERATION ====================

    async def generate_srcset(
        self,
        asset_id: str,
        base_url: str
    ) -> str:
        """
        Generate HTML srcset for responsive images

        Format: url 250w, url 500w, url 1200w
        """
        try:
            srcset_parts = []

            for size_name, (width, height) in self.config.THUMBNAIL_SIZES.items():
                url = f"{base_url}/api/portfolios/assets/{asset_id}/preview?size={size_name}"
                srcset_parts.append(f"{url} {width}w")

            return ", ".join(srcset_parts)

        except Exception as e:
            logger.error(f"Error generating srcset: {str(e)}")
            raise

    # ==================== PREVIEW METADATA ====================

    async def get_preview_metadata(
        self,
        asset_id: str,
        portfolio_id: str
    ) -> Dict[str, Any]:
        """
        Get comprehensive preview metadata for frontend

        Returns: {
            width, height, aspect_ratio,
            blur_placeholder, dominant_color,
            srcset, sizes,
            preview_urls
        }
        """
        try:
            # Get asset
            asset_response = self.supabase.table("assets").select("*").eq(
                "id", asset_id
            ).eq("portfolio_id", portfolio_id).execute()

            if not asset_response.data:
                raise ValueError(f"Asset not found: {asset_id}")

            asset = asset_response.data[0]

            # Get dominant color (from stored metadata if available)
            dominant_color = {
                "color": "#808080",
                "rgb": (128, 128, 128),
                "hex": "808080",
            }

            # Preview URLs for different sizes
            preview_urls = {
                "thumb-250": f"/api/portfolios/{portfolio_id}/assets/{asset_id}/preview?size=thumb-250",
                "thumb-500": f"/api/portfolios/{portfolio_id}/assets/{asset_id}/preview?size=thumb-500",
                "preview-1200": f"/api/portfolios/{portfolio_id}/assets/{asset_id}/preview?size=preview-1200",
                "original": asset.get("preview_path", asset.get("storage_path")),
            }

            return {
                "asset_id": asset_id,
                "width": asset.get("width"),
                "height": asset.get("height"),
                "aspect_ratio": asset.get("aspect_ratio", 1.0),
                "dominant_color": dominant_color,
                "preview_urls": preview_urls,
                "file_size": asset.get("file_size"),
                "mime_type": asset.get("mime_type"),
                "cache_control": {
                    "max_age": self.config.BROWSER_CACHE_SECONDS,
                    "immutable": True,
                },
            }

        except Exception as e:
            logger.error(f"Error getting preview metadata: {str(e)}")
            raise

    # ==================== RESPONSIVE IMAGES ====================

    async def get_responsive_image_config(
        self,
        asset_id: str,
        portfolio_id: str,
        base_url: str
    ) -> Dict[str, Any]:
        """
        Get complete responsive image configuration

        Includes: srcset, sizes, loading="lazy", etc.
        """
        try:
            metadata = await self.get_preview_metadata(asset_id, portfolio_id)
            srcset = await self.generate_srcset(asset_id, base_url)

            return {
                "src": metadata["preview_urls"]["preview-1200"],
                "srcSet": srcset,
                "sizes": "(max-width: 600px) 100vw, (max-width: 1200px) 50vw, 33vw",
                "alt": f"Asset {asset_id}",
                "loading": "lazy",
                "decoding": "async",
                "width": metadata["width"],
                "height": metadata["height"],
                "aspectRatio": metadata["aspect_ratio"],
            }

        except Exception as e:
            logger.error(f"Error getting responsive config: {str(e)}")
            raise

    # ==================== CACHE HEADERS ====================

    def get_cache_headers(
        self,
        max_age_seconds: Optional[int] = None,
        immutable: bool = False
    ) -> Dict[str, str]:
        """Generate cache control headers"""
        if max_age_seconds is None:
            max_age_seconds = self.config.BROWSER_CACHE_SECONDS

        cache_control = f"public, max-age={max_age_seconds}"
        if immutable:
            cache_control += ", immutable"

        return {
            "Cache-Control": cache_control,
            "ETag": f"W/\"{int(datetime.utcnow().timestamp())}\"",
        }

    # ==================== THUMBNAIL VARIANTS ====================

    async def get_thumbnail_variants(
        self,
        asset_id: str,
        base_url: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get all thumbnail variants with metadata

        Returns dictionary of size -> {url, width, height, quality}
        """
        variants = {}

        for size_name, (width, height) in self.config.THUMBNAIL_SIZES.items():
            variants[size_name] = {
                "url": f"{base_url}/api/portfolios/assets/{asset_id}/preview?size={size_name}",
                "width": width,
                "height": height,
                "quality": self.config.QUALITY_LEVELS["medium"],
            }

        return variants

    # ==================== FORMAT NEGOTIATION ====================

    def get_preferred_format(
        self,
        accept_header: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Negotiate image format based on Accept header

        Returns: (format, mime_type)
        """
        if not accept_header:
            return (self.config.PREFERRED_FORMAT, "image/webp")

        # Parse Accept header
        accepted_formats = {
            "image/webp": self.config.PREFERRED_FORMAT,
            "image/avif": "avif",
            "image/jpeg": "jpeg",
            "image/png": "png",
        }

        for mime_type, format_name in accepted_formats.items():
            if mime_type in accept_header:
                return (format_name, mime_type)

        # Fallback
        return (self.config.FALLBACK_FORMAT, "image/jpeg")

    # ==================== PREVIEW STATS ====================

    async def get_preview_stats(
        self,
        portfolio_id: str
    ) -> Dict[str, Any]:
        """Get preview generation statistics for portfolio"""
        try:
            assets_response = self.supabase.table("assets").select(
                "id, thumbnail_status, file_size"
            ).eq("portfolio_id", portfolio_id).is_("deleted_at", "null").execute()

            assets = assets_response.data or []

            stats = {
                "total_assets": len(assets),
                "thumbnail_status": {
                    "completed": 0,
                    "pending": 0,
                    "generating": 0,
                    "failed": 0,
                },
                "total_file_size_mb": round(
                    sum(a.get("file_size", 0) for a in assets) / (1024 * 1024), 2
                ),
                "estimated_thumbnail_size_mb": 0,  # Approximation
            }

            for asset in assets:
                status = asset.get("thumbnail_status", "pending")
                stats["thumbnail_status"][status] = stats["thumbnail_status"].get(status, 0) + 1

            # Rough estimation: ~20% of original size for thumbnails
            stats["estimated_thumbnail_size_mb"] = round(
                stats["total_file_size_mb"] * 0.2, 2
            )

            return stats

        except Exception as e:
            logger.error(f"Error getting preview stats: {str(e)}")
            return {}


# ==================== SINGLETON INSTANCE ====================

_preview_service = None

def get_preview_service() -> AssetPreviewService:
    """Get or create preview service singleton"""
    global _preview_service
    if _preview_service is None:
        _preview_service = AssetPreviewService()
    return _preview_service
