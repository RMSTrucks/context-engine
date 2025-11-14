"""Integration tests for Audio Capture MCP Server

These tests verify the MCP server tools work correctly.
"""
import os
import tempfile
import pytest

from shared.storage.database import Database
from shared.models.audio_transcript import AudioTranscript
from datetime import datetime


@pytest.fixture
def test_db():
    """Create a test database"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
        db_path = f.name

    db = Database(db_path)
    db.connect()
    db.create_schema()

    # Add some test data
    now = datetime.now()

    test_transcripts = [
        AudioTranscript(
            timestamp=now.isoformat(),
            source="microphone",
            text="We need to discuss the insurance policy for the new trucks",
            speaker="user",
        ),
        AudioTranscript(
            timestamp=now.isoformat(),
            source="microphone",
            text="The compliance requirements have changed recently",
            speaker="user",
        ),
        AudioTranscript(
            timestamp=now.isoformat(),
            source="vapi",
            text="This is a call from REMUS about scheduling",
            speaker="remus",
            call_id="test-call-123",
        ),
    ]

    for transcript in test_transcripts:
        db.save_audio_transcript(transcript)

    yield db

    db.close()
    if os.path.exists(db_path):
        os.remove(db_path)


def test_get_transcript_functionality(test_db):
    """Test get_transcript tool functionality"""
    # This simulates what the MCP tool would do
    transcripts = test_db.get_recent_transcripts(minutes=5)

    assert len(transcripts) >= 2
    assert any("insurance" in t["text"].lower() for t in transcripts)
    assert any("compliance" in t["text"].lower() for t in transcripts)


def test_search_audio_functionality(test_db):
    """Test search_audio tool functionality"""
    # Search for "insurance"
    results = test_db.search_audio_transcripts(query="insurance", days_back=7)

    assert len(results) == 1
    assert "insurance" in results[0]["text"].lower()
    assert results[0]["source"] == "microphone"

    # Search for "REMUS"
    results = test_db.search_audio_transcripts(query="REMUS", days_back=7)

    assert len(results) == 1
    assert results[0]["source"] == "vapi"
    assert results[0]["speaker"] == "remus"


def test_microphone_source_filter(test_db):
    """Test filtering by microphone source"""
    results = test_db.get_recent_transcripts(minutes=10, source="microphone")

    assert len(results) == 2
    assert all(r["source"] == "microphone" for r in results)


def test_vapi_source_filter(test_db):
    """Test filtering by VAPI source"""
    results = test_db.get_recent_transcripts(minutes=10, source="vapi")

    assert len(results) == 1
    assert results[0]["source"] == "vapi"
    assert results[0]["call_id"] == "test-call-123"


@pytest.mark.integration
def test_end_to_end_workflow():
    """Test complete workflow: capture -> save -> search

    This is a simulation test that doesn't require real audio.
    """
    # Create temporary database
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
        db_path = f.name

    try:
        # Initialize database
        db = Database(db_path)
        db.connect()
        db.create_schema()

        # Simulate transcription callback
        def on_transcript(transcript: AudioTranscript):
            db.save_audio_transcript(transcript)

        # Simulate some transcripts
        simulated_transcripts = [
            "I need to file an insurance claim",
            "Let's review the compliance checklist",
            "The truck maintenance is scheduled for next week",
        ]

        for text in simulated_transcripts:
            transcript = AudioTranscript(
                timestamp=datetime.now().isoformat(),
                source="microphone",
                text=text,
                speaker="user",
            )
            on_transcript(transcript)

        # Verify transcripts were saved
        recent = db.get_recent_transcripts(minutes=5)
        assert len(recent) == 3

        # Verify search works
        results = db.search_audio_transcripts(query="insurance", days_back=7)
        assert len(results) == 1
        assert "insurance" in results[0]["text"].lower()

        # Cleanup
        db.close()

    finally:
        if os.path.exists(db_path):
            os.remove(db_path)
