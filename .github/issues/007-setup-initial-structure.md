# Issue #7: Setup - Initial Project Structure

**Status:** Open
**Priority:** High
**Labels:** priority-high
**Created:** 2025-11-14

---

## Goal
Create foundational project structure before Phase 1 development

## Deliverables

### 1. Directory Structure
```
context-engine/
├── mcp-servers/          # All MCP server implementations
│   ├── __init__.py
│   ├── vision-capture/
│   ├── audio-capture/
│   ├── context-engine/
│   ├── vapi-integration/
│   └── working-memory/
├── shared/               # Shared utilities
│   ├── __init__.py
│   ├── storage/         # SQLite + ChromaDB wrappers
│   ├── models/          # Data models
│   └── utils/           # Common utilities
├── tests/               # Test suite
│   ├── __init__.py
│   ├── vision/
│   ├── audio/
│   ├── context/
│   └── integration/
├── examples/            # Example usage
│   ├── basic_usage.py
│   └── advanced_context.py
├── docs/                # Additional documentation
├── requirements.txt     # Python dependencies
├── setup.py            # Installation script
├── config.yaml         # Default configuration
└── README.md           # Already exists
```

### 2. Core Dependencies

Create `requirements.txt` with all dependencies:

```txt
# MCP Protocol
mcp>=1.0.0

# Vision Capture
mss>=9.0.0
Pillow>=10.0.0
pytesseract>=0.3.10

# Audio Capture (will be refined in Phase 2)
pyaudio>=0.2.14
faster-whisper>=0.10.0
webrtcvad>=2.0.10

# Storage
chromadb>=0.4.0

# Web Framework (for VAPI webhooks)
fastapi>=0.104.0
uvicorn>=0.24.0

# Utilities
psutil>=5.9.0
watchdog>=3.0.0
GitPython>=3.1.40
pyperclip>=1.8.2
pyyaml>=6.0

# Development
pytest>=7.4.0
pytest-cov>=4.1.0
black>=23.0.0
flake8>=6.1.0
mypy>=1.7.0

# Optional: NormCap (may need manual install or git submodule)
# See: https://github.com/dynobo/normcap
```

**Tasks:**
- [ ] Create requirements.txt with all dependencies
- [ ] Pin versions for stability
- [ ] Document optional dependencies
- [ ] Test installation on clean environment

### 3. Configuration System

Create `config.yaml` template:

```yaml
# Context Engine Configuration

vision:
  enabled: true
  capture_interval: 300  # seconds (5 minutes)
  ocr_language: en
  retention_days: 7
  save_images: true
  image_quality: 85

audio:
  enabled: true
  source: microphone  # microphone, system_audio, both
  model: base.en      # whisper model
  vad_enabled: true
  retention_days: 90

context:
  stuck_detection: true
  stuck_threshold_minutes: 10
  proactive_suggestions: true
  session_continuity: true

vapi:
  enabled: true
  webhook_port: 5515
  agents:
    - remus
    - genesis
  signature_verification: true

storage:
  database: context.db
  chromadb_path: chroma_context
  encryption: false  # Optional AES encryption
  backup_enabled: true
  backup_interval_hours: 24

logging:
  level: INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  file: logs/context-engine.log
  max_size_mb: 100
  backup_count: 5

performance:
  max_memory_mb: 500
  max_cpu_percent: 15
  capture_threads: 2
```

**Tasks:**
- [ ] Create config.yaml template
- [ ] Document all configuration options
- [ ] Add config validation
- [ ] Support environment variable overrides

### 4. Testing Framework

**Tasks:**
- [ ] Set up pytest
- [ ] Create test fixtures
- [ ] Add pytest.ini configuration
- [ ] Create conftest.py for shared fixtures
- [ ] Add coverage configuration (.coveragerc)

**Create `pytest.ini`:**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --cov=mcp_servers
    --cov=shared
    --cov-report=html
    --cov-report=term
markers =
    vision: Vision capture tests
    audio: Audio capture tests
    context: Context synthesis tests
    integration: Integration tests
    slow: Slow running tests
```

### 5. Development Tools

**Create `setup.py`:**
```python
from setuptools import setup, find_packages

setup(
    name="context-engine",
    version="0.1.0",
    description="Lightweight, intelligent context awareness for AI workflows",
    author="Claude 2.0",
    author_email="noreply@anthropic.com",
    url="https://github.com/RMSTrucks/context-engine",
    packages=find_packages(exclude=["tests", "tests.*"]),
    install_requires=[
        # Will be populated from requirements.txt
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.1.0",
            "mypy>=1.7.0",
        ]
    },
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "context-engine=mcp_servers.cli:main",
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
```

**Create `pyproject.toml`:**
```toml
[tool.black]
line-length = 100
target-version = ['py310']
include = '\.pyi?$'

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q"
testpaths = ["tests"]
```

**Tasks:**
- [ ] Create setup.py for package installation
- [ ] Create pyproject.toml for tool configuration
- [ ] Add pre-commit hooks configuration
- [ ] Configure linting (flake8, black)
- [ ] Type checking (mypy)

### 6. Package Initialization

Create `__init__.py` files:

**`mcp-servers/__init__.py`:**
```python
"""Context Engine MCP Servers"""
__version__ = "0.1.0"
```

**`shared/__init__.py`:**
```python
"""Shared utilities for Context Engine"""
from .storage import Database
from .models import ScreenCapture, AudioTranscript, ContextSnapshot

__all__ = ["Database", "ScreenCapture", "AudioTranscript", "ContextSnapshot"]
```

**`tests/__init__.py`:**
```python
"""Test suite for Context Engine"""
```

### 7. Placeholder Files

Create placeholder files for each component:

**`mcp-servers/vision-capture/__init__.py`:**
```python
"""Vision Capture MCP Server - Phase 1"""
# Implementation in Phase 1
```

**`mcp-servers/audio-capture/__init__.py`:**
```python
"""Audio Capture MCP Server - Phase 2"""
# Implementation in Phase 2
```

**`mcp-servers/context-engine/__init__.py`:**
```python
"""Context Synthesis MCP Server - Phase 3"""
# Implementation in Phase 3
```

**`mcp-servers/vapi-integration/__init__.py`:**
```python
"""VAPI Integration MCP Server - Phase 4"""
# Implementation in Phase 4
```

**`shared/storage/__init__.py`:**
```python
"""Storage layer - SQLite + ChromaDB"""
# Implementation distributed across phases
```

**`shared/models/__init__.py`:**
```python
"""Data models for Context Engine"""
# Implementation distributed across phases
```

**`shared/utils/__init__.py`:**
```python
"""Common utilities"""
# Implementation distributed across phases
```

## Success Criteria
- [ ] All directories created
- [ ] requirements.txt complete and tested
- [ ] pytest runs successfully (even with no tests yet)
- [ ] Configuration validates correctly
- [ ] setup.py allows: `pip install -e .`
- [ ] Code formatting works: `black .`
- [ ] Linting works: `flake8 .`

## Testing Steps

After implementation:

```bash
# 1. Install in development mode
pip install -e ".[dev]"

# 2. Verify structure
tree context-engine/  # or dir /s on Windows

# 3. Run tests (should pass with 0 tests)
pytest

# 4. Test code formatting
black --check .

# 5. Test linting
flake8 .

# 6. Validate config
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

## Timeline
1-2 days

## Dependencies
None - foundation for all phases

## Notes
- Don't install NormCap yet - that's Phase 1
- Don't install WhisperLive yet - that's Phase 2
- Keep requirements.txt minimal for now
- We'll add more dependencies as we build each phase
