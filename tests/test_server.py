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
    server = UnbluDocsServer(config_path)
    resources = await server.list_resources()

    assert len(resources) > 0
    assert all(isinstance(resource, types.Resource) for resource in resources)


@pytest.mark.asyncio
async def test_search_tool_integration(config_path):
    """Verify search tool functions correctly through MCP interface."""
    server = UnbluDocsServer(config_path)
    result = await server.handle_tool_call("search_docs", {"query": "installation"})

    assert isinstance(result, list)
    assert all(isinstance(item["relevance"], float) for item in result)


@pytest.mark.asyncio
async def test_invalid_tool_raises_error(config_path):
    """Verify invalid tool calls are handled properly."""
    server = UnbluDocsServer(config_path)
    with pytest.raises(DocumentationError):
        await server.handle_tool_call("nonexistent_tool", {})


@pytest.mark.asyncio
async def test_server_handles_invalid_config():
    """Verify server properly handles invalid config file."""
    with pytest.raises(DocumentationError):
        UnbluDocsServer("nonexistent_config.json")
