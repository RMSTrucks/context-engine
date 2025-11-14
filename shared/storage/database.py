"""SQLite database interface

This module provides the main database interface for Context Engine.
Implementation will be added across different phases.
"""
import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class Database:
    """SQLite database with FTS5 support

    This class provides:
    - Connection management
    - Schema creation and migration
    - Query helpers
    - Full-text search via FTS5
    - Data retention management
    """

    def __init__(self, db_path: str = "context.db"):
        """Initialize database connection

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.connection: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        """Connect to database and enable foreign keys"""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                isolation_level=None  # autocommit mode
            )
            self.connection.row_factory = sqlite3.Row
            # Enable foreign keys
            self.connection.execute("PRAGMA foreign_keys = ON")
            # Enable WAL mode for better concurrency
            self.connection.execute("PRAGMA journal_mode = WAL")
            logger.info(f"Connected to database: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def close(self) -> None:
        """Close database connection"""
        if self.connection:
            try:
                self.connection.close()
                self.connection = None
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing database: {e}")

    @contextmanager
    def transaction(self):
        """Context manager for database transactions"""
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()
        try:
            cursor.execute("BEGIN")
            yield cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Transaction rolled back: {e}")
            raise
        finally:
            cursor.close()

    def create_schema(self) -> None:
        """Create database schema for Phase 1 (Vision Capture)"""
        if not self.connection:
            self.connect()

        schema = """
        -- Screen captures table
        CREATE TABLE IF NOT EXISTS screen_captures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            window_title TEXT,
            ocr_text TEXT,
            ocr_confidence REAL,
            image_path TEXT,
            image_hash TEXT UNIQUE,
            trigger_reason TEXT,
            metadata TEXT,  -- JSON string
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(image_hash)
        );

        -- FTS5 full-text search index for OCR text
        CREATE VIRTUAL TABLE IF NOT EXISTS screen_captures_fts USING fts5(
            ocr_text,
            window_title,
            trigger_reason,
            content='screen_captures',
            content_rowid='id'
        );

        -- Triggers to keep FTS5 index in sync
        CREATE TRIGGER IF NOT EXISTS screen_captures_ai AFTER INSERT ON screen_captures BEGIN
            INSERT INTO screen_captures_fts(rowid, ocr_text, window_title, trigger_reason)
            VALUES (new.id, new.ocr_text, new.window_title, new.trigger_reason);
        END;

        CREATE TRIGGER IF NOT EXISTS screen_captures_ad AFTER DELETE ON screen_captures BEGIN
            DELETE FROM screen_captures_fts WHERE rowid = old.id;
        END;

        CREATE TRIGGER IF NOT EXISTS screen_captures_au AFTER UPDATE ON screen_captures BEGIN
            UPDATE screen_captures_fts
            SET ocr_text = new.ocr_text,
                window_title = new.window_title,
                trigger_reason = new.trigger_reason
            WHERE rowid = new.id;
        END;

        -- Index for fast retention cleanup
        CREATE INDEX IF NOT EXISTS idx_screen_captures_timestamp
        ON screen_captures(timestamp);

        -- Index for deduplication
        CREATE INDEX IF NOT EXISTS idx_screen_captures_hash
        ON screen_captures(image_hash);
        """

        try:
            self.connection.executescript(schema)
            logger.info("Database schema created successfully")
        except Exception as e:
            logger.error(f"Failed to create schema: {e}")
            raise

    def cleanup_old_captures(self, retention_days: int = 7) -> int:
        """Delete captures older than retention period

        Args:
            retention_days: Number of days to retain captures

        Returns:
            Number of records deleted
        """
        if not self.connection:
            self.connect()

        cutoff_date = (datetime.now() - timedelta(days=retention_days)).isoformat()

        try:
            cursor = self.connection.execute(
                "DELETE FROM screen_captures WHERE timestamp < ?",
                (cutoff_date,)
            )
            deleted_count = cursor.rowcount
            logger.info(f"Cleaned up {deleted_count} old captures (older than {retention_days} days)")
            return deleted_count
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            raise

    def search_captures(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Full-text search across screen captures

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching captures with metadata
        """
        if not self.connection:
            self.connect()

        try:
            cursor = self.connection.execute(
                """
                SELECT sc.*, rank
                FROM screen_captures sc
                JOIN screen_captures_fts fts ON sc.id = fts.rowid
                WHERE screen_captures_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (query, limit)
            )

            results = []
            for row in cursor.fetchall():
                results.append(dict(row))

            logger.info(f"Found {len(results)} results for query: {query}")
            return results
        except Exception as e:
            logger.error(f"Search error: {e}")
            raise

    def get_capture_by_hash(self, image_hash: str) -> Optional[Dict[str, Any]]:
        """Check if capture with this hash already exists

        Args:
            image_hash: Hash of the image

        Returns:
            Existing capture record or None
        """
        if not self.connection:
            self.connect()

        try:
            cursor = self.connection.execute(
                "SELECT * FROM screen_captures WHERE image_hash = ?",
                (image_hash,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error checking for duplicate: {e}")
            return None

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


__all__ = ["Database"]
