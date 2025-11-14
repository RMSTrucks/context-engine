#!/usr/bin/env python3
"""Test script for Vision Capture functionality

This script demonstrates basic usage of the Vision Capture system.
Run this to verify your installation and test core functionality.
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp-servers" / "vision-capture"))

from shared.storage.database import Database
from shared.utils.config import load_config
from capture import VisionCapture


def test_database():
    """Test database initialization"""
    print("=" * 60)
    print("Testing Database Initialization")
    print("=" * 60)

    db = Database("test_context.db")
    db.connect()
    db.create_schema()

    print("✓ Database connected")
    print("✓ Schema created")

    # Test cleanup
    deleted = db.cleanup_old_captures(retention_days=7)
    print(f"✓ Cleanup: {deleted} old captures removed")

    return db


def test_window_title(vision):
    """Test window title detection"""
    print("\n" + "=" * 60)
    print("Testing Window Title Detection")
    print("=" * 60)

    title = vision.get_window_title()
    if title:
        print(f"✓ Active window: {title}")
    else:
        print("⚠ Could not detect window title (this is platform-dependent)")


def test_screen_capture(vision):
    """Test full screen capture with OCR"""
    print("\n" + "=" * 60)
    print("Testing Full Screen Capture")
    print("=" * 60)

    print("Capturing screen in 3 seconds...")
    print("Please make sure you have some text visible on screen!")
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)

    start_time = time.time()
    capture = vision.capture_screen(trigger_reason="test")
    elapsed = time.time() - start_time

    print(f"\n✓ Capture completed in {elapsed:.2f}s")
    print(f"  Timestamp: {capture.timestamp}")
    print(f"  Window: {capture.window_title or 'Unknown'}")
    print(f"  Confidence: {capture.ocr_confidence:.2%}")
    print(f"  Text length: {len(capture.ocr_text or '')} characters")
    print(f"  Image saved: {capture.image_path}")

    if capture.ocr_text:
        print(f"\n  First 200 chars of extracted text:")
        print(f"  {'-' * 58}")
        snippet = capture.ocr_text[:200]
        for line in snippet.split('\n'):
            print(f"  {line}")
        if len(capture.ocr_text) > 200:
            print(f"  ...")
    else:
        print("  ⚠ No text detected - ensure text is visible on screen")

    # Performance check
    if elapsed < 2.5:
        print(f"\n✓ Performance: {elapsed:.2f}s (target: <2.5s)")
    else:
        print(f"\n⚠ Performance: {elapsed:.2f}s (slower than target 2.5s)")

    return capture


def test_region_capture(vision):
    """Test region capture"""
    print("\n" + "=" * 60)
    print("Testing Region Capture")
    print("=" * 60)

    # Capture center portion of screen (assuming 1920x1080 or similar)
    print("Capturing center region (800x600) in 2 seconds...")
    time.sleep(2)

    start_time = time.time()
    capture = vision.capture_region(
        x=560,   # Center of 1920
        y=240,   # Center of 1080
        width=800,
        height=600,
        trigger_reason="test"
    )
    elapsed = time.time() - start_time

    print(f"\n✓ Region capture completed in {elapsed:.2f}s")
    print(f"  Region: (560, 240) - 800x600")
    print(f"  Confidence: {capture.ocr_confidence:.2%}")
    print(f"  Text length: {len(capture.ocr_text or '')} characters")


def test_search(vision):
    """Test search functionality"""
    print("\n" + "=" * 60)
    print("Testing Search Functionality")
    print("=" * 60)

    # Search for common words that might be in captures
    test_queries = ["the", "test", "python", "capture"]

    for query in test_queries:
        results = vision.search_captures(query, limit=5)
        if results:
            print(f"\n✓ Query '{query}': Found {len(results)} result(s)")
            for i, result in enumerate(results[:2], 1):
                text = result.get('ocr_text', '')[:100]
                print(f"  {i}. {result.get('timestamp')}: {text}...")
            break
    else:
        print("⚠ No search results found (database may be empty)")


def test_deduplication(vision):
    """Test deduplication"""
    print("\n" + "=" * 60)
    print("Testing Deduplication")
    print("=" * 60)

    print("Capturing screen twice (should detect duplicate)...")
    time.sleep(1)

    capture1 = vision.capture_screen(trigger_reason="dedup_test_1")
    hash1 = capture1.image_hash

    print("First capture complete, capturing again...")
    time.sleep(0.5)

    capture2 = vision.capture_screen(trigger_reason="dedup_test_2")
    hash2 = capture2.image_hash

    if hash1 == hash2:
        print(f"✓ Deduplication working: Same hash detected")
        print(f"  Hash: {hash1[:16]}...")
    else:
        print(f"⚠ Different hashes (screen content may have changed)")
        print(f"  Hash 1: {hash1[:16]}...")
        print(f"  Hash 2: {hash2[:16]}...")


def print_summary():
    """Print test summary"""
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print("\nIf all tests passed (✓), your Vision Capture system is working!")
    print("\nNext steps:")
    print("1. Start the MCP server: python -m mcp_servers.vision_capture.server")
    print("2. Configure Claude Desktop/Code to use the server")
    print("3. Try: 'Look at my screen' in Claude")
    print("\nFor issues, check:")
    print("- Tesseract installation: tesseract --version")
    print("- Logs in: logs/vision-capture.log")
    print("- Documentation: mcp-servers/vision-capture/README.md")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Vision Capture Test Suite")
    print("=" * 60)
    print("\nThis will test all core functionality of the Vision Capture system.")
    print("Press Ctrl+C to cancel.\n")

    try:
        # Load config
        try:
            config = load_config()
            print("✓ Configuration loaded")
        except Exception as e:
            print(f"⚠ Could not load config: {e}")
            print("Using default configuration")
            config = {
                'vision': {
                    'save_images': True,
                    'image_quality': 85,
                    'retention_days': 7
                }
            }

        # Initialize database
        db = test_database()

        # Initialize vision capture
        vision_config = config.get('vision', {})
        vision = VisionCapture(
            db=db,
            screenshots_dir="test_screenshots",
            save_images=vision_config.get('save_images', True),
            image_quality=vision_config.get('image_quality', 85)
        )

        # Run tests
        test_window_title(vision)
        test_screen_capture(vision)
        test_region_capture(vision)
        test_search(vision)
        test_deduplication(vision)

        # Summary
        print_summary()

        # Cleanup
        db.close()
        print("\n✓ Database closed")

    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
