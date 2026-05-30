"""
Asset search and organization service
Phase 2: Task 2.4 - Search, filter, organize assets
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

from database import supabase

logger = logging.getLogger(__name__)

# ==================== ENUMS ====================

class SortField(str, Enum):
    """Sort field options"""
    created_at = "created_at"
    file_size = "file_size"
    file_name = "file_name"
    aspect_ratio = "aspect_ratio"


class SortOrder(str, Enum):
    """Sort order options"""
    asc = "asc"
    desc = "desc"


# ==================== DATA CLASSES ====================

@dataclass
class SearchFilter:
    """Search filter criteria"""
    portfolio_id: str
    user_id: str

    # Text search
    search_query: Optional[str] = None

    # Type filtering
    asset_types: Optional[List[str]] = None

    # Tag filtering
    tags: Optional[List[str]] = None

    # Date range filtering
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None

    # Size filtering
    min_size_kb: Optional[float] = None
    max_size_kb: Optional[float] = None

    # Aspect ratio filtering
    aspect_ratio_min: Optional[float] = None
    aspect_ratio_max: Optional[float] = None

    # Sorting
    sort_by: SortField = SortField.created_at
    sort_order: SortOrder = SortOrder.desc

    # Pagination
    page: int = 1
    page_size: int = 20

    # Exclude deleted
    include_deleted: bool = False


@dataclass
class SearchResult:
    """Search result"""
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int
    filters_applied: Dict[str, Any]


# ==================== SEARCH SERVICE ====================

class AssetSearchService:
    """Comprehensive asset search and organization"""

    def __init__(self):
        """Initialize search service"""
        self.supabase = supabase

    # ==================== BASIC SEARCH ====================

    async def search(self, filters: SearchFilter) -> SearchResult:
        """
        Search assets with comprehensive filtering
        """
        try:
            # Start with base query
            query = self.supabase.table("assets").select("*").eq(
                "portfolio_id", filters.portfolio_id
            ).eq("user_id", filters.user_id)

            # Apply text search
            if filters.search_query:
                search_term = filters.search_query.lower()
                # Search in file_name and description
                query = query.or_(
                    f"file_name.ilike.%{search_term}%,description.ilike.%{search_term}%"
                )

            # Apply asset type filter
            if filters.asset_types:
                if len(filters.asset_types) == 1:
                    query = query.eq("asset_type", filters.asset_types[0])
                else:
                    # Use IN-like filtering with OR
                    type_filters = ",".join([f"asset_type.eq.{t}" for t in filters.asset_types])
                    query = query.or_(type_filters)

            # Apply date range filter
            if filters.created_after:
                query = query.gte("created_at", filters.created_after.isoformat())
            if filters.created_before:
                query = query.lte("created_at", filters.created_before.isoformat())

            # Apply size filter (convert to bytes)
            if filters.min_size_kb is not None:
                min_bytes = filters.min_size_kb * 1024
                query = query.gte("file_size", int(min_bytes))
            if filters.max_size_kb is not None:
                max_bytes = filters.max_size_kb * 1024
                query = query.lte("file_size", int(max_bytes))

            # Apply aspect ratio filter
            if filters.aspect_ratio_min is not None:
                query = query.gte("aspect_ratio", filters.aspect_ratio_min)
            if filters.aspect_ratio_max is not None:
                query = query.lte("aspect_ratio", filters.aspect_ratio_max)

            # Apply deleted filter
            if not filters.include_deleted:
                query = query.is_("deleted_at", "null")

            # Apply sorting
            is_desc = filters.sort_order == SortOrder.desc
            query = query.order(filters.sort_by.value, desc=is_desc)

            # Get total count
            count_response = self.supabase.table("assets").select(
                "id", count="exact"
            ).eq("portfolio_id", filters.portfolio_id).eq(
                "user_id", filters.user_id
            )
            if not filters.include_deleted:
                count_response = count_response.is_("deleted_at", "null")
            count_response = count_response.execute()
            total = count_response.count

            # Apply pagination
            offset = (filters.page - 1) * filters.page_size
            response = query.range(offset, offset + filters.page_size - 1).execute()

            assets = response.data or []

            # Get tags for each asset
            for asset in assets:
                tags_response = self.supabase.table("asset_tags").select(
                    "tag_name"
                ).eq("asset_id", asset["id"]).execute()
                asset["tags"] = [t["tag_name"] for t in tags_response.data]

            # Apply tag filter after retrieval (since tags are in separate table)
            if filters.tags:
                assets = [
                    a for a in assets
                    if any(tag in a.get("tags", []) for tag in filters.tags)
                ]

            total_pages = (total + filters.page_size - 1) // filters.page_size

            return SearchResult(
                items=assets,
                total=len(assets),  # Filtered total
                page=filters.page,
                page_size=filters.page_size,
                total_pages=(len(assets) + filters.page_size - 1) // filters.page_size,
                filters_applied={
                    "search_query": filters.search_query,
                    "asset_types": filters.asset_types,
                    "tags": filters.tags,
                    "date_range": {
                        "after": filters.created_after.isoformat() if filters.created_after else None,
                        "before": filters.created_before.isoformat() if filters.created_before else None,
                    },
                    "size_range_kb": {
                        "min": filters.min_size_kb,
                        "max": filters.max_size_kb,
                    },
                    "sort": {
                        "by": filters.sort_by.value,
                        "order": filters.sort_order.value,
                    },
                }
            )

        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            raise

    # ==================== TEXT SEARCH ====================

    async def search_by_filename(
        self,
        portfolio_id: str,
        user_id: str,
        query: str,
        page: int = 1,
        page_size: int = 20
    ) -> SearchResult:
        """Search assets by filename"""
        filters = SearchFilter(
            portfolio_id=portfolio_id,
            user_id=user_id,
            search_query=query,
            page=page,
            page_size=page_size,
        )
        return await self.search(filters)

    async def search_by_tag(
        self,
        portfolio_id: str,
        user_id: str,
        tags: List[str],
        match_all: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> SearchResult:
        """
        Search assets by tags

        Args:
            tags: List of tags to search for
            match_all: If True, asset must have all tags. If False, any tag match.
        """
        filters = SearchFilter(
            portfolio_id=portfolio_id,
            user_id=user_id,
            tags=tags,
            page=page,
            page_size=page_size,
        )
        result = await self.search(filters)

        # If match_all, filter further
        if match_all:
            result.items = [
                a for a in result.items
                if all(tag in a.get("tags", []) for tag in tags)
            ]

        return result

    # ==================== FILTERING ====================

    async def filter_by_type(
        self,
        portfolio_id: str,
        user_id: str,
        asset_types: List[str],
        page: int = 1,
        page_size: int = 20
    ) -> SearchResult:
        """Filter assets by type"""
        filters = SearchFilter(
            portfolio_id=portfolio_id,
            user_id=user_id,
            asset_types=asset_types,
            page=page,
            page_size=page_size,
        )
        return await self.search(filters)

    async def filter_by_date_range(
        self,
        portfolio_id: str,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
        page: int = 1,
        page_size: int = 20
    ) -> SearchResult:
        """Filter assets by date range"""
        filters = SearchFilter(
            portfolio_id=portfolio_id,
            user_id=user_id,
            created_after=start_date,
            created_before=end_date,
            page=page,
            page_size=page_size,
        )
        return await self.search(filters)

    async def filter_by_size(
        self,
        portfolio_id: str,
        user_id: str,
        min_kb: float,
        max_kb: float,
        page: int = 1,
        page_size: int = 20
    ) -> SearchResult:
        """Filter assets by file size"""
        filters = SearchFilter(
            portfolio_id=portfolio_id,
            user_id=user_id,
            min_size_kb=min_kb,
            max_size_kb=max_kb,
            page=page,
            page_size=page_size,
        )
        return await self.search(filters)

    async def filter_by_aspect_ratio(
        self,
        portfolio_id: str,
        user_id: str,
        min_ratio: float,
        max_ratio: float,
        page: int = 1,
        page_size: int = 20
    ) -> SearchResult:
        """Filter assets by aspect ratio"""
        filters = SearchFilter(
            portfolio_id=portfolio_id,
            user_id=user_id,
            aspect_ratio_min=min_ratio,
            aspect_ratio_max=max_ratio,
            page=page,
            page_size=page_size,
        )
        return await self.search(filters)

    # ==================== TAG MANAGEMENT ====================

    async def get_all_tags(self, portfolio_id: str) -> Dict[str, int]:
        """Get all tags in portfolio with counts"""
        try:
            # Get all assets in portfolio
            assets_response = self.supabase.table("assets").select(
                "id"
            ).eq("portfolio_id", portfolio_id).execute()

            asset_ids = [a["id"] for a in assets_response.data]

            if not asset_ids:
                return {}

            # Get tags for these assets
            tags_response = self.supabase.table("asset_tags").select(
                "tag_name"
            ).in_("asset_id", asset_ids).execute()

            # Count tags
            tag_counts = {}
            for tag_record in tags_response.data:
                tag_name = tag_record["tag_name"]
                tag_counts[tag_name] = tag_counts.get(tag_name, 0) + 1

            return dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True))

        except Exception as e:
            logger.error(f"Error getting tags: {str(e)}")
            return {}

    async def get_popular_tags(
        self,
        portfolio_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get most popular tags in portfolio"""
        tag_counts = await self.get_all_tags(portfolio_id)
        popular = [
            {"tag": tag, "count": count}
            for tag, count in list(tag_counts.items())[:limit]
        ]
        return popular

    async def add_tag_to_asset(
        self,
        asset_id: str,
        tag_name: str
    ) -> None:
        """Add tag to asset"""
        try:
            # Check if tag already exists
            existing = self.supabase.table("asset_tags").select("id").eq(
                "asset_id", asset_id
            ).eq("tag_name", tag_name).execute()

            if not existing.data:
                from uuid import uuid4
                tag_data = {
                    "id": str(uuid4()),
                    "asset_id": asset_id,
                    "tag_name": tag_name,
                    "created_at": datetime.utcnow().isoformat(),
                }
                self.supabase.table("asset_tags").insert(tag_data).execute()

        except Exception as e:
            logger.error(f"Error adding tag: {str(e)}")
            raise

    async def remove_tag_from_asset(
        self,
        asset_id: str,
        tag_name: str
    ) -> None:
        """Remove tag from asset"""
        try:
            self.supabase.table("asset_tags").delete().eq(
                "asset_id", asset_id
            ).eq("tag_name", tag_name).execute()

        except Exception as e:
            logger.error(f"Error removing tag: {str(e)}")
            raise

    # ==================== COLLECTIONS/FOLDERS ====================

    async def get_asset_collections(
        self,
        portfolio_id: str
    ) -> List[Dict[str, Any]]:
        """Get asset collections/folders grouped by type"""
        try:
            assets_response = self.supabase.table("assets").select(
                "id, asset_type, file_name"
            ).eq("portfolio_id", portfolio_id).is_("deleted_at", "null").execute()

            # Group by type
            collections = {}
            for asset in assets_response.data:
                asset_type = asset.get("asset_type", "other")
                if asset_type not in collections:
                    collections[asset_type] = {
                        "name": asset_type.title(),
                        "type": asset_type,
                        "count": 0,
                        "assets": []
                    }
                collections[asset_type]["count"] += 1
                collections[asset_type]["assets"].append(asset)

            return list(collections.values())

        except Exception as e:
            logger.error(f"Error getting collections: {str(e)}")
            return []

    async def get_collection_stats(
        self,
        portfolio_id: str
    ) -> Dict[str, Any]:
        """Get statistics about assets in portfolio"""
        try:
            assets_response = self.supabase.table("assets").select(
                "file_size, aspect_ratio, asset_type, created_at"
            ).eq("portfolio_id", portfolio_id).is_("deleted_at", "null").execute()

            assets = assets_response.data or []

            if not assets:
                return {
                    "total_assets": 0,
                    "total_size_mb": 0,
                    "asset_types": {},
                    "aspect_ratio_stats": {},
                }

            # Calculate stats
            total_size = sum(a.get("file_size", 0) for a in assets)
            asset_types = {}
            for asset in assets:
                asset_type = asset.get("asset_type", "other")
                asset_types[asset_type] = asset_types.get(asset_type, 0) + 1

            aspect_ratios = [a.get("aspect_ratio", 1.0) for a in assets if a.get("aspect_ratio")]
            avg_aspect_ratio = sum(aspect_ratios) / len(aspect_ratios) if aspect_ratios else 1.0

            return {
                "total_assets": len(assets),
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "asset_types": asset_types,
                "aspect_ratio_stats": {
                    "min": round(min(aspect_ratios), 2) if aspect_ratios else None,
                    "max": round(max(aspect_ratios), 2) if aspect_ratios else None,
                    "average": round(avg_aspect_ratio, 2),
                },
                "oldest_asset": min(a.get("created_at") for a in assets) if assets else None,
                "newest_asset": max(a.get("created_at") for a in assets) if assets else None,
            }

        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {}

    # ==================== RECOMMENDATIONS ====================

    async def get_search_suggestions(
        self,
        portfolio_id: str,
        user_id: str,
        query: str,
        limit: int = 10
    ) -> Dict[str, List[str]]:
        """Get search suggestions based on query"""
        try:
            suggestions = {
                "tags": [],
                "filenames": [],
                "asset_types": [],
            }

            # Get matching tags
            tags = await self.get_all_tags(portfolio_id)
            matching_tags = [t for t in tags.keys() if query.lower() in t.lower()]
            suggestions["tags"] = matching_tags[:limit]

            # Get matching filenames
            assets_response = self.supabase.table("assets").select(
                "file_name"
            ).eq("portfolio_id", portfolio_id).like(
                "file_name", f"%{query}%"
            ).limit(limit).execute()
            suggestions["filenames"] = [a["file_name"] for a in assets_response.data]

            # Asset types
            types_response = self.supabase.table("assets").select(
                "asset_type", count="exact"
            ).eq("portfolio_id", portfolio_id).execute()
            all_types = set(a["asset_type"] for a in types_response.data if a.get("asset_type"))
            matching_types = [t for t in all_types if query.lower() in t.lower()]
            suggestions["asset_types"] = matching_types

            return suggestions

        except Exception as e:
            logger.error(f"Error getting suggestions: {str(e)}")
            return {"tags": [], "filenames": [], "asset_types": []}


# ==================== SINGLETON INSTANCE ====================

_search_service = None

def get_search_service() -> AssetSearchService:
    """Get or create search service singleton"""
    global _search_service
    if _search_service is None:
        _search_service = AssetSearchService()
    return _search_service
