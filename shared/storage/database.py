"""SQLite database interface

This module provides the main database interface for Context Engine.
Implementation will be added across different phases.
"""
import sqlite3
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from contextlib import contextmanager

from ..models.audio_transcript import AudioTranscript

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
        """Create database schema for all phases"""
        if not self.connection:
            self.connect()

        # Phase 1: Vision Capture Schema
        vision_schema = """
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
            self.connection.executescript(vision_schema)
            logger.info("Vision capture schema created successfully")
        except Exception as e:
            logger.error(f"Failed to create vision schema: {e}")
            raise

        # Phase 2: Audio Capture Schema
        cursor = self.connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS audio_transcripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                source TEXT NOT NULL,
                speaker TEXT,
                text TEXT NOT NULL,
                confidence REAL,
                audio_file TEXT,
                call_id TEXT,
                metadata TEXT
            )
        """
        )

        # Create FTS5 full-text search index for audio transcripts
        cursor.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS audio_transcripts_fts
            USING fts5(
                text,
                content=audio_transcripts,
                content_rowid=id
            )
        """
        )

        # Create triggers to keep FTS5 index in sync
        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS audio_transcripts_ai
            AFTER INSERT ON audio_transcripts BEGIN
                INSERT INTO audio_transcripts_fts(rowid, text)
                VALUES (new.id, new.text);
            END
        """
        )

        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS audio_transcripts_ad
            AFTER DELETE ON audio_transcripts BEGIN
                INSERT INTO audio_transcripts_fts(audio_transcripts_fts, rowid, text)
                VALUES('delete', old.id, old.text);
            END
        """
        )

        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS audio_transcripts_au
            AFTER UPDATE ON audio_transcripts BEGIN
                INSERT INTO audio_transcripts_fts(audio_transcripts_fts, rowid, text)
                VALUES('delete', old.id, old.text);
                INSERT INTO audio_transcripts_fts(rowid, text)
                VALUES (new.id, new.text);
            END
        """
        )

        # Create indexes for common queries
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_audio_timestamp
            ON audio_transcripts(timestamp)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_audio_source
            ON audio_transcripts(source)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_audio_call_id
            ON audio_transcripts(call_id)
        """
        )

        self.connection.commit()
        logger.info("Audio capture schema created successfully")

    # Phase 1: Vision Capture Methods

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


    # Phase 2: Audio Capture Methods

    def save_audio_transcript(self, transcript: AudioTranscript) -> int:
        """Save audio transcript to database

        Args:
            transcript: AudioTranscript object to save

        Returns:
            Row ID of inserted transcript
        """
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO audio_transcripts
            (timestamp, source, speaker, text, confidence, audio_file, call_id, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                transcript.timestamp,
                transcript.source,
                transcript.speaker,
                transcript.text,
                transcript.confidence,
                transcript.audio_file,
                transcript.call_id,
                json.dumps(transcript.metadata) if transcript.metadata else None,
            ),
        )
        self.connection.commit()
        return cursor.lastrowid

    def get_recent_transcripts(self, minutes: int = 5, source: Optional[str] = None) -> List[Dict]:
        """Get recent transcripts

        Args:
            minutes: Number of minutes to look back
            source: Optional filter by source ('microphone', 'vapi', 'system')

        Returns:
            List of transcript dictionaries
        """
        if not self.connection:
            self.connect()

        cutoff_time = (datetime.now() - timedelta(minutes=minutes)).isoformat()

        query = """
            SELECT id, timestamp, source, speaker, text, confidence,
                   audio_file, call_id, metadata
            FROM audio_transcripts
            WHERE timestamp >= ?
        """
        params = [cutoff_time]

        if source:
            query += " AND source = ?"
            params.append(source)

        query += " ORDER BY timestamp ASC"

        cursor = self.connection.cursor()
        cursor.execute(query, params)

        results = []
        for row in cursor.fetchall():
            result = dict(row)
            if result["metadata"]:
                result["metadata"] = json.loads(result["metadata"])
            results.append(result)

        return results

    def search_audio_transcripts(
        self, query: str, days_back: int = 7, limit: int = 50
    ) -> List[Dict]:
        """Search audio transcripts using full-text search

        Args:
            query: Search query
            days_back: Number of days to search back
            limit: Maximum number of results

        Returns:
            List of matching transcript dictionaries
        """
        if not self.connection:
            self.connect()

        cutoff_time = (datetime.now() - timedelta(days=days_back)).isoformat()

        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT a.id, a.timestamp, a.source, a.speaker, a.text,
                   a.confidence, a.audio_file, a.call_id, a.metadata
            FROM audio_transcripts a
            JOIN audio_transcripts_fts f ON a.id = f.rowid
            WHERE f.text MATCH ?
            AND a.timestamp >= ?
            ORDER BY a.timestamp DESC
            LIMIT ?
        """,
            (query, cutoff_time, limit),
        )

        results = []
        for row in cursor.fetchall():
            result = dict(row)
            if result["metadata"]:
                result["metadata"] = json.loads(result["metadata"])
            results.append(result)

        return results

    def cleanup_old_transcripts(self, retention_days: int = 90):
        """Delete transcripts older than retention period

        Args:
            retention_days: Number of days to retain transcripts (default: 90)
        """
        if not self.connection:
            self.connect()

        cutoff_time = (datetime.now() - timedelta(days=retention_days)).isoformat()

        cursor = self.connection.cursor()
        cursor.execute(
            """
            DELETE FROM audio_transcripts
            WHERE timestamp < ?
            AND source != 'vapi'
        """,
            (cutoff_time,),
        )
        self.connection.commit()

        # VAPI calls are kept indefinitely as per requirements



__all__ = ["Database"]
