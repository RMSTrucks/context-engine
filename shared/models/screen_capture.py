"""Screen capture data model

This module defines the data model for vision capture.
To be implemented in Phase 1.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ScreenCapture:
    """Screen capture with OCR data

    Attributes:
        timestamp: ISO 8601 timestamp
        window_title: Active window title
        ocr_text: Extracted text from OCR
        ocr_confidence: OCR confidence score (0.0-1.0)
        image_path: Path to saved screenshot
        image_hash: Hash of image for deduplication
        trigger_reason: Why capture was triggered
        metadata: Additional metadata
    """
    timestamp: str
    window_title: Optional[str] = None
    ocr_text: Optional[str] = None
    ocr_confidence: Optional[float] = None
    image_path: Optional[str] = None
    image_hash: Optional[str] = None
    trigger_reason: Optional[str] = None
    metadata: Optional[dict] = None


__all__ = ["ScreenCapture"]
