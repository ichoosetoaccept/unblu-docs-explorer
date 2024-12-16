"""Tests for the documentation fetcher."""

import pytest
import httpx
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from unblu_docs_explorer.fetcher import DocumentationFetcher
from unblu_docs_explorer.errors import DocumentationError, ResourceNotFoundError


@pytest.fixture
def base_url():
    """Base URL for testing."""
    return "https://docs.example.com"


@pytest.fixture
def sample_doc_html():
    """Sample HTML document for testing."""
    return """
    <html>
        <head><title>Test Doc</title></head>
        <body>
            <h1>Test Section</h1>
            <p>Test content</p>
        </body>
    </html>
    """


@pytest.fixture
def sample_doc_with_subsections():
    """Sample HTML document with subsections for testing."""
    return """
    <html>
        <head><title>Test Doc with Subsections</title></head>
        <body>
            <h1>Main Section</h1>
            <p>Main content</p>
            <h2>Subsection 1</h2>
            <p>Subsection 1 content</p>
            <h2>Subsection 2</h2>
            <p>Subsection 2 content</p>
            <h1>Second Main Section</h1>
            <p>More content</p>
        </body>
    </html>
    """


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client."""
    client = AsyncMock(spec=httpx.AsyncClient)
    client.aclose = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_fetch_document_success(base_url, sample_doc_html, mock_http_client):
    """Test successful document fetching."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.text = sample_doc_html
    mock_http_client.get.return_value = mock_response

    async with DocumentationFetcher(base_url, mock_http_client) as fetcher:
        doc = await fetcher.fetch_document("/test")
        assert doc.url == f"{base_url}/test"
        assert doc.title == "Test Doc"
        assert len(doc.sections) == 1
        assert doc.sections[0].title == "Test Section"
        assert doc.sections[0].content.strip() == "Test content"

    mock_http_client.get.assert_called_once_with(f"{base_url}/test")


@pytest.mark.asyncio
async def test_fetch_document_not_found(base_url, mock_http_client):
    """Test handling of 404 responses."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 404
    mock_http_client.get.return_value = mock_response

    async with DocumentationFetcher(base_url, mock_http_client) as fetcher:
        with pytest.raises(ResourceNotFoundError) as exc_info:
            await fetcher.fetch_document("/missing")
        assert "Document not found" in str(exc_info.value)

    mock_http_client.get.assert_called_once_with(f"{base_url}/missing")


@pytest.mark.asyncio
async def test_fetch_document_server_error(base_url, mock_http_client):
    """Test handling of server errors."""
    error_codes = [500, 502, 503]
    for code in error_codes:
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = code
        mock_http_client.get.return_value = mock_response

        async with DocumentationFetcher(base_url, mock_http_client) as fetcher:
            with pytest.raises(DocumentationError) as exc_info:
                await fetcher.fetch_document(f"/error{code}")
            assert exc_info.value.operation == "fetch_document"
            assert str(code) in str(exc_info.value)

        mock_http_client.get.assert_called_once_with(f"{base_url}/error{code}")
        mock_http_client.get.reset_mock()


@pytest.mark.asyncio
async def test_fetch_document_malformed_html(base_url, mock_http_client):
    """Test handling of malformed HTML responses."""
    malformed_html = "<html><title>Broken<//title><body><h1>Test</h2></body>"
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.text = malformed_html

    mock_http_client.get.return_value = mock_response

    async with DocumentationFetcher(base_url, mock_http_client) as fetcher:
        doc = await fetcher.fetch_document("/malformed")
        assert doc.url == f"{base_url}/malformed"
        assert doc.title == "/malformed"  # Fallback to path when title can't be parsed
        assert len(doc.sections) == 1
        assert doc.sections[0].title == "Test"

    mock_http_client.get.assert_called_once_with(f"{base_url}/malformed")


@pytest.mark.asyncio
async def test_document_timestamp(base_url, sample_doc_html, mock_http_client):
    """Test that document timestamps are set correctly."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.text = sample_doc_html
    mock_http_client.get.return_value = mock_response

    async with DocumentationFetcher(base_url, mock_http_client) as fetcher:
        before_fetch = datetime.now(timezone.utc)
        doc = await fetcher.fetch_document("/test")
        after_fetch = datetime.now(timezone.utc)

        assert before_fetch <= doc.last_fetched <= after_fetch

    mock_http_client.get.assert_called_once_with(f"{base_url}/test")


@pytest.mark.asyncio
async def test_document_caching(base_url, sample_doc_html, mock_http_client):
    """Test that documents are properly cached."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.text = sample_doc_html
    mock_http_client.get.return_value = mock_response

    async with DocumentationFetcher(base_url, mock_http_client) as fetcher:
        # First fetch should hit the network
        doc1 = await fetcher.fetch_document("/test")
        assert mock_http_client.get.call_count == 1

        # Second fetch should use cache
        doc2 = await fetcher.fetch_document("/test")
        assert mock_http_client.get.call_count == 1  # Still 1 because we used cache
        assert doc1 is doc2  # Same object reference

        # After invalidating cache, should hit network again
        await fetcher.invalidate_cache("/test")
        doc3 = await fetcher.fetch_document("/test")
        assert mock_http_client.get.call_count == 2
        assert doc1 is not doc3  # Different object reference

    mock_http_client.get.assert_called_with(f"{base_url}/test")


@pytest.mark.asyncio
async def test_fetch_document_with_subsections(base_url, sample_doc_with_subsections, mock_http_client):
    """Test document fetching with subsections."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.text = sample_doc_with_subsections
    mock_http_client.get.return_value = mock_response

    async with DocumentationFetcher(base_url, mock_http_client) as fetcher:
        doc = await fetcher.fetch_document("/test-subsections")
        assert doc.url == f"{base_url}/test-subsections"
        assert doc.title == "Test Doc with Subsections"
        assert len(doc.sections) == 2

        # Check first main section
        assert doc.sections[0].title == "Main Section"
        assert "Main content" in doc.sections[0].content
        assert "Subsection 1 content" in doc.sections[0].content
        assert "Subsection 2 content" in doc.sections[0].content

        # Check second main section
        assert doc.sections[1].title == "Second Main Section"
        assert "More content" in doc.sections[1].content

    mock_http_client.get.assert_called_once_with(f"{base_url}/test-subsections")
