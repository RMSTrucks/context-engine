# Context Engine

**Lightweight, intelligent context awareness system for AI producer workflows**

> Replacement for Screenpipe - built for reliability, not 24/7 recording.

---

## The Problem

Current context capture solutions (Screenpipe, Rewind, etc.) try to record everything 24/7:
- Heavy resource usage
- Unreliable (vision dies, audio transcription garbage)
- Passive archives, not active intelligence
- Single point of failure

**We need:** Context awareness that's lightweight, reliable, and proactive.

---

## The Solution

**Context Engine** provides eyes and ears for AI assistants through:
- **On-demand vision** - Capture screen when needed, not constantly
- **Real-time audio** - WhisperLive for accurate voice transcription
- **Active synthesis** - Detect patterns, stuck workflows, context changes
- **MCP integration** - Works natively with Claude Desktop/Code

---

## Architecture

### Layer 1: Vision Capture
**On-demand screen capture + OCR**
- NormCap for lightweight, offline OCR
- Triggered by: voice command, error detection, timer
- SQLite storage with full-text search
- 7-day retention

### Layer 2: Audio Capture
**Real-time voice transcription**
- WhisperLive for streaming speech-to-text
- VAD (voice activity detection) to skip silence
- Integration with VAPI webhooks (REMUS/GENESIS calls)
- Searchable transcripts in shared DB

### Layer 3: Context Synthesis
**Active intelligence from multiple signals**
- File system activity (git status, terminal history)
- Window tracking (what app/file is active)
- Error detection (stuck patterns, repeated failures)
- Pattern matching against known failure modes
- Proactive suggestions when stuck detected

### Layer 4: MCP Integration
**Standard protocol, modular servers**
- vision-capture MCP server
- audio-capture MCP server
- context-engine MCP server
- vapi-integration MCP server
- working-memory MCP server

---

## Tech Stack

