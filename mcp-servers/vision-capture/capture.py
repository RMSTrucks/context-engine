"""Screen capture and OCR functionality

This module provides core vision capture capabilities including:
- Full screen capture with OCR
- Region-based capture with OCR
- Window title extraction
- Image hashing for deduplication
"""

import io
import logging
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dataclasses import asdict

import mss
import pytesseract
from PIL import Image
import psutil

from shared.models.screen_capture import ScreenCapture
from shared.storage.database import Database

logger = logging.getLogger(__name__)


class VisionCapture:
    """Handles screen capture and OCR operations"""

    def __init__(
        self,
        db: Database,
        screenshots_dir: str = "screenshots",
        save_images: bool = True,
        image_quality: int = 85
    ):
        """Initialize vision capture

        Args:
            db: Database instance for storing captures
            screenshots_dir: Directory to save screenshot images
            save_images: Whether to save screenshot files
            image_quality: JPEG quality (1-100)
        """
        self.db = db
        self.screenshots_dir = Path(screenshots_dir)
        self.save_images = save_images
        self.image_quality = image_quality

        if save_images:
            self.screenshots_dir.mkdir(parents=True, exist_ok=True)

        logger.info("VisionCapture initialized")

    def _hash_image(self, image: Image.Image) -> str:
        """Generate hash of image for deduplication

        Args:
            image: PIL Image object

        Returns:
            SHA256 hash of image
        """
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return hashlib.sha256(img_bytes.read()).hexdigest()

    def _save_image(self, image: Image.Image, timestamp: str) -> Optional[str]:
        """Save screenshot to disk

        Args:
            image: PIL Image to save
            timestamp: ISO timestamp for filename

        Returns:
            Path to saved image or None
        """
        if not self.save_images:
            return None

        try:
            # Create filename from timestamp
            safe_timestamp = timestamp.replace(":", "-").replace(".", "-")
            filename = f"screenshot_{safe_timestamp}.jpg"
            filepath = self.screenshots_dir / filename

            # Save as JPEG to save space
            image.save(filepath, "JPEG", quality=self.image_quality, optimize=True)
            logger.debug(f"Saved screenshot: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Failed to save image: {e}")
            return None

    def _perform_ocr(self, image: Image.Image) -> Tuple[str, float]:
        """Perform OCR on image

        Args:
            image: PIL Image to process

        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        try:
            # Get OCR data with confidence scores
            ocr_data = pytesseract.image_to_data(
                image,
                output_type=pytesseract.Output.DICT
            )

            # Extract text
            text = pytesseract.image_to_string(image).strip()

            # Calculate average confidence (excluding -1 values which indicate no text)
            confidences = [
                conf for conf in ocr_data['conf']
                if conf != -1
            ]

            if confidences:
                avg_confidence = sum(confidences) / len(confidences) / 100.0  # Convert to 0-1 scale
            else:
                avg_confidence = 0.0

            logger.debug(f"OCR completed: {len(text)} chars, confidence: {avg_confidence:.2f}")
            return text, avg_confidence

        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return "", 0.0

    def get_window_title(self) -> Optional[str]:
        """Get title of currently active window

        Returns:
            Window title or None if unavailable
        """
        try:
            # Try to get active window using psutil
            # This is platform-dependent and may need adjustment
            import platform

            if platform.system() == "Windows":
                import ctypes
                user32 = ctypes.windll.user32
                h_wnd = user32.GetForegroundWindow()
                length = user32.GetWindowTextLengthW(h_wnd)
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(h_wnd, buff, length + 1)
                return buff.value if buff.value else None

            elif platform.system() == "Linux":
                # Try using xdotool if available
                import subprocess
                try:
                    result = subprocess.run(
                        ["xdotool", "getactivewindow", "getwindowname"],
                        capture_output=True,
                        text=True,
                        timeout=1
                    )
                    return result.stdout.strip() if result.returncode == 0 else None
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    return None

            elif platform.system() == "Darwin":  # macOS
                # Try using AppleScript
                import subprocess
                try:
                    script = 'tell application "System Events" to get name of first application process whose frontmost is true'
                    result = subprocess.run(
                        ["osascript", "-e", script],
                        capture_output=True,
                        text=True,
                        timeout=1
                    )
                    return result.stdout.strip() if result.returncode == 0 else None
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    return None

            return None

        except Exception as e:
            logger.warning(f"Failed to get window title: {e}")
            return None

    def capture_screen(
        self,
        trigger_reason: str = "manual",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ScreenCapture:
        """Capture full screen with OCR

        Args:
            trigger_reason: Reason for capture (manual, timer, voice_command, etc.)
            metadata: Additional metadata to store

        Returns:
            ScreenCapture object with results
        """
        timestamp = datetime.now().isoformat()
        logger.info(f"Capturing full screen at {timestamp}")

        try:
            # Capture screen using mss (fast cross-platform)
            with mss.mss() as sct:
                # Capture primary monitor
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)

                # Convert to PIL Image
                image = Image.frombytes(
                    "RGB",
                    (screenshot.width, screenshot.height),
                    screenshot.rgb
                )

            # Generate hash for deduplication
            image_hash = self._hash_image(image)

            # Check for duplicate
            existing = self.db.get_capture_by_hash(image_hash)
            if existing:
                logger.info(f"Duplicate capture detected (hash: {image_hash[:8]}...)")
                # Return existing capture
                return ScreenCapture(**existing)

            # Get window title
            window_title = self.get_window_title()

            # Perform OCR
            ocr_text, ocr_confidence = self._perform_ocr(image)

            # Save image
            image_path = self._save_image(image, timestamp)

            # Create capture object
            capture = ScreenCapture(
                timestamp=timestamp,
                window_title=window_title,
                ocr_text=ocr_text,
                ocr_confidence=ocr_confidence,
                image_path=image_path,
                image_hash=image_hash,
                trigger_reason=trigger_reason,
                metadata=metadata
            )

            # Store in database
            self._save_to_db(capture)

            logger.info(f"Screen capture completed: {len(ocr_text)} chars, confidence: {ocr_confidence:.2f}")
            return capture

        except Exception as e:
            logger.error(f"Screen capture failed: {e}")
            raise

    def capture_region(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        trigger_reason: str = "manual",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ScreenCapture:
        """Capture specific region with OCR

        Args:
            x: X coordinate of top-left corner
            y: Y coordinate of top-left corner
            width: Width of region
            height: Height of region
            trigger_reason: Reason for capture
            metadata: Additional metadata

        Returns:
            ScreenCapture object with results
        """
        timestamp = datetime.now().isoformat()
        logger.info(f"Capturing region ({x}, {y}, {width}, {height}) at {timestamp}")

        try:
            # Capture region using mss
            with mss.mss() as sct:
                monitor = {
                    "top": y,
                    "left": x,
                    "width": width,
                    "height": height
                }
                screenshot = sct.grab(monitor)

                # Convert to PIL Image
                image = Image.frombytes(
                    "RGB",
                    (screenshot.width, screenshot.height),
                    screenshot.rgb
                )

            # Generate hash
            image_hash = self._hash_image(image)

            # Check for duplicate
            existing = self.db.get_capture_by_hash(image_hash)
            if existing:
                logger.info(f"Duplicate region capture detected")
                return ScreenCapture(**existing)

            # Get window title
            window_title = self.get_window_title()

            # Perform OCR
            ocr_text, ocr_confidence = self._perform_ocr(image)

            # Save image
            image_path = self._save_image(image, timestamp)

            # Add region info to metadata
            region_metadata = metadata or {}
            region_metadata.update({
                "region": {"x": x, "y": y, "width": width, "height": height}
            })

            # Create capture object
            capture = ScreenCapture(
                timestamp=timestamp,
                window_title=window_title,
                ocr_text=ocr_text,
                ocr_confidence=ocr_confidence,
                image_path=image_path,
                image_hash=image_hash,
                trigger_reason=trigger_reason,
                metadata=region_metadata
            )

            # Store in database
            self._save_to_db(capture)

            logger.info(f"Region capture completed: {len(ocr_text)} chars")
            return capture

        except Exception as e:
            logger.error(f"Region capture failed: {e}")
            raise

    def _save_to_db(self, capture: ScreenCapture) -> None:
        """Save capture to database

        Args:
            capture: ScreenCapture object to save
        """
        try:
            with self.db.transaction() as cursor:
                cursor.execute(
                    """
                    INSERT INTO screen_captures
                    (timestamp, window_title, ocr_text, ocr_confidence,
                     image_path, image_hash, trigger_reason, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        capture.timestamp,
                        capture.window_title,
                        capture.ocr_text,
                        capture.ocr_confidence,
                        capture.image_path,
                        capture.image_hash,
                        capture.trigger_reason,
                        json.dumps(capture.metadata) if capture.metadata else None
                    )
                )
            logger.debug("Capture saved to database")
        except Exception as e:
            logger.error(f"Failed to save capture to database: {e}")
            raise

    def search_captures(self, query: str, limit: int = 10) -> list:
        """Search captured text

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching captures
        """
        return self.db.search_captures(query, limit)


__all__ = ["VisionCapture"]
