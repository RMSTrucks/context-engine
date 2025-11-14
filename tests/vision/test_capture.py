"""Unit tests for vision capture functionality"""

import pytest
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.storage.database import Database
from shared.models.screen_capture import ScreenCapture

# Import vision capture handling hyphenated directory names
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "mcp-servers" / "vision-capture"))
from capture import VisionCapture as VC
VisionCapture = VC


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def test_db(temp_dir):
    """Create test database"""
    db_path = Path(temp_dir) / "test.db"
    db = Database(str(db_path))
    db.connect()
    db.create_schema()
    yield db
    db.close()


@pytest.fixture
def vision_capture(test_db, temp_dir):
    """Create VisionCapture instance for testing"""
    screenshots_dir = Path(temp_dir) / "screenshots"
    return VisionCapture(
        db=test_db,
        screenshots_dir=str(screenshots_dir),
        save_images=True,
        image_quality=85
    )


def create_test_image(text: str, size: tuple = (800, 600)) -> Image.Image:
    """Create a test image with text for OCR testing

    Args:
        text: Text to render in image
        size: Image size (width, height)

    Returns:
        PIL Image with rendered text
    """
    # Create white background
    image = Image.new('RGB', size, color='white')
    draw = ImageDraw.Draw(image)

    # Draw text in black (large font for better OCR)
    try:
        # Try to use a common font
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
    except:
        # Fallback to default font
        font = ImageFont.load_default()

    # Center text
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    x = (size[0] - text_width) // 2
    y = (size[1] - text_height) // 2

    draw.text((x, y), text, fill='black', font=font)
    return image


class TestVisionCapture:
    """Test suite for VisionCapture class"""

    def test_initialization(self, vision_capture, temp_dir):
        """Test VisionCapture initialization"""
        assert vision_capture is not None
        assert vision_capture.save_images is True
        assert vision_capture.image_quality == 85
        assert vision_capture.screenshots_dir == Path(temp_dir) / "screenshots"

    def test_image_hashing(self, vision_capture):
        """Test image hash generation"""
        # Create two identical images
        img1 = create_test_image("Hello World")
        img2 = create_test_image("Hello World")

        # Hashes should be identical
        hash1 = vision_capture._hash_image(img1)
        hash2 = vision_capture._hash_image(img2)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 produces 64 hex chars

        # Different images should have different hashes
        img3 = create_test_image("Different Text")
        hash3 = vision_capture._hash_image(img3)
        assert hash1 != hash3

    def test_image_saving(self, vision_capture, temp_dir):
        """Test image saving functionality"""
        img = create_test_image("Test Save")
        timestamp = datetime.now().isoformat()

        image_path = vision_capture._save_image(img, timestamp)

        assert image_path is not None
        assert Path(image_path).exists()
        assert Path(image_path).suffix == ".jpg"

        # Verify saved image can be loaded
        saved_img = Image.open(image_path)
        assert saved_img.size == img.size

    def test_ocr_basic_text(self, vision_capture):
        """Test OCR on simple text"""
        img = create_test_image("HELLO WORLD")

        text, confidence = vision_capture._perform_ocr(img)

        # OCR should detect some text (may not be perfect)
        assert text is not None
        assert isinstance(text, str)
        assert confidence >= 0.0
        assert confidence <= 1.0

        # Simple text should have reasonable confidence
        # Note: OCR accuracy depends on tesseract installation
        # We're just checking it runs without error

    def test_ocr_empty_image(self, vision_capture):
        """Test OCR on empty image"""
        # Create blank white image
        img = Image.new('RGB', (800, 600), color='white')

        text, confidence = vision_capture._perform_ocr(img)

        # Should handle empty image gracefully
        assert isinstance(text, str)
        assert confidence >= 0.0

    def test_get_window_title(self, vision_capture):
        """Test window title retrieval"""
        # This is platform-dependent, so we just test it doesn't crash
        title = vision_capture.get_window_title()

        # Title could be None or a string
        assert title is None or isinstance(title, str)

    def test_capture_deduplication(self, vision_capture, test_db, monkeypatch):
        """Test that duplicate captures are detected"""
        # Create a mock image
        test_img = create_test_image("Duplicate Test")

        # Mock mss to return our test image
        class MockScreenShot:
            def __init__(self, img):
                self.width = img.width
                self.height = img.height
                self.rgb = img.tobytes()

        class MockMSS:
            def __init__(self, img):
                self.img = img
                self.monitors = [None, {"top": 0, "left": 0, "width": 800, "height": 600}]

            def grab(self, monitor):
                return MockScreenShot(self.img)

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        # Monkey-patch mss
        import capture as capture_module
        original_mss = capture_module.mss

        try:
            capture_module.mss.mss = lambda: MockMSS(test_img)

            # First capture
            capture1 = vision_capture.capture_screen(trigger_reason="test")
            assert capture1 is not None
            hash1 = capture1.image_hash

            # Second capture of same image should be deduplicated
            capture2 = vision_capture.capture_screen(trigger_reason="test")
            hash2 = capture2.image_hash

            assert hash1 == hash2
            # Should return existing capture
            assert capture2.timestamp == capture1.timestamp

        finally:
            # Restore original mss
            capture_module.mss = original_mss


