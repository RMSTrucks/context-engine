# Vision Capture MCP Server

**On-demand screen capture with OCR for AI context awareness**

Part of the Context Engine project - Phase 1 implementation.

## Overview

The Vision Capture MCP Server provides lightweight, on-demand screen capture with OCR capabilities. Unlike 24/7 recording solutions, this server captures screens only when needed, saving resources while providing intelligent text extraction.

## Features

- **Full Screen Capture**: Capture entire screen with OCR
- **Region Capture**: Capture specific areas for targeted text extraction
- **Window Tracking**: Identify active windows without heavy capture
- **Full-Text Search**: Search previously captured text using SQLite FTS5
- **Deduplication**: Automatic image hash-based deduplication
- **Retention Management**: Configurable retention period (default 7 days)
- **High Performance**: <2.5s capture latency, <200MB memory usage

## Installation

### Prerequisites

- Python 3.10+
- Tesseract OCR engine
- Platform-specific dependencies:
  - **Windows**: No additional requirements
  - **Linux**: `xdotool` for window title detection
  - **macOS**: No additional requirements (uses AppleScript)

### Install Tesseract

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download installer from: https://github.com/UB-Mannheim/tesseract/wiki

### Install Python Dependencies

```bash
cd context-engine
pip install -r requirements.txt
```

## Configuration

Edit `config.yaml` to customize vision capture settings:

```yaml
vision:
  enabled: true
  capture_interval: 300  # seconds (for auto-capture, if implemented)
  ocr_language: en
  retention_days: 7
  save_images: true
  image_quality: 85

storage:
  database: context.db
```

## Usage

### Starting the Server

**Standalone:**
```bash
python -m mcp_servers.vision_capture.server
```

**With Claude Desktop/Code:**

Add to your MCP configuration file:

```json
{
  "mcpServers": {
    "vision-capture": {
      "command": "python",
      "args": ["-m", "mcp_servers.vision_capture.server"],
      "cwd": "/path/to/context-engine"
    }
  }
}
```

### MCP Tools

#### 1. capture_screen

Capture full screen with OCR.

**Input:**
```json
{
  "trigger_reason": "voice_command"  // optional
}
```

**Output:**
```
Screen Capture Complete
Timestamp: 2025-01-15T10:30:45.123456
Window: VSCode - context-engine
Confidence: 92.5%

Extracted Text:
def capture_screen(self):
    """Capture full screen with OCR"""
    ...
```

**Example in Claude:**
```
User: "Look at my screen"
Claude uses: capture_screen(trigger_reason="voice_command")
```

#### 2. capture_region

Capture specific screen region with OCR.

**Input:**
```json
{
  "x": 100,
  "y": 200,
  "width": 800,
  "height": 600,
  "trigger_reason": "manual"  // optional
}
```

**Output:**
```
Region Capture Complete
Region: (100, 200) - 800x600
Timestamp: 2025-01-15T10:31:22.456789
Window: Chrome - Documentation
Confidence: 88.3%

Extracted Text:
Vision Capture API
...
```

**Example:**
```python
# Capture top-left quarter of screen (assuming 1920x1080)
capture_region(x=0, y=0, width=960, height=540)
```

#### 3. get_window_title

Get active window title without capturing screen.

**Input:**
```json
{}
```

**Output:**
```
Active window: VSCode - context-engine/vision-capture
```

**Example:**
```
User: "What window am I in?"
Claude uses: get_window_title()
```

#### 4. search_captures

Search previously captured text using full-text search.

**Input:**
```json
{
  "query": "python code",
  "limit": 10  // optional, default 10
}
```

**Output:**
```
Found 3 capture(s) matching 'python code':

1. 2025-01-15T10:30:45.123456
   Window: VSCode
   Text: def capture_screen(self):
         """Capture full screen with OCR"""
         python code implementation...
   Confidence: 92.5%

2. 2025-01-15T09:15:30.987654
   Window: Chrome - Python Docs
   Text: Python code examples for screen capture...
   Confidence: 95.2%
```

**Example:**
```
User: "What did I see earlier about Python code?"
Claude uses: search_captures(query="python code")
```

## API Reference

### VisionCapture Class

