"""Audio Capture MCP Server

This MCP server provides real-time audio transcription using faster-whisper.

Available tools:
- start_listening: Start real-time audio transcription
- stop_listening: Stop audio transcription
- get_transcript: Get recent transcript
- search_audio: Search audio transcripts
"""
import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp.server import Server
from mcp.types import Tool, TextContent

from shared.storage.database import Database
from shared.models.audio_transcript import AudioTranscript
from .transcription_service import TranscriptionService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global state
db: Optional[Database] = None
transcription_service: Optional[TranscriptionService] = None


def on_transcript(transcript: AudioTranscript):
    """Callback for new transcripts

    Args:
        transcript: New transcript to save
    """
    global db

    try:
        if db:
            db.save_audio_transcript(transcript)
            logger.info(f"Saved transcript: {transcript.text[:50]}...")
    except Exception as e:
        logger.error(f"Error saving transcript: {e}")


async def start_listening(arguments: dict) -> list[TextContent]:
    """Start real-time audio transcription

    Args:
        arguments: Tool arguments containing:
            - source: Audio source ('microphone', 'system_audio', 'both')
            - language: Language code (default: 'en')

    Returns:
        Status message
    """
    global transcription_service, db

    source = arguments.get("source", "microphone")
    language = arguments.get("language", "en")

    try:
        # Initialize database if needed
        if db is None:
            db = Database()
            db.connect()
            db.create_schema()

        # Initialize transcription service if needed
        if transcription_service is None:
            transcription_service = TranscriptionService(
                model_size="base.en" if language == "en" else "base",
                language=language,
            )

        # Start listening
        transcription_service.start_listening(callback=on_transcript)

        return [
            TextContent(
                type="text",
                text=f"Started listening to {source}. Transcription is now active.",
            )
        ]

    except Exception as e:
        logger.error(f"Error starting transcription: {e}")
        return [
            TextContent(
                type="text",
                text=f"Error starting transcription: {str(e)}",
            )
        ]


async def stop_listening(arguments: dict) -> list[TextContent]:
    """Stop audio transcription

    Args:
        arguments: Tool arguments (none required)

    Returns:
        Status message
    """
    global transcription_service

    try:
        if transcription_service is None:
            return [
                TextContent(
                    type="text",
                    text="Transcription is not currently active.",
                )
            ]

        transcription_service.stop_listening()

        return [
            TextContent(
                type="text",
                text="Stopped listening. Transcription is now inactive.",
            )
        ]

    except Exception as e:
        logger.error(f"Error stopping transcription: {e}")
        return [
            TextContent(
                type="text",
                text=f"Error stopping transcription: {str(e)}",
            )
        ]


async def get_transcript(arguments: dict) -> list[TextContent]:
    """Get recent transcript

    Args:
        arguments: Tool arguments containing:
            - minutes: How many minutes back to retrieve (default: 5)

    Returns:
        Recent transcripts
    """
    global db

    minutes = arguments.get("minutes", 5)

    try:
        # Initialize database if needed
        if db is None:
            db = Database()
            db.connect()
            db.create_schema()

        # Get recent transcripts
        transcripts = db.get_recent_transcripts(minutes=minutes, source="microphone")

        if not transcripts:
            return [
                TextContent(
                    type="text",
                    text=f"No transcripts found in the last {minutes} minutes.",
                )
            ]

        # Format transcripts
        result_lines = [f"# Transcripts from last {minutes} minutes\n"]

        for t in transcripts:
            timestamp = t["timestamp"].split("T")[1].split(".")[0]  # Get time only
            text = t["text"]
            result_lines.append(f"[{timestamp}] {text}")

        return [
            TextContent(
                type="text",
                text="\n".join(result_lines),
            )
        ]

    except Exception as e:
        logger.error(f"Error getting transcripts: {e}")
        return [
            TextContent(
                type="text",
                text=f"Error getting transcripts: {str(e)}",
            )
        ]


async def search_audio(arguments: dict) -> list[TextContent]:
    """Search audio transcripts

    Args:
        arguments: Tool arguments containing:
            - query: Search query
            - days_back: Number of days to search (default: 7)

    Returns:
        Matching transcripts
    """
    global db

    query = arguments.get("query")
    days_back = arguments.get("days_back", 7)

    if not query:
        return [
            TextContent(
                type="text",
                text="Error: 'query' parameter is required",
            )
        ]

    try:
        # Initialize database if needed
        if db is None:
            db = Database()
            db.connect()
            db.create_schema()

        # Search transcripts
        results = db.search_audio_transcripts(query=query, days_back=days_back)

        if not results:
            return [
                TextContent(
                    type="text",
                    text=f"No transcripts found matching '{query}' in the last {days_back} days.",
                )
            ]

        # Format results
        result_lines = [f"# Search results for '{query}' ({len(results)} matches)\n"]

        for r in results:
            timestamp = r["timestamp"].split("T")[0]  # Get date
            time = r["timestamp"].split("T")[1].split(".")[0]  # Get time
            text = r["text"]
            source = r["source"]

            result_lines.append(f"**{timestamp} {time}** ({source})")
            result_lines.append(f"{text}\n")

        return [
            TextContent(
                type="text",
                text="\n".join(result_lines),
            )
        ]

    except Exception as e:
        logger.error(f"Error searching transcripts: {e}")
        return [
            TextContent(
                type="text",
                text=f"Error searching transcripts: {str(e)}",
            )
        ]


async def main():
    """Main entry point for MCP server"""
    logger.info("Starting Audio Capture MCP Server")

    # Create server instance
    server = Server("audio-capture")

    # Register tools
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="start_listening",
                description="Start real-time audio transcription from microphone",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "source": {
                            "type": "string",
                            "enum": ["microphone", "system_audio", "both"],
                            "default": "microphone",
                            "description": "Audio source to capture",
                        },
                        "language": {
                            "type": "string",
                            "default": "en",
                            "description": "Language code (e.g., 'en', 'es', 'fr')",
                        },
                    },
                },
            ),
            Tool(
                name="stop_listening",
                description="Stop audio transcription",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="get_transcript",
                description="Get recent transcript from the last N minutes",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "minutes": {
                            "type": "number",
                            "default": 5,
                            "description": "How many minutes back to retrieve transcripts",
                        },
                    },
                },
            ),
            Tool(
                name="search_audio",
                description="Search audio transcripts using full-text search",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query",
                        },
                        "days_back": {
                            "type": "number",
                            "default": 7,
                            "description": "Number of days to search back",
                        },
                    },
                    "required": ["query"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Handle tool calls"""
        logger.info(f"Tool called: {name} with arguments: {arguments}")

        if name == "start_listening":
            return await start_listening(arguments)
        elif name == "stop_listening":
            return await stop_listening(arguments)
        elif name == "get_transcript":
            return await get_transcript(arguments)
        elif name == "search_audio":
            return await search_audio(arguments)
        else:
            return [
                TextContent(
                    type="text",
                    text=f"Unknown tool: {name}",
                )
            ]

    # Run server
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        logger.info("Server running on stdio")
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    finally:
        # Cleanup
        if transcription_service:
            transcription_service.cleanup()
        if db:
            db.close()
