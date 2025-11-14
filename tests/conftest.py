"""Shared test fixtures for Context Engine"""
import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp)


@pytest.fixture
def sample_config():
    """Sample configuration for testing"""
    return {
        "vision": {
            "enabled": True,
            "capture_interval": 300,
            "ocr_language": "en",
            "retention_days": 7,
        },
        "audio": {
            "enabled": True,
            "source": "microphone",
            "model": "base.en",
            "vad_enabled": True,
        },
        "storage": {
            "database": ":memory:",  # Use in-memory DB for testing
            "chromadb_path": "test_chroma",
        },
    }


@pytest.fixture
def mock_screen_capture():
    """Mock screen capture data"""
    return {
        "timestamp": "2025-11-14T16:30:00Z",
        "window_title": "Test Window",
        "ocr_text": "Sample OCR text for testing",
        "ocr_confidence": 0.95,
        "image_hash": "abc123def456",
    }


@pytest.fixture
def mock_audio_transcript():
    """Mock audio transcript data"""
    return {
        "timestamp": "2025-11-14T16:30:00Z",
        "source": "microphone",
        "speaker": "user",
        "text": "This is a test transcript",
        "confidence": 0.92,
    }
