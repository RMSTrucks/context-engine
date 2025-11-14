"""Vision Capture MCP Server - Phase 1

This server provides on-demand screen capture with OCR capabilities.

MCP Tools:
- capture_screen: Capture full screen with OCR
- capture_region: Capture selected region with OCR
- get_window_title: Get active window title
- search_captures: Full-text search of captured text
"""

from .capture import VisionCapture
from .server import main

__all__ = ["VisionCapture", "main"]
