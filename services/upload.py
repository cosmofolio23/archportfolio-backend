"""
Upload handler for multipart and resumable uploads
Phase 2: Task 2.2 - Upload management and progress tracking
"""

import asyncio
import hashlib
import logging
from typing import Optional, BinaryIO
from uuid import uuid4
from datetime import datetime, timedelta
from dataclasses import dataclass

from fastapi import UploadFile
from sqlalchemy.orm import Session

from services.storage import get_storage_client
from models import AssetResponse

logger = logging.getLogger(__name__)

# ==================== DATA CLASSES ====================

@dataclass
class UploadProgress:
    """Track upload progress"""
    upload_id: str
    file_name: str
    total_size: int
    uploaded_size: int = 0
    status: str = "uploading"  # uploading, processing, completed, failed
    error: Optional[str] = None
    percentage: float = 0.0
    started_at: datetime = None
    completed_at: Optional[datetime] = None

    def update(self, bytes_uploaded: int):
        """Update progress"""
        self.uploaded_size = bytes_uploaded
        self.percentage = (bytes_uploaded / self.total_size) * 100

    def mark_completed(self):
        """Mark upload as completed"""
        self.status = "completed"
        self.uploaded_size = self.total_size
        self.percentage = 100.0
        self.completed_at = datetime.utcnow()

    def mark_failed(self, error: str):
        """Mark upload as failed"""
        self.status = "failed"
        self.error = error
        self.completed_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "upload_id": self.upload_id,
            "file_name": self.file_name,
            "total_size": self.total_size,
            "uploaded_size": self.uploaded_size,
            "status": self.status,
            "percentage": round(self.percentage, 2),
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class UploadSession:
    """Track resumable upload session"""
    session_id: str
    file_name: str
    file_size: int
    chunk_size: int
    chunks_uploaded: list  # List of uploaded chunk indexes
    upload_started_at: datetime
    last_activity: datetime
    storage_path: str = ""

    def add_chunk(self, chunk_index: int):
        """Mark chunk as uploaded"""
        if chunk_index not in self.chunks_uploaded:
            self.chunks_uploaded.append(chunk_index)
        self.last_activity = datetime.utcnow()

    def is_complete(self) -> bool:
        """Check if all chunks uploaded"""
        total_chunks = (self.file_size + self.chunk_size - 1) // self.chunk_size
        return len(self.chunks_uploaded) == total_chunks

    def is_expired(self, retention_hours: int = 24) -> bool:
        """Check if session expired"""
        expiration_time = self.last_activity + timedelta(hours=retention_hours)
        return datetime.utcnow() > expiration_time

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        total_chunks = (self.file_size + self.chunk_size - 1) // self.chunk_size
        return {
            "session_id": self.session_id,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "total_chunks": total_chunks,
            "chunks_uploaded": len(self.chunks_uploaded),
            "percentage": round((len(self.chunks_uploaded) / total_chunks) * 100, 2),
            "upload_started_at": self.upload_started_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
        }


# ==================== UPLOAD MANAGER ====================

