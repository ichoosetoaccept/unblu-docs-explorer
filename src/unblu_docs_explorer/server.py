"""MCP server implementation for Unblu documentation explorer."""

import json
import mcp.types as types
from mcp.server import Server
from pydantic import AnyUrl
import mcp.server.stdio
import asyncio

from .search import DocumentationSearch
from .errors import DocumentationError


class UnbluDocsServer:
    """MCP server for Unblu documentation."""

    @classmethod
    async def create(cls, config_path: str) -> "UnbluDocsServer":
        """Create and initialize a new server instance."""
        server = cls()
        await server._initialize(config_path)
        return server

    def __init__(self):
        """Initialize instance variables."""
        self.config = None
        self.search = DocumentationSearch()

    async def _initialize(self, config_path: str):
        """Initialize server with config file."""
        self.config = self._load_config(config_path)
        await self._index_documents()

    def _load_config(self, config_path: str) -> dict:
        """Load and validate config file."""
        try:
            with open(config_path) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise DocumentationError(
                f"Failed to load config from {config_path}", operation="load_config", original_error=e
            )

    async def _index_documents(self):
        """Index all documentation sections."""
        for section in self.config["sections"]:
            await self.search.index_document(
                {
                    "title": section["title"],
                    "content": section.get("content", f"Documentation section for {section['title']}"),
                    "path": section["path"],
                    "metadata": {"section": section["path"].lstrip("/")},
                }
            )

    async def list_resources(self) -> list[types.Resource]:
        """List available documentation sections."""
        return [
            types.Resource(
                uri=AnyUrl(f"docs://{section['path'].lstrip('/')}"),
                name=section["title"],
                description=f"Documentation for {section['title']}",
                mimeType="text/html",
            )
            for section in self.config["sections"]
        ]

    async def get_resource(self, uri: str) -> types.Resource:
        """Get a specific documentation resource."""
        # Convert AnyUrl to string if needed
        uri_str = str(uri) if not isinstance(uri, str) else uri
        # Remove the docs:// prefix and any leading/trailing slashes
        path = "/" + uri_str.replace("docs://", "").strip("/")

        for section in self.config["sections"]:
            if section["path"] == path:
                return types.Resource(
                    uri=AnyUrl(f"docs://{section['path'].lstrip('/')}"),
                    name=section["title"],
                    description=section.get("content", f"Documentation for {section['title']}"),
                    mimeType="text/html",
                    content=section.get("content", f"Documentation for {section['title']}"),
                )
        raise DocumentationError(f"Resource not found: {uri}", operation="get_resource")

    async def handle_tool_call(self, name: str, arguments: dict | None) -> any:
        """Handle tool execution requests."""
        if name == "search_docs":
            if not arguments or "query" not in arguments:
                raise DocumentationError("Missing required 'query' argument", operation="search_docs")
            return await self.search.search(arguments["query"], context=arguments.get("context"))
        raise DocumentationError(f"Unknown tool: {name}", operation="handle_tool")


# Initialize the MCP server
server = Server("unblu-docs-explorer")

# Global variable to store server instance
_docs_server = None


async def get_docs_server(config_path: str = "config.json") -> UnbluDocsServer:
    """Get or create UnbluDocsServer instance."""
    global _docs_server
    if _docs_server is None:
        _docs_server = await UnbluDocsServer.create(config_path)
    return _docs_server


@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """List available documentation resources."""
    docs_server = await get_docs_server()
    return await docs_server.list_resources()


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    return [
        types.Tool(
            name="search_docs",
            description="Search through Unblu documentation",
            arguments={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "context": {"type": "string", "description": "Optional section to search within"},
                },
                "required": ["query"],
            },
        )
    ]


@server.read_resource()
async def handle_get_resource(uri: str) -> types.Resource:
    """Handle resource retrieval requests."""
    docs_server = await get_docs_server()
    return await docs_server.get_resource(uri)


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> any:
    """Handle tool execution requests."""
    docs_server = await get_docs_server()
    return await docs_server.handle_tool_call(name, arguments)


async def main():
    """Run the MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
