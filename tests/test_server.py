import pytest
from mcp import types
from unblu_docs_explorer.server import UnbluDocsServer
from unblu_docs_explorer.errors import DocumentationError


@pytest.fixture
def config_path(tmp_path):
    """Create a temporary config file for testing."""
    config = tmp_path / "config.json"
    config.write_text("""
    {
        "docs_base_url": "https://docs.unblu.com",
        "cache_dir": "/tmp/unblu-docs-cache",
        "sections": [
            {
                "path": "/installation",
                "title": "Installation Guide"
            },
            {
                "path": "/api",
                "title": "API Reference"
            }
        ]
    }
    """)
    return str(config)


@pytest.mark.asyncio
async def test_server_lists_resources(config_path):
    """Verify server properly exposes documentation sections."""
    server = await UnbluDocsServer.create(config_path)
    resources = await server.list_resources()

    assert len(resources) > 0
    assert all(isinstance(resource, types.Resource) for resource in resources)


@pytest.mark.asyncio
async def test_search_tool_integration(config_path):
    """Verify search tool functions correctly through MCP interface."""
    server = await UnbluDocsServer.create(config_path)
    result = await server.handle_tool_call("search_docs", {"query": "installation"})

    assert isinstance(result, list)
    assert all(isinstance(item["relevance"], float) for item in result)


@pytest.mark.asyncio
async def test_invalid_tool_raises_error(config_path):
    """Verify invalid tool calls are handled properly."""
    server = await UnbluDocsServer.create(config_path)
    with pytest.raises(DocumentationError):
        await server.handle_tool_call("nonexistent_tool", {})


@pytest.mark.asyncio
async def test_server_handles_invalid_config():
    """Verify server properly handles invalid config file."""
    with pytest.raises(DocumentationError):
        await UnbluDocsServer.create("nonexistent_config.json")


@pytest.mark.asyncio
async def test_get_resource_success(config_path):
    """Verify server can retrieve a specific resource."""
    server = await UnbluDocsServer.create(config_path)
    resource = await server.get_resource("docs://installation")

    assert isinstance(resource, types.Resource)
    assert str(resource.uri) == "docs://installation"
    assert resource.name == "Installation Guide"
    assert resource.mimeType == "text/html"


@pytest.mark.asyncio
async def test_get_resource_not_found(config_path):
    """Verify server handles non-existent resources properly."""
    server = await UnbluDocsServer.create(config_path)
    with pytest.raises(DocumentationError) as exc_info:
        await server.get_resource("docs://nonexistent")

    assert "Resource not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_resource_handles_uri_formats(config_path):
    """Verify server handles different URI formats correctly."""
    server = await UnbluDocsServer.create(config_path)

    # These should all return the same resource
    uris = ["docs://installation", "docs://installation/", "installation"]

    resources = [await server.get_resource(uri) for uri in uris]
    assert all(r.name == "Installation Guide" for r in resources)
    assert all(str(r.uri) == "docs://installation" for r in resources)
