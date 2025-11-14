"""Audio Capture MCP Server - Phase 2

This server provides real-time voice transcription using faster-whisper.

MCP Tools:
- start_listening: Start real-time audio transcription
- stop_listening: Stop audio transcription
- get_transcript: Get recent transcript
- search_audio: Search audio transcripts

Usage:
    python -m mcp-servers.audio-capture
"""

from .server import main
from .transcription_service import TranscriptionService

__all__ = ["main", "TranscriptionService"]
