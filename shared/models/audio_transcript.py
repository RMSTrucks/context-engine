"""Audio transcript data model

This module defines the data model for audio transcription.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class AudioTranscript:
    """Audio transcript with metadata

    Attributes:
        timestamp: ISO 8601 timestamp
        source: Source of audio ('microphone', 'vapi', 'system')
        text: Transcribed text
        speaker: Speaker identifier ('user', 'remus', 'genesis', 'unknown')
        confidence: Transcription confidence score (0.0-1.0)
        audio_file: Path to original audio file (optional)
        call_id: VAPI call ID if from VAPI (optional)
        metadata: Additional metadata
    """

    timestamp: str
    source: str  # 'microphone', 'vapi', 'system'
    text: str
    speaker: str = "unknown"  # 'user', 'remus', 'genesis', 'unknown'
    confidence: Optional[float] = None
    audio_file: Optional[str] = None
    call_id: Optional[str] = None
    metadata: Optional[dict] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage"""
        return {
            "timestamp": self.timestamp,
            "source": self.source,
            "speaker": self.speaker,
            "text": self.text,
            "confidence": self.confidence,
            "audio_file": self.audio_file,
            "call_id": self.call_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AudioTranscript":
        """Create from dictionary"""
        return cls(
            timestamp=data["timestamp"],
            source=data["source"],
            text=data["text"],
            speaker=data.get("speaker", "unknown"),
            confidence=data.get("confidence"),
            audio_file=data.get("audio_file"),
            call_id=data.get("call_id"),
            metadata=data.get("metadata", {}),
        )


__all__ = ["AudioTranscript"]