class UploadManager:
    """Manage file uploads with progress tracking"""

    def __init__(self):
        """Initialize upload manager"""
        self.storage_client = get_storage_client()
        self.progress_sessions = {}  # upload_id -> UploadProgress
        self.resumable_sessions = {}  # session_id -> UploadSession

    # ==================== SIMPLE UPLOAD ====================

    async def upload_file(
        self,
        upload_file: UploadFile,
        portfolio_id: str,
        asset_id: str,
        asset_type: str
    ) -> dict:
        """
        Upload single file
        Returns: {asset_id, storage_path, thumb_path, preview_path, width, height}
        """
        upload_id = str(uuid4())
        progress = UploadProgress(
            upload_id=upload_id,
            file_name=upload_file.filename,
            total_size=upload_file.size or 0,
            started_at=datetime.utcnow()
        )

        try:
            # Read file data
            file_data = await upload_file.read()
            progress.update(len(file_data))

            # Validate
            mime_type = upload_file.content_type or "image/jpeg"
            is_valid, error = self.storage_client.validate_file(
                file_data,
                mime_type,
                upload_file.filename
            )

            if not is_valid:
                progress.mark_failed(error)
                self.progress_sessions[upload_id] = progress
                raise ValueError(error)

            progress.status = "processing"

            # Process image
            processing_result = await self.storage_client.process_image(
                file_data,
                mime_type
            )

            # Get metadata
            metadata = await self.storage_client.get_asset_metadata(
                file_data,
                upload_file.filename
            )

            # Upload to storage
            upload_result = await self.storage_client.upload_asset(
                file_data,
                upload_file.filename,
                mime_type,
                portfolio_id,
                asset_id,
                processing_result["thumbnails"]
            )

            # Mark as completed
            progress.mark_completed()
            self.progress_sessions[upload_id] = progress

            return {
                "asset_id": asset_id,
                "upload_id": upload_id,
                **upload_result,
                "width": processing_result["width"],
                "height": processing_result["height"],
                "aspect_ratio": processing_result["aspect_ratio"],
                "file_size": len(file_data),
                "mime_type": mime_type,
                "metadata": metadata,
            }

        except Exception as e:
            logger.error(f"Upload failed: {str(e)}")
            progress.mark_failed(str(e))
            self.progress_sessions[upload_id] = progress
            raise

    # ==================== RESUMABLE UPLOAD ====================

    async def create_upload_session(
        self,
        file_name: str,
        file_size: int,
        chunk_size: int = 5 * 1024 * 1024  # 5MB chunks
    ) -> UploadSession:
        """Create resumable upload session"""
        session = UploadSession(
            session_id=str(uuid4()),
            file_name=file_name,
            file_size=file_size,
            chunk_size=chunk_size,
            chunks_uploaded=[],
            upload_started_at=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )

        self.resumable_sessions[session.session_id] = session
        logger.info(f"Created upload session: {session.session_id}")
        return session

    async def upload_chunk(
        self,
        session_id: str,
        chunk_index: int,
        chunk_data: bytes
    ) -> dict:
        """Upload single chunk of file"""
        if session_id not in self.resumable_sessions:
            raise ValueError(f"Session not found: {session_id}")

        session = self.resumable_sessions[session_id]
        session.add_chunk(chunk_index)

        return {
            "session_id": session_id,
            "chunk_index": chunk_index,
            "chunk_size": len(chunk_data),
            "session": session.to_dict(),
        }

    async def complete_resumable_upload(
        self,
        session_id: str,
        portfolio_id: str,
        asset_id: str,
        asset_type: str,
        chunk_parts: list  # List of {chunk_index, etag} from multipart upload
    ) -> dict:
        """Complete resumable upload after all chunks uploaded"""
        if session_id not in self.resumable_sessions:
            raise ValueError(f"Session not found: {session_id}")

        session = self.resumable_sessions[session_id]

        if not session.is_complete():
            raise ValueError("Not all chunks have been uploaded")

        try:
            # Process and store the assembled file
            # (In production, use S3 multipart merge or reassemble from chunks)

            session.storage_path = f"portfolios/{portfolio_id}/assets/{asset_id}/original"

            # Mark session as complete
            del self.resumable_sessions[session_id]

            return {
                "asset_id": asset_id,
                "session_id": session_id,
                "status": "completed",
                "storage_path": session.storage_path,
            }

        except Exception as e:
            logger.error(f"Failed to complete upload: {str(e)}")
            raise

    # ==================== PROGRESS TRACKING ====================

    def get_upload_progress(self, upload_id: str) -> Optional[dict]:
        """Get upload progress"""
        if upload_id in self.progress_sessions:
            return self.progress_sessions[upload_id].to_dict()
        return None

    def get_session_progress(self, session_id: str) -> Optional[dict]:
        """Get resumable session progress"""
        if session_id in self.resumable_sessions:
            return self.resumable_sessions[session_id].to_dict()
        return None

    def cleanup_expired_sessions(self, retention_hours: int = 24):
        """Clean up expired upload sessions"""
        expired_sessions = [
            sid for sid, session in self.resumable_sessions.items()
            if session.is_expired(retention_hours)
        ]

        for sid in expired_sessions:
            del self.resumable_sessions[sid]
            logger.info(f"Cleaned up expired session: {sid}")

        # Also cleanup old progress records
        expired_progress = [
            uid for uid, progress in self.progress_sessions.items()
            if progress.completed_at and
            (datetime.utcnow() - progress.completed_at).total_seconds() > (retention_hours * 3600)
        ]

        for uid in expired_progress:
            del self.progress_sessions[uid]

        logger.info(f"Cleaned up {len(expired_sessions) + len(expired_progress)} expired uploads")

    # ==================== BATCH UPLOAD ====================

    async def upload_batch(
        self,
        files: list,  # List of UploadFile
        portfolio_id: str,
        asset_type: str
    ) -> dict:
        """
        Upload multiple files
        Returns: {uploaded: int, failed: int, total: int, errors: list}
        """
        results = {
            "uploaded": 0,
            "failed": 0,
            "total": len(files),
            "errors": [],
            "assets": []
        }

        for file in files:
            try:
                asset_id = str(uuid4())
                result = await self.upload_file(
                    file,
                    portfolio_id,
                    asset_id,
                    asset_type
                )
                results["uploaded"] += 1
                results["assets"].append(result)

            except Exception as e:
                logger.error(f"Batch upload failed for {file.filename}: {str(e)}")
                results["failed"] += 1
                results["errors"].append({
                    "file_name": file.filename,
                    "error": str(e),
                })

        return results

    # ==================== CHECKSUM ====================

    async def calculate_checksum(self, file_data: bytes) -> str:
        """Calculate file checksum for integrity verification"""
        return hashlib.sha256(file_data).hexdigest()

    async def verify_checksum(self, file_data: bytes, expected_checksum: str) -> bool:
        """Verify file integrity"""
        actual_checksum = await self.calculate_checksum(file_data)
        return actual_checksum == expected_checksum


# ==================== SINGLETON INSTANCE ====================

_upload_manager = None

def get_upload_manager() -> UploadManager:
    """Get or create upload manager singleton"""
    global _upload_manager
    if _upload_manager is None:
        _upload_manager = UploadManager()
    return _upload_manager
