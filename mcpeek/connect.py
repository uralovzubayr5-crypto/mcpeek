"""Live audit path: connect to an MCP server over stdio and list its tools.

Requires the `mcp` package (pip install mcp). Kept separate so `audit.py`
stays dependency-free and testable without a running server.
"""

from __future__ import annotations

import asyncio

from .audit import ToolFinding, audit


async def collect_tools(command: str, args: list[str]) -> list[dict]:
    try:
        from mcp import ClientSession, StdioServerParameters  # type: ignore
        from mcp.client.stdio import stdio_client  # type: ignore
    except ImportError as err:  # pragma: no cover
        raise SystemExit("live mode needs the mcp package: pip install mcp") from err

    params = StdioServerParameters(command=command, args=args)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listed = await session.list_tools()
            return [
                {"name": t.name, "description": t.description, "inputSchema": t.inputSchema}
                for t in listed.tools
            ]


def audit_server(command: str, args: list[str]) -> list[ToolFinding]:
    return audit(asyncio.run(collect_tools(command, args)))