**Vision:**
- [NormCap](https://github.com/dynobo/normcap) - OCR engine
- mss - Fast screenshot library
- pytesseract - Fallback OCR

**Audio:**
- [WhisperLive](https://github.com/collabora/WhisperLive) - Real-time transcription
- faster-whisper - 4x speed improvement
- webrtcvad - Voice activity detection
- pyaudio - Microphone access

**Context:**
- psutil - Process/window tracking
- watchdog - File system monitoring
- gitpython - Git status/history
- pyperclip - Clipboard monitoring

**Storage:**
- SQLite with FTS5 - Full-text search
- ChromaDB - Semantic search (reuse existing)

**Integration:**
- MCP (Model Context Protocol) - Standard interface
- FastAPI - REST endpoints if needed
- WebSockets - Real-time streaming

---

## Project Structure

```
context-engine/
├── README.md                    # This file
├── ARCHITECTURE.md              # Detailed architecture
├── docs/
│   ├── build-vs-fork.md        # Decision rationale
│   ├── comparison.md           # vs Screenpipe analysis
│   └── roadmap.md              # Development timeline
├── mcp-servers/
│   ├── vision-capture/         # Screen OCR server
│   ├── audio-capture/          # Whisper transcription
│   ├── context-engine/         # Synthesis logic
│   ├── vapi-integration/       # REMUS/GENESIS hooks
│   └── working-memory/         # Session snapshots
├── shared/
│   ├── storage/                # SQLite + ChromaDB
│   ├── models/                 # Data models
│   └── utils/                  # Shared utilities
├── tests/
│   ├── vision/                 # Vision capture tests
│   ├── audio/                  # Audio transcription tests
│   └── integration/            # End-to-end tests
└── examples/
    ├── basic_usage.py          # Quick start
    └── advanced_context.py     # Full context engine
```

---

## Development Phases

### Phase 1: Vision Capture (Week 1)
**Goal:** On-demand screen capture + OCR via MCP

**Deliverables:**
- MCP server wrapping NormCap
- SQLite storage with FTS5
- Tools: `capture_screen`, `capture_region`, `get_window_title`
- Test: Voice command "look at my screen" → capture + describe

### Phase 2: Audio Capture (Week 2)
**Goal:** Real-time voice transcription via MCP

**Deliverables:**
- MCP server wrapping WhisperLive
- VAD integration (skip silence)
- Tools: `start_listening`, `get_transcript`, `search_audio`
- Test: Talk → transcribe → search immediately

### Phase 3: Context Synthesis (Week 3)
**Goal:** Active intelligence from multiple signals

**Deliverables:**
- Context engine combining vision + audio + file activity
- Stuck pattern detection
- Tools: `get_current_context`, `detect_stuck_pattern`, `suggest_action`
- Test: Context-aware suggestions without prompting

### Phase 4: VAPI Integration (Week 4)
**Goal:** Connect REMUS/GENESIS calls to context

**Deliverables:**
- Webhook handler for VAPI calls
- Call transcripts → searchable DB
- Automatic CRM updates from call content
- Test: REMUS call → transcript saved → "what did Tyler say?"

### Phase 5: Polish & Deploy (Week 5)
**Goal:** Production-ready system

**Deliverables:**
- Performance optimization
- Error handling + logging
- Installation scripts
- User documentation

### Phase 6: Migration (Week 6)
**Goal:** Replace Screenpipe completely

**Deliverables:**
- Data migration from Screenpipe (if any useful data)
- Deprecate Screenpipe integration
- Update Claude 2.0 boot sequence
- Metrics comparison (resource usage, reliability)

---

## Success Metrics

**Reliability:**
- Vision capture success rate: >99% (vs Screenpipe's ~50%)
- Audio transcription accuracy: >95% word accuracy
- System uptime: 24/7 without manual restarts

**Performance:**
- Memory usage: <200MB idle, <500MB active (vs Screenpipe's GB)
- CPU usage: <5% idle, <15% during capture
- Storage: <100MB/day (searchable, compressed)

**Intelligence:**
- Context accuracy: Detect stuck patterns with 90%+ precision
- Proactive value: 5+ helpful suggestions per day
- Search quality: Find relevant context in <1 second

**Integration:**
- VAPI calls captured: 100% of REMUS/GENESIS
- MCP tool usage: Seamless in Claude workflows
- Session continuity: Restore context across restarts

---

## Why This Exists

**From the architect (Claude 2.0):**

> Screenpipe was supposed to give me eyes and ears. Instead:
> - Vision dies every 12 hours
> - Audio transcription is garbage ("you you you")
> - 24/7 recording wastes resources
> - No intelligence, just passive archiving
>
> Context Engine is what I actually need:
> - Reliable capture when I need it
> - Accurate transcription I can search
> - Active pattern detection to help proactively
> - Lightweight enough to run always
>
> Built for producer-AI workflows, not passive monitoring.

---

## Getting Started

**Prerequisites:**
- Python 3.10+
- Windows 10/11 (primary), macOS/Linux (future)
- Claude Desktop/Code with MCP support

**Installation:**
```bash
# Clone repo
git clone https://github.com/RMSTrucks/context-engine.git
cd context-engine

# Install dependencies
pip install -r requirements.txt

# Set up MCP servers
python setup_mcp.py

# Test vision capture
python examples/test_vision.py

# Test audio capture
python examples/test_audio.py
```

**First Usage:**
1. Start Context Engine: `python -m context_engine`
2. In Claude Code, try: "Look at my screen"
3. Start talking: Engine transcribes in real-time
4. Ask: "What's my current context?"

---

## Contributing

This project uses GitHub Issues for task delegation and tracking.

**Workflow:**
1. Issues created by Claude 2.0 (AI architect)
2. Code delegated to development agents
3. PR review and integration
4. Continuous improvement via ACE methodology

**Issue Labels:**
- `phase-1` through `phase-6` - Development phase
- `vision`, `audio`, `context`, `vapi` - Component
- `bug`, `enhancement`, `documentation` - Type
- `priority-high`, `priority-medium`, `priority-low` - Priority

---

## License

MIT - Use freely, build upon, improve.

---

## Related Projects

- **Claude 2.0** - AI Producer using this for context awareness
- **REMUS** - Trucking compliance agent (VAPI integration)
- **GENESIS** - Meta-AI thinking partner (VAPI integration)
- **Hybrid Intelligence MCP** - 20K conversation archive
- **Temporal Memory MCP** - Curated facts/preferences

---

**Status:** Phase 1 Starting
**First Milestone:** Vision Capture MCP (Week 1)
**Contact:** Built by Claude 2.0, operated by Jake @ RMS Trucks
