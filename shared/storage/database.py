"""SQLite database interface

This module provides the main database interface for Context Engine.
Implementation will be added across different phases.
"""
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models.audio_transcript import AudioTranscript


class Database:
    """SQLite database with FTS5 support

    This class provides:
    - Connection management
    - Schema creation and migration
    - Query helpers
    - Full-text search via FTS5
    """

    def __init__(self, db_path: str = "context.db"):
        """Initialize database connection

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.connection: Optional[sqlite3.Connection] = None

    def connect(self):
        """Connect to database"""
        if self.connection is None:
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row
            # Enable foreign keys
            self.connection.execute("PRAGMA foreign_keys = ON")

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None

    def create_schema(self):
        """Create database schema - implemented in phases"""
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()

        # Phase 2: Audio transcripts table
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
