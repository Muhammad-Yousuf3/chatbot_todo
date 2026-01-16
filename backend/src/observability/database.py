"""
SQLite database connection manager for observability logs.

This module provides async connection management for the logs.db database,
separate from the main PostgreSQL tasks database.

Feature: 004-agent-observability
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import AsyncGenerator

import aiosqlite

# Default database path
_DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "logs.db"

# Module-level database path (can be overridden for testing)
_db_path: Path | str = _DEFAULT_DB_PATH

# Lock for concurrent access
_db_lock = asyncio.Lock()

# Flag for in-memory shared cache mode
_use_shared_cache: bool = False


def set_db_path(path: Path | str, shared_cache: bool = False) -> None:
    """
    Set the database path. Used for testing with in-memory or temp databases.

    Args:
        path: Database path or ":memory:" for in-memory database
        shared_cache: If True and path is ":memory:", use shared cache mode
                      so multiple connections share the same database
    """
    global _db_path, _use_shared_cache
    _db_path = path if isinstance(path, str) and path == ":memory:" else (
        Path(path) if isinstance(path, str) else path
    )
    _use_shared_cache = shared_cache


def get_db_path() -> Path | str:
    """Get the current database path."""
    return _db_path


def _get_connection_string() -> str:
    """Get the SQLite connection string, handling shared cache for in-memory DBs."""
    db_path = get_db_path()
    if db_path == ":memory:" and _use_shared_cache:
        # Use URI mode with shared cache for in-memory database
        # This allows multiple connections to share the same in-memory DB
        return "file::memory:?cache=shared"
    return str(db_path)


@asynccontextmanager
async def get_log_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """
    Get an async connection to the log database.

    Usage:
        async with get_log_db() as db:
            await db.execute("SELECT * FROM decision_logs")
    """
    # Ensure parent directory exists for file-based databases
    db_path = get_db_path()
    if isinstance(db_path, Path):
        db_path.parent.mkdir(parents=True, exist_ok=True)

    connection_string = _get_connection_string()
    use_uri = connection_string.startswith("file:")

    async with _db_lock:
        conn = await aiosqlite.connect(connection_string, uri=use_uri)
        conn.row_factory = aiosqlite.Row
        try:
            yield conn
        finally:
            await conn.close()


async def init_log_db() -> None:
    """
    Initialize the log database with required tables.

    Creates tables for:
    - decision_logs: Agent decision records
    - tool_invocation_logs: Tool call records
    - baseline_snapshots: Behavioral baselines
    - validation_reports: Validation run results

    Safe to call multiple times - uses CREATE TABLE IF NOT EXISTS.
    """
    async with get_log_db() as db:
        # DecisionLog table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS decision_logs (
                id TEXT PRIMARY KEY,
                decision_id TEXT NOT NULL UNIQUE,
                conversation_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                message TEXT NOT NULL,
                intent_type TEXT NOT NULL,
                confidence REAL,
                extracted_params TEXT DEFAULT '{}',
                decision_type TEXT NOT NULL,
                outcome_category TEXT NOT NULL,
                response_text TEXT,
                created_at TEXT NOT NULL,
                duration_ms INTEGER NOT NULL
            )
        """)

        # DecisionLog indexes
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_decision_conversation
            ON decision_logs(conversation_id)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_decision_user
            ON decision_logs(user_id)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_decision_created
            ON decision_logs(created_at)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_decision_outcome
            ON decision_logs(outcome_category)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_decision_id
            ON decision_logs(decision_id)
        """)

        # ToolInvocationLog table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tool_invocation_logs (
                id TEXT PRIMARY KEY,
                decision_id TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                parameters TEXT NOT NULL,
                result TEXT,
                success INTEGER NOT NULL,
                error_code TEXT,
                error_message TEXT,
                duration_ms INTEGER NOT NULL,
                invoked_at TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                FOREIGN KEY (decision_id) REFERENCES decision_logs(decision_id)
            )
        """)

        # ToolInvocationLog indexes
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_tool_decision
            ON tool_invocation_logs(decision_id)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_tool_name
            ON tool_invocation_logs(tool_name)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_tool_invoked
            ON tool_invocation_logs(invoked_at)
        """)

        # BaselineSnapshot table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS baseline_snapshots (
                id TEXT PRIMARY KEY,
                snapshot_name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TEXT NOT NULL,
                sample_start TEXT NOT NULL,
                sample_end TEXT NOT NULL,
                intent_distribution TEXT NOT NULL,
                tool_frequency TEXT NOT NULL,
                error_rate REAL NOT NULL,
                sample_size INTEGER NOT NULL
            )
        """)

        # ValidationReport table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS validation_reports (
                id TEXT PRIMARY KEY,
                run_at TEXT NOT NULL,
                baseline_id TEXT,
                test_count INTEGER NOT NULL,
                pass_count INTEGER NOT NULL,
                fail_count INTEGER NOT NULL,
                results TEXT NOT NULL,
                duration_ms INTEGER NOT NULL,
                drift_detected INTEGER NOT NULL,
                FOREIGN KEY (baseline_id) REFERENCES baseline_snapshots(id)
            )
        """)

        await db.commit()


async def cleanup_old_logs(retention_days: int = 30) -> int:
    """
    Delete logs older than the specified retention period.

    Args:
        retention_days: Number of days to retain logs (default: 30)

    Returns:
        Number of decision logs deleted
    """
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
    cutoff_str = cutoff_date.isoformat()

    async with get_log_db() as db:
        # Get count before deletion
        cursor = await db.execute(
            "SELECT COUNT(*) FROM decision_logs WHERE created_at < ?",
            (cutoff_str,)
        )
        row = await cursor.fetchone()
        count = row[0] if row else 0

        # Delete old tool invocation logs first (foreign key constraint)
        await db.execute("""
            DELETE FROM tool_invocation_logs
            WHERE decision_id IN (
                SELECT decision_id FROM decision_logs WHERE created_at < ?
            )
        """, (cutoff_str,))

        # Delete old decision logs
        await db.execute(
            "DELETE FROM decision_logs WHERE created_at < ?",
            (cutoff_str,)
        )

        await db.commit()
        return count
