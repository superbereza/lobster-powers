"""MCP server exposing OpenClaw tools to Claude Code."""

import asyncio
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .gateway import OpenClawGateway
from .tools import cron, memory

logger = logging.getLogger(__name__)

# Initialize MCP server
server = Server("openclaw-tools")

# Gateway client (lazy init)
_gateway: OpenClawGateway | None = None


def get_gateway() -> OpenClawGateway:
    """Get or create gateway client."""
    global _gateway
    if _gateway is None:
        _gateway = OpenClawGateway()
    return _gateway


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available OpenClaw tools."""
    return [
        cron.get_tool_definition(),
        memory.get_search_tool_definition(),
        memory.get_get_tool_definition(),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute an OpenClaw tool."""
    gateway = get_gateway()

    try:
        if name == "cron":
            result = await cron.execute(gateway, arguments)
        elif name == "memory_search":
            result = await memory.execute_search(gateway, arguments)
        elif name == "memory_get":
            result = await memory.execute_get(gateway, arguments)
        else:
            result = {"error": f"Unknown tool: {name}"}

        return [TextContent(type="text", text=str(result))]

    except Exception as e:
        logger.exception(f"Tool {name} failed")
        return [TextContent(type="text", text=f"Error: {e}")]


async def serve():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main():
    """Entry point."""
    logging.basicConfig(level=logging.INFO)
    asyncio.run(serve())


if __name__ == "__main__":
    main()
