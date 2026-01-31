"""Memory tools - semantic search and retrieval.

Based on OpenClaw memory-tool.ts
"""

from typing import Any

from mcp.types import Tool

from ..gateway import OpenClawGateway

SEARCH_DESCRIPTION = """Semantic search across MEMORY.md and memory/*.md files.

Use this tool before answering questions about:
- Prior work and decisions
- Dates and timelines
- People and contacts
- Preferences and settings
- TODOs and tasks

Returns top matching snippets with file path and line numbers.

PARAMETERS:
- query: Search query (required)
- maxResults: Maximum results to return (optional, default 10)
- minScore: Minimum similarity score (optional, 0.0-1.0)

EXAMPLE:
{
  "query": "what did we decide about authentication",
  "maxResults": 5
}
"""

GET_DESCRIPTION = """Read specific lines from memory files.

Use after memory_search to retrieve full context for a snippet.
Keeps context small by only pulling needed lines.

PARAMETERS:
- path: Relative path to file (required)
- from: Starting line number (optional)
- lines: Number of lines to read (optional)

EXAMPLE:
{
  "path": "memory/2024-01-15.md",
  "from": 42,
  "lines": 20
}
"""


def get_search_tool_definition() -> Tool:
    """Get MCP tool definition for memory_search."""
    return Tool(
        name="memory_search",
        description=SEARCH_DESCRIPTION,
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query",
                },
                "maxResults": {
                    "type": "integer",
                    "description": "Maximum results to return",
                },
                "minScore": {
                    "type": "number",
                    "description": "Minimum similarity score (0.0-1.0)",
                },
            },
            "required": ["query"],
        },
    )


def get_get_tool_definition() -> Tool:
    """Get MCP tool definition for memory_get."""
    return Tool(
        name="memory_get",
        description=GET_DESCRIPTION,
        inputSchema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path to file",
                },
                "from": {
                    "type": "integer",
                    "description": "Starting line number",
                },
                "lines": {
                    "type": "integer",
                    "description": "Number of lines to read",
                },
            },
            "required": ["path"],
        },
    )


async def execute_search(gateway: OpenClawGateway, params: dict[str, Any]) -> dict[str, Any]:
    """Execute memory_search tool via OpenClaw Gateway."""
    query = params.get("query")
    if not query:
        return {"error": "query required"}

    return await gateway.call_tool(
        "memory.search",
        {
            "query": query,
            "maxResults": params.get("maxResults"),
            "minScore": params.get("minScore"),
        },
    )


async def execute_get(gateway: OpenClawGateway, params: dict[str, Any]) -> dict[str, Any]:
    """Execute memory_get tool via OpenClaw Gateway."""
    path = params.get("path")
    if not path:
        return {"error": "path required"}

    return await gateway.call_tool(
        "memory.get",
        {
            "path": path,
            "from": params.get("from"),
            "lines": params.get("lines"),
        },
    )
