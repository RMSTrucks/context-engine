"""Unit tests for transcription service

Note: These tests require audio hardware and whisper models.
They are marked as integration tests and can be skipped in CI.
"""
import pytest
import time
from datetime import datetime

from shared.models.audio_transcript import AudioTranscript


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture
def transcription_service():
    """Create transcription service for testing"""
    try:
        from mcp_servers.audio_capture.transcription_service import TranscriptionService

        service = TranscriptionService(
            model_size="tiny.en",  # Use smallest model for testing
            language="en",
        )
        yield service
        service.cleanup()
    except ImportError:
        pytest.skip("Audio dependencies not installed")


def test_service_initialization(transcription_service):
    """Test service can be initialized"""
    assert transcription_service is not None
    assert transcription_service.model_size == "tiny.en"
    assert transcription_service.language == "en"


def test_start_stop_listening(transcription_service):
    """Test starting and stopping transcription"""
    transcripts = []

    def callback(transcript: AudioTranscript):
        transcripts.append(transcript)

    # Start listening
    transcription_service.start_listening(callback)
    assert transcription_service.is_listening

    # Wait a bit
    time.sleep(2)

    # Stop listening
    transcription_service.stop_listening()
    assert not transcription_service.is_listening


def test_vad_filtering():
    """Test VAD filters silence correctly"""
    # This test would require generating audio data
    # For now, we'll just verify the VAD is initialized
    try:
        from mcp_servers.audio_capture.transcription_service import TranscriptionService

        service = TranscriptionService()
        service._init_components()

        assert service.vad is not None
        assert service.vad_mode == 3

        service.cleanup()
    except ImportError:
        pytest.skip("Audio dependencies not installed")


@pytest.mark.manual
def test_real_transcription(transcription_service):
    """Test real audio transcription (manual test)

    This test requires:
    1. A working microphone
    2. Manual speech input
    3. Run with: pytest -m manual

    To run:
        pytest tests/audio/test_transcription_service.py -m manual -v
    """
    transcripts = []

    def callback(transcript: AudioTranscript):
        print(f"\nTranscribed: {transcript.text}")
        transcripts.append(transcript)

    print("\n" + "=" * 60)
    print("MANUAL TEST: Real Audio Transcription")
    print("=" * 60)
    print("\nInstructions:")
    print("1. Speak into your microphone")
    print("2. Say a few sentences")
    print("3. Test will run for 30 seconds")
    print("\nStarting in 3 seconds...\n")

    time.sleep(3)

    # Start listening
    transcription_service.start_listening(callback)
    print("Listening... (speak now)")

    # Listen for 30 seconds
    time.sleep(30)

    # Stop listening
    transcription_service.stop_listening()
    print("\nStopped listening")

    # Check results
    print(f"\nCaptured {len(transcripts)} transcript(s)")
    for i, t in enumerate(transcripts, 1):
        print(f"\n{i}. {t.text}")

    assert len(transcripts) > 0, "No transcripts captured - check microphone"
