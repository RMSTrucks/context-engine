"""Vision Capture MCP Server

This server provides on-demand screen capture with OCR via MCP protocol.

Tools:
- capture_screen: Capture full screen with OCR
- capture_region: Capture specific region with OCR
- get_window_title: Get active window title
- search_captures: Search previously captured text
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.storage.database import Database
from shared.utils.config import load_config

# Use relative import to avoid module naming issues with hyphens
try:
    from .capture import VisionCapture
except ImportError:
    # Fallback for direct execution
    import capture as capture_module
    VisionCapture = capture_module.VisionCapture

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/vision-capture.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global instances
db: Optional[Database] = None
vision: Optional[VisionCapture] = None
config: dict = {}


def initialize():
    """Initialize database and vision capture"""
    global db, vision, config

    try:
        # Load configuration
        config = load_config()
        vision_config = config.get('vision', {})
        storage_config = config.get('storage', {})

        # Initialize database
        db_path = storage_config.get('database', 'context.db')
        db = Database(db_path)
        db.connect()
        db.create_schema()

        # Initialize vision capture
        vision = VisionCapture(
            db=db,
            screenshots_dir="screenshots",
            save_images=vision_config.get('save_images', True),
            image_quality=vision_config.get('image_quality', 85)
        )

        # Cleanup old captures on startup
        retention_days = vision_config.get('retention_days', 7)
        deleted = db.cleanup_old_captures(retention_days)
        logger.info(f"Initialization complete. Cleaned up {deleted} old captures.")

    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        raise


# Create MCP server
app = Server("vision-capture")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="capture_screen",
            description=(
                "Capture full screen with OCR. "
                "Extracts all visible text and returns it with confidence scores. "
                "Useful for understanding what's currently on screen."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "trigger_reason": {
                        "type": "string",
                        "description": "Reason for capture (e.g., 'voice_command', 'manual', 'timer')",
                        "default": "manual"
                    }
                }
            }
        ),
        Tool(
            name="capture_region",
            description=(
                "Capture specific screen region with OCR. "
                "Useful for extracting text from a particular area like a dialog box or code snippet."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {
                        "type": "integer",
                        "description": "X coordinate of top-left corner"
                    },
                    "y": {
                        "type": "integer",
                        "description": "Y coordinate of top-left corner"
                    },
                    "width": {
                        "type": "integer",
                        "description": "Width of region in pixels"
                    },
                    "height": {
                        "type": "integer",
                        "description": "Height of region in pixels"
                    },
                    "trigger_reason": {
                        "type": "string",
                        "description": "Reason for capture",
                        "default": "manual"
                    }
                },
                "required": ["x", "y", "width", "height"]
            }
        ),
        Tool(
            name="get_window_title",
            description=(
                "Get the title of the currently active window. "
                "Lightweight operation that doesn't capture or OCR anything."
            ),
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="search_captures",
            description=(
                "Search previously captured screen text using full-text search. "
                "Returns matching captures with context and timestamps."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (supports full-text search syntax)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""
    global vision, db

    if not vision or not db:
        return [TextContent(
            type="text",
            text="Error: Vision capture not initialized"
        )]

    try:
        if name == "capture_screen":
            trigger_reason = arguments.get("trigger_reason", "manual")
            capture = vision.capture_screen(trigger_reason=trigger_reason)

            result = f"""Screen Capture Complete
Timestamp: {capture.timestamp}
Window: {capture.window_title or 'Unknown'}
Confidence: {capture.ocr_confidence:.2%}

Extracted Text:
{capture.ocr_text or '(No text detected)'}
"""
            if capture.image_path:
                result += f"\nSaved to: {capture.image_path}"

            return [TextContent(type="text", text=result)]

        elif name == "capture_region":
            x = arguments["x"]
            y = arguments["y"]
            width = arguments["width"]
            height = arguments["height"]
            trigger_reason = arguments.get("trigger_reason", "manual")

            capture = vision.capture_region(
                x=x, y=y, width=width, height=height,
                trigger_reason=trigger_reason
            )

            result = f"""Region Capture Complete
Region: ({x}, {y}) - {width}x{height}
Timestamp: {capture.timestamp}
Window: {capture.window_title or 'Unknown'}
Confidence: {capture.ocr_confidence:.2%}

Extracted Text:
{capture.ocr_text or '(No text detected)'}
"""
            if capture.image_path:
                result += f"\nSaved to: {capture.image_path}"

            return [TextContent(type="text", text=result)]

        elif name == "get_window_title":
            title = vision.get_window_title()
            if title:
                return [TextContent(
                    type="text",
                    text=f"Active window: {title}"
                )]
            else:
                return [TextContent(
                    type="text",
                    text="Could not determine active window"
                )]

        elif name == "search_captures":
            query = arguments["query"]
            limit = arguments.get("limit", 10)

            results = vision.search_captures(query, limit)

            if not results:
                return [TextContent(
                    type="text",
                    text=f"No captures found matching '{query}'"
                )]

            result_text = f"Found {len(results)} capture(s) matching '{query}':\n\n"
            for i, capture in enumerate(results, 1):
                result_text += f"{i}. {capture['timestamp']}\n"
                if capture['window_title']:
                    result_text += f"   Window: {capture['window_title']}\n"

                # Show snippet of text
                text = capture['ocr_text'] or ''
                snippet = text[:200] + "..." if len(text) > 200 else text
                result_text += f"   Text: {snippet}\n"
                result_text += f"   Confidence: {capture['ocr_confidence']:.2%}\n\n"

            return [TextContent(type="text", text=result_text)]

        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]

    except Exception as e:
        logger.error(f"Tool execution failed: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


async def main():
    """Main entry point for MCP server"""
    try:
        # Initialize
        logger.info("Starting Vision Capture MCP Server...")
        initialize()

        # Run stdio server
        async with stdio_server() as (read_stream, write_stream):
            logger.info("MCP server running on stdio")
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )

    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        raise
    finally:
        # Cleanup
        if db:
            db.close()


if __name__ == "__main__":
    asyncio.run(main())