class TestDatabase:
    """Test suite for database operations"""

    def test_schema_creation(self, test_db):
        """Test database schema creation"""
        # Schema should be created by fixture
        cursor = test_db.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='screen_captures'"
        )
        result = cursor.fetchone()
        assert result is not None

        # FTS5 table should exist
        cursor = test_db.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='screen_captures_fts'"
        )
        result = cursor.fetchone()
        assert result is not None

    def test_capture_storage(self, test_db):
        """Test storing and retrieving captures"""
        timestamp = datetime.now().isoformat()

        # Insert test capture
        with test_db.transaction() as cursor:
            cursor.execute(
                """
                INSERT INTO screen_captures
                (timestamp, window_title, ocr_text, ocr_confidence,
                 image_path, image_hash, trigger_reason, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    timestamp,
                    "Test Window",
                    "Test OCR Text",
                    0.95,
                    "/path/to/image.jpg",
                    "abc123",
                    "test",
                    None
                )
            )

        # Retrieve capture
        cursor = test_db.connection.execute(
            "SELECT * FROM screen_captures WHERE image_hash = ?",
            ("abc123",)
        )
        result = cursor.fetchone()

        assert result is not None
        assert result['window_title'] == "Test Window"
        assert result['ocr_text'] == "Test OCR Text"
        assert result['ocr_confidence'] == 0.95

    def test_full_text_search(self, test_db):
        """Test FTS5 full-text search"""
        timestamp = datetime.now().isoformat()

        # Insert test captures with different text
        captures = [
            ("python programming tutorial", "hash1"),
            ("javascript web development", "hash2"),
            ("python data science guide", "hash3"),
        ]

        for text, hash_val in captures:
            with test_db.transaction() as cursor:
                cursor.execute(
                    """
                    INSERT INTO screen_captures
                    (timestamp, ocr_text, image_hash, trigger_reason)
                    VALUES (?, ?, ?, ?)
                    """,
                    (timestamp, text, hash_val, "test")
                )

        # Search for "python"
        results = test_db.search_captures("python", limit=10)

        assert len(results) == 2
        # Results should contain python-related captures

    def test_cleanup_old_captures(self, test_db):
        """Test retention cleanup"""
        from datetime import timedelta

        # Insert old capture
        old_timestamp = (datetime.now() - timedelta(days=10)).isoformat()
        recent_timestamp = datetime.now().isoformat()

        with test_db.transaction() as cursor:
            cursor.execute(
                """
                INSERT INTO screen_captures
                (timestamp, ocr_text, image_hash, trigger_reason)
                VALUES (?, ?, ?, ?)
                """,
                (old_timestamp, "old capture", "old_hash", "test")
            )
            cursor.execute(
                """
                INSERT INTO screen_captures
                (timestamp, ocr_text, image_hash, trigger_reason)
                VALUES (?, ?, ?, ?)
                """,
                (recent_timestamp, "recent capture", "recent_hash", "test")
            )

        # Cleanup captures older than 7 days
        deleted = test_db.cleanup_old_captures(retention_days=7)

        assert deleted == 1

        # Verify only recent capture remains
        cursor = test_db.connection.execute("SELECT COUNT(*) FROM screen_captures")
        count = cursor.fetchone()[0]
        assert count == 1

    def test_duplicate_hash_prevention(self, test_db):
        """Test that duplicate hashes are prevented"""
        timestamp = datetime.now().isoformat()

        # Insert first capture
        with test_db.transaction() as cursor:
            cursor.execute(
                """
                INSERT INTO screen_captures
                (timestamp, ocr_text, image_hash, trigger_reason)
                VALUES (?, ?, ?, ?)
                """,
                (timestamp, "test", "duplicate_hash", "test")
            )

        # Try to insert duplicate hash - should fail
        with pytest.raises(Exception):
            with test_db.transaction() as cursor:
                cursor.execute(
                    """
                    INSERT INTO screen_captures
                    (timestamp, ocr_text, image_hash, trigger_reason)
                    VALUES (?, ?, ?, ?)
                    """,
                    (timestamp, "test2", "duplicate_hash", "test")
                )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
