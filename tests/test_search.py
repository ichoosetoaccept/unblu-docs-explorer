import pytest
from unblu_docs_explorer.search import DocumentationSearch
from unblu_docs_explorer.errors import SearchError


@pytest.fixture
def sample_documentation():
    """Provide sample documentation content for testing."""
    return [
        {
            "title": "Installation Guide",
            "content": "This guide explains how to install and configure the system.",
            "path": "/docs/installation",
            "metadata": {"section": "getting_started"},
        },
        {
            "title": "API Reference",
            "content": "Complete API documentation with examples and use cases.",
            "path": "/docs/api",
            "metadata": {"section": "reference"},
        },
    ]


@pytest.mark.asyncio
async def test_search_finds_relevant_content(sample_documentation):
    """Verify search returns relevant results in correct order."""
    search = DocumentationSearch()
    for doc in sample_documentation:
        await search.index_document(doc)

    results = await search.search("installation configure")

    assert len(results) > 0
    assert results[0]["path"] == "/docs/installation"
    assert "relevance" in results[0]
    assert results[0]["relevance"] >= 0.0


@pytest.mark.asyncio
async def test_search_respects_context():
    """Verify context-aware search narrows results appropriately."""
    search = DocumentationSearch()
    await search.index_document(
        {
            "title": "API Guide",
            "content": "API configuration steps",
            "path": "/docs/api",
            "metadata": {"section": "api"},
        }
    )
    await search.index_document(
        {
            "title": "User Guide",
            "content": "User configuration steps",
            "path": "/docs/user",
            "metadata": {"section": "user"},
        }
    )

    results = await search.search("configuration", context="api")

    assert len(results) == 1
    assert results[0]["path"] == "/docs/api"


@pytest.mark.asyncio
async def test_empty_search_raises_error():
    """Verify empty search query raises appropriate error."""
    search = DocumentationSearch()
    with pytest.raises(SearchError):
        await search.search("")


@pytest.mark.asyncio
async def test_search_returns_empty_for_no_matches():
    """Verify search returns empty list when no matches found."""
    search = DocumentationSearch()
    results = await search.search("nonexistent term")
    assert len(results) == 0
