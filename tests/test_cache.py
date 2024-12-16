"""Tests for the documentation cache system."""

import pytest
from datetime import timedelta

from unblu_docs_explorer.cache import DocumentCache
from unblu_docs_explorer.models.document import Document, DocumentSection


@pytest.fixture
def sample_document():
    """Create a sample document for testing."""
    return Document(
        url="https://docs.example.com/test",
        title="Test Document",
        sections=[
            DocumentSection(
                title="Section 1",
                content="Test content 1",
                subsections=[DocumentSection(title="Subsection 1.1", content="Subsection content")],
            )
        ],
    )


@pytest.fixture
def cache():
    """Create a fresh cache instance for testing."""
    return DocumentCache()


@pytest.mark.asyncio
async def test_cache_store_and_retrieve(cache, sample_document):
    """Test basic cache storage and retrieval."""
    await cache.store(sample_document.url, sample_document)
    cached = await cache.get(sample_document.url)

    assert cached is not None
    assert cached.url == sample_document.url
    assert cached.title == sample_document.title
    assert len(cached.sections) == len(sample_document.sections)
    assert cached.sections[0].title == sample_document.sections[0].title


@pytest.mark.asyncio
async def test_cache_expiration(cache, sample_document):
    """Test that cached items expire after the configured time."""
    # Store with short expiration
    await cache.store(sample_document.url, sample_document, expiration=timedelta(seconds=1))

    # Should be available immediately
    assert await cache.get(sample_document.url) is not None

    # Wait for expiration
    await cache.force_expire(sample_document.url)

    # Should be None after expiration
    assert await cache.get(sample_document.url) is None


@pytest.mark.asyncio
async def test_cache_clear(cache, sample_document):
    """Test cache clearing functionality."""
    await cache.store(sample_document.url, sample_document)
    assert await cache.get(sample_document.url) is not None

    await cache.clear()
    assert await cache.get(sample_document.url) is None


@pytest.mark.asyncio
async def test_cache_update(cache, sample_document):
    """Test updating cached items."""
    await cache.store(sample_document.url, sample_document)

    # Modify document
    updated_doc = Document(url=sample_document.url, title="Updated Title", sections=sample_document.sections)

    await cache.store(sample_document.url, updated_doc)
    cached = await cache.get(sample_document.url)

    assert cached.title == "Updated Title"


@pytest.mark.asyncio
async def test_cache_invalid_key(cache):
    """Test behavior with invalid cache keys."""
    assert await cache.get("nonexistent") is None


@pytest.mark.asyncio
async def test_cache_metadata(cache, sample_document):
    """Test cache metadata handling."""
    await cache.store(sample_document.url, sample_document)
    metadata = await cache.get_metadata(sample_document.url)

    assert metadata is not None
    assert "last_accessed" in metadata
    assert "created_at" in metadata
    assert "access_count" in metadata
    assert metadata["access_count"] == 0  # No gets performed yet

    # Access the document
    await cache.get(sample_document.url)
    updated_metadata = await cache.get_metadata(sample_document.url)
    assert updated_metadata["access_count"] == 1


@pytest.mark.asyncio
async def test_cache_size_limit(cache, sample_document):
    """Test cache respects size limits."""
    # Set a small cache size limit
    cache.set_size_limit(2)

    # Add multiple documents
    for i in range(3):
        doc = Document(
            url=f"https://docs.example.com/test{i}", title=f"Test Document {i}", sections=sample_document.sections
        )
        await cache.store(doc.url, doc)

    # First document should be evicted
    assert await cache.get("https://docs.example.com/test0") is None
    assert await cache.get("https://docs.example.com/test1") is not None
    assert await cache.get("https://docs.example.com/test2") is not None
