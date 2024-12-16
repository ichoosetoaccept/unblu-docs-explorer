"""Cache system for storing and managing documentation content."""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Any
from collections import OrderedDict

from .models.document import Document


class CacheEntry:
    """Represents a cached item with metadata."""

    def __init__(self, document: Document, expiration: Optional[timedelta] = None):
        """Initialize a cache entry.

        Args:
            document: The document to cache
            expiration: Optional expiration time
        """
        self.document = document
        self.created_at = datetime.now(timezone.utc)
        self.last_accessed = self.created_at
        self.access_count = 0
        self.expires_at = self.created_at + expiration if expiration else None

    def is_expired(self) -> bool:
        """Check if the entry has expired."""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def access(self) -> None:
        """Record an access to this cache entry."""
        self.last_accessed = datetime.now(timezone.utc)
        self.access_count += 1


class DocumentCache:
    """Cache for storing processed documentation."""

    def __init__(self, max_size: int = 100):
        """Initialize the cache.

        Args:
            max_size: Maximum number of items to store
        """
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._lock = asyncio.Lock()

    def set_size_limit(self, limit: int) -> None:
        """Set the maximum cache size.

        Args:
            limit: New maximum size
        """
        self._max_size = limit

    async def store(self, key: str, document: Document, expiration: Optional[timedelta] = None) -> None:
        """Store a document in the cache.

        Args:
            key: Cache key (usually document URL)
            document: Document to cache
            expiration: Optional expiration time
        """
        async with self._lock:
            # Create new entry
            entry = CacheEntry(document, expiration)

            # If at size limit, remove oldest entry
            if len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)

            # Store new entry
            self._cache[key] = entry

    async def get(self, key: str) -> Optional[Document]:
        """Retrieve a document from the cache.

        Args:
            key: Cache key to lookup

        Returns:
            Document if found and not expired, None otherwise
        """
        async with self._lock:
            entry = self._cache.get(key)
            if not entry:
                return None

            # Check expiration
            if entry.is_expired():
                del self._cache[key]
                return None

            # Record access and return
            entry.access()
            return entry.document

    async def get_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a cached item.

        Args:
            key: Cache key to lookup

        Returns:
            Dictionary of metadata if found, None otherwise
        """
        async with self._lock:
            entry = self._cache.get(key)
            if not entry:
                return None

            return {
                "created_at": entry.created_at,
                "last_accessed": entry.last_accessed,
                "access_count": entry.access_count,
                "expires_at": entry.expires_at,
            }

    async def clear(self) -> None:
        """Clear all items from the cache."""
        async with self._lock:
            self._cache.clear()

    async def force_expire(self, key: str) -> None:
        """Force a cache entry to expire immediately.

        Args:
            key: Cache key to expire
        """
        async with self._lock:
            entry = self._cache.get(key)
            if entry:
                entry.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
