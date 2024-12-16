import json
import pytest
import pytest_asyncio
from mcp import types
from unblu_docs_explorer.server import UnbluDocsServer
from unblu_docs_explorer.errors import DocumentationError


@pytest.fixture
def config_file(tmp_path):
    """Create a temporary config file for testing."""
    config = {
        "docs_base_url": "https://docs.unblu.com",
        "cache_dir": str(tmp_path / "cache"),
        "sections": [
            {"path": "/installation", "title": "Installation Guide", "content": "Guide for installing Unblu"},
            {"path": "/api", "title": "API Reference", "content": "API documentation and examples"},
        ],
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))
    return str(config_path)


@pytest_asyncio.fixture
async def server(config_file):
    """Create a server instance for testing."""
    return await UnbluDocsServer.create(config_file)


@pytest.mark.asyncio
async def test_server_initialization(config_file):
    """Test server initialization with valid config."""
    server = await UnbluDocsServer.create(config_file)
    assert server.config["docs_base_url"] == "https://docs.unblu.com"
    assert len(server.config["sections"]) == 2


@pytest.mark.asyncio
async def test_server_initialization_invalid_config():
    """Test server initialization with invalid config path."""
    with pytest.raises(DocumentationError) as exc_info:
        await UnbluDocsServer.create("nonexistent.json")
    assert "Failed to load config" in str(exc_info.value)
    assert exc_info.value.operation == "load_config"


@pytest.mark.asyncio
async def test_server_initialization_invalid_json(tmp_path):
    """Test server initialization with invalid JSON."""
    config_path = tmp_path / "invalid.json"
    config_path.write_text("invalid json")

    with pytest.raises(DocumentationError) as exc_info:
        await UnbluDocsServer.create(str(config_path))
    assert "Failed to load config" in str(exc_info.value)
    assert exc_info.value.operation == "load_config"


@pytest.mark.asyncio
async def test_list_resources(server):
    """Test listing available documentation resources."""
    resources = await server.list_resources()

    assert len(resources) == 2
    assert all(isinstance(resource, types.Resource) for resource in resources)

    installation = next(r for r in resources if "installation" in str(r.uri))
    assert installation.name == "Installation Guide"
    assert installation.mimeType == "text/html"

    api = next(r for r in resources if "api" in str(r.uri))
    assert api.name == "API Reference"
    assert api.mimeType == "text/html"


@pytest.mark.asyncio
async def test_search_tool(server):
    """Test search tool functionality."""
    result = await server.handle_tool_call("search_docs", {"query": "installation"})

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["path"] == "/installation"
    assert isinstance(result[0]["relevance"], float)


@pytest.mark.asyncio
async def test_search_tool_with_context(server):
    """Test search tool with context filtering."""
    result = await server.handle_tool_call("search_docs", {"query": "documentation", "context": "api"})

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["path"] == "/api"


@pytest.mark.asyncio
async def test_search_tool_no_query(server):
    """Test search tool with missing query."""
    with pytest.raises(DocumentationError) as exc_info:
        await server.handle_tool_call("search_docs", {})
    assert "Missing required 'query' argument" in str(exc_info.value)
    assert exc_info.value.operation == "search_docs"


@pytest.mark.asyncio
async def test_unknown_tool(server):
    """Test handling of unknown tool calls."""
    with pytest.raises(DocumentationError) as exc_info:
        await server.handle_tool_call("nonexistent_tool", {})
    assert "Unknown tool" in str(exc_info.value)
    assert exc_info.value.operation == "handle_tool"


@pytest.mark.asyncio
async def test_search_no_results(server):
    """Test search with no matching results."""
    result = await server.handle_tool_call("search_docs", {"query": "nonexistent"})
    assert isinstance(result, list)
    assert len(result) == 0
