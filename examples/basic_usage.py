"""Basic usage example for Context Engine

This example demonstrates basic setup and usage of Context Engine.
Full implementation will be available after Phase 1.
"""
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    """Basic usage example"""
    print("Context Engine - Basic Usage Example")
    print("=" * 50)
    print()

    # Step 1: Load configuration
    print("Step 1: Load configuration")
    print("  from shared.utils.config import load_config")
    print("  config = load_config('config.yaml')")
    print()

    # Step 2: Initialize database
    print("Step 2: Initialize database")
    print("  from shared.storage.database import Database")
    print("  db = Database(config['storage']['database'])")
    print("  db.connect()")
    print()

    # Step 3: Use vision capture (Phase 1)
    print("Step 3: Capture screen (Phase 1)")
    print("  # Via MCP in Claude Code:")
    print("  # 'Look at my screen'")
    print("  # OR via Python:")
    print("  # from mcp_servers.vision_capture import capture_screen")
    print("  # result = capture_screen(reason='manual capture')")
    print()

    # Step 4: Use audio capture (Phase 2)
    print("Step 4: Start audio transcription (Phase 2)")
    print("  # Via MCP in Claude Code:")
    print("  # 'Start listening'")
    print("  # OR via Python:")
    print("  # from mcp_servers.audio_capture import start_listening")
    print("  # start_listening(source='microphone')")
    print()

    # Step 5: Get context (Phase 3)
    print("Step 5: Get current context (Phase 3)")
    print("  # Via MCP in Claude Code:")
    print("  # 'What's my current context?'")
    print("  # OR via Python:")
    print("  # from mcp_servers.context_engine import get_current_context")
    print("  # context = get_current_context(depth='full')")
    print()

    print("=" * 50)
    print("NOTE: This is a placeholder example.")
    print("Full implementation will be available as phases are completed.")
    print()
    print("To use Context Engine with Claude Code:")
    print("1. Install: pip install -e .")
    print("2. Configure MCP servers in Claude Desktop/Code")
    print("3. Use natural language commands in chat")


if __name__ == "__main__":
    main()
