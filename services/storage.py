"""
File storage integration for CosmoFolio
Phase 2: Task 2.2 - File storage, thumbnails, optimization
"""

import os
import asyncio
from typing import Optional, Tuple
from pathlib import Path
from io import BytesIO
from datetime import datetime, timedelta
import mimetypes
from uuid import uuid4
import logging

from PIL import Image
import boto3
from botocore.exceptions import ClientError
from supabase import create_client

logger = logging.getLogger(__name__)

# ==================== CONFIGURATION ====================

class StorageConfig:
    """Storage configuration"""
    # S3 Configuration
    AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET = os.getenv("S3_BUCKET", "cosmfolio-assets")
    S3_CDN_URL = os.getenv("S3_CDN_URL", f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com")

    # Supabase Configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "cosmfolio-assets")

    # File Configuration
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    MIN_FILE_SIZE = 100 * 1024  # 100KB
    ALLOWED_MIME_TYPES = {
        "image/jpeg": [".jpg", ".jpeg"],
        "image/png": [".png"],
        "image/webp": [".webp"],
        "image/tiff": [".tiff", ".tif"],
    }

    # Thumbnail Sizes
    THUMB_SIZES = {
        "thumb-250": (250, 250),
        "thumb-500": (500, 500),
        "preview-1200": (1200, 1200),
    }

    # Expiration
    PRESIGNED_URL_EXPIRATION = 3600  # 1 hour
    TEMP_FILE_RETENTION = 7  # days


# ==================== STORAGE CLIENT ====================

class StorageClient:
    """Handle file storage operations"""

    def __init__(self):
        """Initialize storage client"""
        self.config = StorageConfig()
        self.s3_client = None
        self.supabase = None
        self._init_clients()

    def _init_clients(self):
        """Initialize S3 and Supabase clients"""
        try:
            # S3 Client
            if self.config.AWS_ACCESS_KEY and self.config.AWS_SECRET_KEY:
                self.s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=self.config.AWS_ACCESS_KEY,
                    aws_secret_access_key=self.config.AWS_SECRET_KEY,
                    region_name=self.config.AWS_REGION,
                )
                logger.info("S3 client initialized")
            else:
                logger.warning("AWS credentials not configured, S3 disabled")

            # Supabase Client (alternative)
            if self.config.SUPABASE_URL and self.config.SUPABASE_KEY:
                self.supabase = create_client(
                    self.config.SUPABASE_URL,
                    self.config.SUPABASE_KEY
                )
                logger.info("Supabase storage client initialized")
            else:
                logger.warning("Supabase credentials not configured")

        except Exception as e:
            logger.error(f"Failed to initialize storage clients: {str(e)}")
            raise

    # ==================== FILE VALIDATION ====================

    def validate_file(self, file_data: bytes, mime_type: str, file_name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate file before upload
        Returns: (is_valid, error_message)
        """
        # Check file size
        if len(file_data) > self.config.MAX_FILE_SIZE:
            return False, f"File size exceeds maximum of {self.config.MAX_FILE_SIZE / 1024 / 1024:.0f}MB"

        if len(file_data) < self.config.MIN_FILE_SIZE:
            return False, f"File size below minimum of {self.config.MIN_FILE_SIZE / 1024:.0f}KB"

        # Check MIME type
        if mime_type not in self.config.ALLOWED_MIME_TYPES:
            return False, f"File type {mime_type} not allowed"

        # Check file extension
        file_ext = Path(file_name).suffix.lower()
        allowed_exts = self.config.ALLOWED_MIME_TYPES.get(mime_type, [])
        if file_ext not in allowed_exts:
            return False, f"File extension {file_ext} not allowed for {mime_type}"

        # Basic magic number validation
        if not self._validate_image_magic(file_data, mime_type):
            return False, "Invalid image file"

        return True, None

    def _validate_image_magic(self, file_data: bytes, mime_type: str) -> bool:
        """Validate image magic numbers"""
        magic_numbers = {
            "image/jpeg": [b"\xff\xd8\xff"],
            "image/png": [b"\x89PNG"],
            "image/webp": [b"RIFF"],
        }

        magic = magic_numbers.get(mime_type, [])
        for m in magic:
            if file_data.startswith(m):
                return True
        return False

    # ==================== IMAGE PROCESSING ====================

    async def process_image(
        self,
        file_data: bytes,
        mime_type: str
    ) -> dict:
        """
        Process image: extract metadata, generate thumbnails
        Returns: {width, height, thumbnails{size: bytes}}
        """
        try:
            # Open image
            image = Image.open(BytesIO(file_data))

            # Get dimensions
            width, height = image.size
            aspect_ratio = width / height if height > 0 else 1.0

            # Convert to RGB if needed (for JPEG conversion)
            if image.mode in ("RGBA", "LA", "P"):
                rgb_image = Image.new("RGB", image.size, (255, 255, 255))
                rgb_image.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
                image = rgb_image

            # Generate thumbnails
            thumbnails = {}
            for size_name, (size_w, size_h) in self.config.THUMB_SIZES.items():
                thumb = await self._generate_thumbnail(image, size_w, size_h, mime_type)
                thumbnails[size_name] = thumb

            return {
                "width": width,
                "height": height,
                "aspect_ratio": round(aspect_ratio, 2),
                "thumbnails": thumbnails,
            }

        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            raise

    async def _generate_thumbnail(
        self,
        image: Image.Image,
        width: int,
        height: int,
        mime_type: str
    ) -> bytes:
        """Generate thumbnail of specified size"""
        try:
            # Resize with aspect ratio preservation
            image.thumbnail((width, height), Image.Resampling.LANCZOS)

            # Convert to bytes
            thumb_io = BytesIO()
            # Save as WebP for better compression, fallback to JPEG
            save_format = "WEBP" if mime_type != "image/png" else "PNG"
            quality = 80 if save_format == "WEBP" else 85

            image.save(
                thumb_io,
                format=save_format,
                quality=quality,
                optimize=True
            )

            thumb_io.seek(0)
            return thumb_io.getvalue()

        except Exception as e:
            logger.error(f"Error generating thumbnail: {str(e)}")
            raise

    # ==================== UPLOAD OPERATIONS ====================

    async def upload_asset(
        self,
        file_data: bytes,
        file_name: str,
        mime_type: str,
        portfolio_id: str,
        asset_id: str,
        thumbnails: dict
    ) -> dict:
        """
        Upload asset and thumbnails to S3
        Returns: {storage_path, thumb_path, preview_path}
        """
        try:
            # Generate paths
            base_path = f"portfolios/{portfolio_id}/assets/{asset_id}"
            storage_path = f"{base_path}/original{Path(file_name).suffix.lower()}"
            thumb_path = f"{base_path}/thumb-250.webp"
            preview_path = f"{base_path}/preview-1200.webp"

            # Upload original
            if self.s3_client:
                await self._upload_to_s3(file_data, storage_path, mime_type)
            elif self.supabase:
                await self._upload_to_supabase(file_data, storage_path, mime_type)
            else:
                raise Exception("No storage client available")

            # Upload thumbnails
            if "thumb-250" in thumbnails:
                thumb_250 = thumbnails["thumb-250"]
                if self.s3_client:
                    await self._upload_to_s3(thumb_250, thumb_path, "image/webp")
                elif self.supabase:
                    await self._upload_to_supabase(thumb_250, thumb_path, "image/webp")

            if "preview-1200" in thumbnails:
                preview = thumbnails["preview-1200"]
                if self.s3_client:
                    await self._upload_to_s3(preview, preview_path, "image/webp")
                elif self.supabase:
                    await self._upload_to_supabase(preview, preview_path, "image/webp")

            return {
                "storage_path": storage_path,
                "thumb_path": thumb_path,
                "preview_path": preview_path,
            }

        except Exception as e:
            logger.error(f"Error uploading asset: {str(e)}")
            # Cleanup on failure
            await self.delete_asset(portfolio_id, asset_id)
            raise

    async def _upload_to_s3(
        self,
        file_data: bytes,
        file_path: str,
        mime_type: str
    ) -> None:
        """Upload file to S3"""
        try:
            # Set cache headers
            cache_control = "max-age=31536000" if "original" in file_path else "max-age=2592000"

            self.s3_client.put_object(
                Bucket=self.config.S3_BUCKET,
                Key=file_path,
                Body=file_data,
                ContentType=mime_type,
                CacheControl=cache_control,
                Metadata={
                    "uploaded-at": datetime.utcnow().isoformat(),
                },
            )
            logger.info(f"Uploaded to S3: {file_path}")

        except ClientError as e:
            logger.error(f"S3 upload error: {str(e)}")
            raise

    async def _upload_to_supabase(
        self,
        file_data: bytes,
        file_path: str,
        mime_type: str
    ) -> None:
        """Upload file to Supabase Storage"""
        try:
            self.supabase.storage.from_(self.config.SUPABASE_BUCKET).upload(
                file_path,
                file_data,
                {
                    "contentType": mime_type,
                    "cacheControl": "31536000" if "original" in file_path else "2592000",
                },
            )
            logger.info(f"Uploaded to Supabase: {file_path}")

        except Exception as e:
            logger.error(f"Supabase upload error: {str(e)}")
            raise

    # ==================== DOWNLOAD OPERATIONS ====================

    async def get_asset_url(
        self,
        storage_path: str,
        expiration_hours: int = 1
    ) -> str:
        """
        Get signed download URL for asset
        """
        try:
            if self.s3_client:
                return self._get_s3_url(storage_path, expiration_hours)
            elif self.supabase:
                return self._get_supabase_url(storage_path, expiration_hours)
            else:
                raise Exception("No storage client available")

        except Exception as e:
            logger.error(f"Error generating URL: {str(e)}")
            raise

    def _get_s3_url(self, storage_path: str, expiration_hours: int) -> str:
        """Get presigned S3 URL"""
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.config.S3_BUCKET,
                    "Key": storage_path,
                },
                ExpiresIn=expiration_hours * 3600,
            )
            return url
        except ClientError as e:
            logger.error(f"Error generating S3 URL: {str(e)}")
            raise

    def _get_supabase_url(self, storage_path: str, expiration_hours: int) -> str:
        """Get Supabase Storage URL"""
        try:
            response = self.supabase.storage.from_(
                self.config.SUPABASE_BUCKET
            ).create_signed_url(
                storage_path,
                expiration_hours * 3600
            )
            return response["signedURL"]
        except Exception as e:
            logger.error(f"Error generating Supabase URL: {str(e)}")
            raise

    async def get_public_url(self, storage_path: str) -> str:
        """Get public URL for asset (CDN)"""
        if self.s3_client:
            return f"{self.config.S3_CDN_URL}/{storage_path}"
        elif self.supabase:
            return self.supabase.storage.from_(
                self.config.SUPABASE_BUCKET
            ).get_public_url(storage_path)["publicURL"]
        else:
            raise Exception("No storage client available")

    # ==================== DELETE OPERATIONS ====================

    async def delete_asset(self, portfolio_id: str, asset_id: str) -> None:
        """Delete asset and all thumbnails"""
        try:
            base_path = f"portfolios/{portfolio_id}/assets/{asset_id}"

            # List and delete all files in asset directory
            if self.s3_client:
                await self._delete_from_s3(base_path)
            elif self.supabase:
                await self._delete_from_supabase(base_path)

            logger.info(f"Deleted asset: {asset_id}")

        except Exception as e:
            logger.error(f"Error deleting asset: {str(e)}")
            raise

    async def _delete_from_s3(self, prefix: str) -> None:
        """Delete all files with given prefix from S3"""
        try:
            # List objects
            response = self.s3_client.list_objects_v2(
                Bucket=self.config.S3_BUCKET,
                Prefix=prefix,
            )

            # Delete objects
            if "Contents" in response:
                objects = [{"Key": obj["Key"]} for obj in response["Contents"]]
                if objects:
                    self.s3_client.delete_objects(
                        Bucket=self.config.S3_BUCKET,
                        Delete={"Objects": objects},
                    )
                    logger.info(f"Deleted {len(objects)} files from S3")

        except ClientError as e:
            logger.error(f"Error deleting from S3: {str(e)}")
            raise

    async def _delete_from_supabase(self, prefix: str) -> None:
        """Delete all files with given prefix from Supabase"""
        try:
            # List files
            files = self.supabase.storage.from_(
                self.config.SUPABASE_BUCKET
            ).list(prefix)

            # Delete files
            if files:
                file_paths = [f["name"] for f in files]
                self.supabase.storage.from_(
                    self.config.SUPABASE_BUCKET
                ).remove(file_paths)
                logger.info(f"Deleted {len(file_paths)} files from Supabase")

        except Exception as e:
            logger.error(f"Error deleting from Supabase: {str(e)}")
            raise

    # ==================== UTILITY OPERATIONS ====================

    async def get_asset_metadata(
        self,
        file_data: bytes,
        file_name: str
    ) -> dict:
        """
        Extract metadata from asset
        Returns: {width, height, aspect_ratio, exif_data, color_space}
        """
        try:
            image = Image.open(BytesIO(file_data))

            # Basic metadata
            metadata = {
                "width": image.width,
                "height": image.height,
                "aspect_ratio": round(image.width / image.height, 2),
                "format": image.format,
                "mode": image.mode,
            }

            # EXIF data (if available)
            try:
                exif = image._getexif()
                if exif:
                    metadata["exif"] = {
                        "camera": exif.get(271, "Unknown"),  # Make
                        "model": exif.get(272, "Unknown"),   # Model
                        "software": exif.get(305, "Unknown"), # Software
                    }
            except Exception:
                pass

            return metadata

        except Exception as e:
            logger.error(f"Error extracting metadata: {str(e)}")
            return {}


# ==================== SINGLETON INSTANCE ====================

_storage_client = None

def get_storage_client() -> StorageClient:
    """Get or create storage client singleton"""
    global _storage_client
    if _storage_client is None:
        _storage_client = StorageClient()
    return _storage_client