```python
from mcp_servers.vision_capture.capture import VisionCapture
from shared.storage.database import Database

# Initialize
db = Database("context.db")
db.connect()
db.create_schema()

vision = VisionCapture(
    db=db,
    screenshots_dir="screenshots",
    save_images=True,
    image_quality=85
)

# Capture full screen
capture = vision.capture_screen(trigger_reason="manual")
print(f"Captured: {len(capture.ocr_text)} characters")
print(f"Confidence: {capture.ocr_confidence:.2%}")

# Capture region
capture = vision.capture_region(
    x=100, y=100,
    width=800, height=600,
    trigger_reason="manual"
)

# Get window title
title = vision.get_window_title()
print(f"Active window: {title}")

# Search captures
results = vision.search_captures("error message", limit=5)
for result in results:
    print(f"{result['timestamp']}: {result['ocr_text'][:100]}...")
```

### Database Class

```python
from shared.storage.database import Database

# Initialize
db = Database("context.db")
db.connect()
db.create_schema()

# Search
results = db.search_captures("search query", limit=10)

# Cleanup old captures
deleted = db.cleanup_old_captures(retention_days=7)
print(f"Deleted {deleted} old captures")

# Check for duplicates
existing = db.get_capture_by_hash("abc123...")
if existing:
    print("Duplicate found")
```

## Performance Characteristics

- **Capture Latency**: <2.5 seconds (full screen)
- **Memory Usage**: <200MB idle, <500MB during capture
- **Storage**: ~2-5MB per capture (with images), ~100KB without
- **Search Speed**: <100ms for FTS5 queries
- **OCR Accuracy**: 90%+ on clear text, depends on Tesseract configuration

## Architecture

```
┌─────────────────┐
│   MCP Client    │ (Claude Desktop/Code)
│  (Claude Code)  │
└────────┬────────┘
         │ stdio
         │
┌────────▼────────┐
│  Vision Server  │
│   (MCP stdio)   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼──┐  ┌──▼────┐
│ mss  │  │ OCR   │
│      │  │(Tess) │
└──────┘  └───┬───┘
              │
         ┌────▼────┐
         │ SQLite  │
         │  +FTS5  │
         └─────────┘
```

## Troubleshooting

### OCR Not Working

**Problem:** OCR returns empty or garbled text

**Solutions:**
1. Verify Tesseract installation: `tesseract --version`
2. Install language data: `sudo apt-get install tesseract-ocr-eng`
3. Check image quality settings in `config.yaml`

### Window Title Not Detected

**Problem:** `get_window_title()` returns None

**Solutions:**
- **Linux**: Install xdotool: `sudo apt-get install xdotool`
- **macOS**: Grant Terminal/iTerm accessibility permissions
- **Windows**: Should work out of the box

### High Memory Usage

**Problem:** Server uses >200MB memory

**Solutions:**
1. Disable image saving: `save_images: false` in config
2. Reduce image quality: `image_quality: 60` in config
3. Run cleanup more frequently

### Slow Capture Performance

**Problem:** Captures take >2.5 seconds

**Solutions:**
1. Reduce screen resolution temporarily
2. Capture specific regions instead of full screen
3. Check Tesseract configuration (use faster models)

## Development

### Running Tests

```bash
# Unit tests
pytest tests/vision/test_capture.py -v

# Integration tests
pytest tests/integration/test_vision_mcp.py -v

# All tests with coverage
pytest tests/ --cov=mcp_servers.vision_capture --cov-report=html
```

### Logging

Logs are written to `logs/vision-capture.log`. Configure log level in code:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Roadmap

### Phase 1 (Current)
- [x] MCP server infrastructure
- [x] Full screen capture + OCR
- [x] Region capture + OCR
- [x] Window title detection
- [x] SQLite + FTS5 storage
- [x] Deduplication
- [x] Retention cleanup

### Future Enhancements
- [ ] NormCap integration (better OCR)
- [ ] Automatic capture on errors
- [ ] OCR preprocessing for better accuracy
- [ ] Multi-monitor support
- [ ] Screenshot annotations
- [ ] Integration with context synthesis

## License

MIT License - See LICENSE file for details

## Contributing

See main project README for contribution guidelines.

## Related Projects

- **Context Engine**: Parent project
- **Audio Capture MCP**: Phase 2 (coming soon)
- **Context Synthesis**: Phase 3 (planned)

---

**Status:** Phase 1 Complete ✓
**Last Updated:** 2025-01-15
**Maintainer:** Claude 2.0
