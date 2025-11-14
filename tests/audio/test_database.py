"""Unit tests for audio transcript database operations"""
import os
import sqlite3
import tempfile
from datetime import datetime, timedelta

import pytest

from shared.storage.database import Database
from shared.models.audio_transcript import AudioTranscript


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
        db_path = f.name

    db = Database(db_path)
    db.connect()
    db.create_schema()

    yield db

    db.close()
    if os.path.exists(db_path):
        os.remove(db_path)


def test_database_creation(temp_db):
    """Test database schema creation"""
    # Check that tables exist
    cursor = temp_db.connection.cursor()

    cursor.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='audio_transcripts'
    """
    )
    assert cursor.fetchone() is not None

    cursor.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='audio_transcripts_fts'
    """
    )
    assert cursor.fetchone() is not None


def test_save_audio_transcript(temp_db):
    """Test saving audio transcript"""
    transcript = AudioTranscript(
        timestamp=datetime.now().isoformat(),
        source="microphone",
        text="This is a test transcript",
        speaker="user",
        confidence=0.95,
    )

    row_id = temp_db.save_audio_transcript(transcript)
    assert row_id > 0


def test_get_recent_transcripts(temp_db):
    """Test retrieving recent transcripts"""
    # Add some test transcripts
    now = datetime.now()

    for i in range(5):
        transcript = AudioTranscript(
            timestamp=(now - timedelta(minutes=i)).isoformat(),
            source="microphone",
            text=f"Test transcript {i}",
            speaker="user",
        )
        temp_db.save_audio_transcript(transcript)

    # Get recent transcripts
    results = temp_db.get_recent_transcripts(minutes=10)
    assert len(results) == 5

    # Check ordering (should be chronological)
    assert results[0]["text"] == "Test transcript 4"
    assert results[-1]["text"] == "Test transcript 0"


def test_get_recent_transcripts_with_source_filter(temp_db):
    """Test retrieving recent transcripts with source filter"""
    now = datetime.now()

    # Add microphone transcripts
    for i in range(3):
        transcript = AudioTranscript(
            timestamp=now.isoformat(),
            source="microphone",
            text=f"Microphone transcript {i}",
            speaker="user",
        )
        temp_db.save_audio_transcript(transcript)

    # Add VAPI transcripts
    for i in range(2):
        transcript = AudioTranscript(
            timestamp=now.isoformat(),
            source="vapi",
            text=f"VAPI transcript {i}",
            speaker="remus",
        )
        temp_db.save_audio_transcript(transcript)

    # Get only microphone transcripts
    results = temp_db.get_recent_transcripts(minutes=10, source="microphone")
    assert len(results) == 3
    assert all(r["source"] == "microphone" for r in results)

    # Get only VAPI transcripts
    results = temp_db.get_recent_transcripts(minutes=10, source="vapi")
    assert len(results) == 2
    assert all(r["source"] == "vapi" for r in results)


def test_search_audio_transcripts(temp_db):
    """Test full-text search of transcripts"""
    now = datetime.now()

    # Add test transcripts
    transcripts = [
        "I need to discuss the insurance policy",
        "Let's talk about compliance requirements",
        "The insurance claim was approved",
        "We need better compliance training",
    ]

    for text in transcripts:
        transcript = AudioTranscript(
            timestamp=now.isoformat(),
            source="microphone",
            text=text,
            speaker="user",
        )
        temp_db.save_audio_transcript(transcript)

    # Search for "insurance"
    results = temp_db.search_audio_transcripts(query="insurance", days_back=7)
    assert len(results) == 2
    assert all("insurance" in r["text"].lower() for r in results)

    # Search for "compliance"
    results = temp_db.search_audio_transcripts(query="compliance", days_back=7)
    assert len(results) == 2
    assert all("compliance" in r["text"].lower() for r in results)


def test_cleanup_old_transcripts(temp_db):
    """Test cleanup of old transcripts"""
    now = datetime.now()

    # Add old transcripts
    for i in range(3):
        transcript = AudioTranscript(
            timestamp=(now - timedelta(days=100 + i)).isoformat(),
            source="microphone",
            text=f"Old transcript {i}",
            speaker="user",
        )
        temp_db.save_audio_transcript(transcript)

    # Add recent transcripts
    for i in range(3):
        transcript = AudioTranscript(
            timestamp=(now - timedelta(days=i)).isoformat(),
            source="microphone",
            text=f"Recent transcript {i}",
            speaker="user",
        )
        temp_db.save_audio_transcript(transcript)

    # Add old VAPI transcript (should be kept)
    vapi_transcript = AudioTranscript(
        timestamp=(now - timedelta(days=100)).isoformat(),
        source="vapi",
        text="Old VAPI transcript",
        speaker="remus",
        call_id="test-call-123",
    )
    temp_db.save_audio_transcript(vapi_transcript)

    # Cleanup old transcripts (90 day retention)
    temp_db.cleanup_old_transcripts(retention_days=90)

    # Check that old microphone transcripts were deleted
    results = temp_db.get_recent_transcripts(minutes=1000000)  # Get all
    microphone_transcripts = [r for r in results if r["source"] == "microphone"]
    assert len(microphone_transcripts) == 3  # Only recent ones remain

    # Check that VAPI transcript was kept
    vapi_transcripts = [r for r in results if r["source"] == "vapi"]
    assert len(vapi_transcripts) == 1
    assert vapi_transcripts[0]["text"] == "Old VAPI transcript"


def test_audio_transcript_model():
    """Test AudioTranscript data model"""
    transcript = AudioTranscript(
        timestamp="2025-11-14T12:00:00",
        source="microphone",
        text="Test transcript",
        speaker="user",
        confidence=0.95,
        metadata={"key": "value"},
    )

    # Test to_dict
    data = transcript.to_dict()
    assert data["text"] == "Test transcript"
    assert data["speaker"] == "user"
    assert data["metadata"]["key"] == "value"

    # Test from_dict
    transcript2 = AudioTranscript.from_dict(data)
    assert transcript2.text == transcript.text
    assert transcript2.speaker == transcript.speaker
    assert transcript2.metadata == transcript.metadata
