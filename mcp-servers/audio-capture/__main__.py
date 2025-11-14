"""Entry point for audio-capture MCP server

Run with: python -m mcp-servers.audio-capture
"""
from .server import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
