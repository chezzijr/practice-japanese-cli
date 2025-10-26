"""
Database connection management for Japanese Learning CLI.

Provides context managers and utilities for safe SQLite database access.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator


# Default database path
DEFAULT_DB_PATH = Path.home() / ".local" / "share" / "japanese-cli" / "japanese.db"

# Project-relative database path (for development)
PROJECT_DB_PATH = Path(__file__).parent.parent.parent.parent / "data" / "japanese.db"


def get_db_path() -> Path:
    """
    Get the database file path.

    Uses the project-relative path if it exists or its directory exists,
    otherwise uses the user data directory.

    Returns:
        Path: Path to the database file
    """
    # Check if we're in project development mode
    if PROJECT_DB_PATH.parent.exists():
        return PROJECT_DB_PATH
    return DEFAULT_DB_PATH


def ensure_data_directory() -> None:
    """
    Ensure the data directory exists.

    Creates the directory structure if it doesn't exist.
    """
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Also create dict subdirectory for downloaded dictionaries
    dict_path = db_path.parent / "dict"
    dict_path.mkdir(exist_ok=True)


@contextmanager
def get_db_connection(
    db_path: Path | None = None,
    row_factory: bool = True
) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database connections with automatic transaction management.

    Provides a database connection that automatically commits on success
    or rolls back on exception.

    Args:
        db_path: Path to database file (defaults to get_db_path())
        row_factory: If True, use Row factory for dict-like access (default: True)

    Yields:
        sqlite3.Connection: Database connection

    Example:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM vocabulary")
            rows = cursor.fetchall()

    Raises:
        sqlite3.Error: On database errors
    """
    if db_path is None:
        db_path = get_db_path()

    # Ensure directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))

    # Set row factory for dict-like access
    if row_factory:
        conn.row_factory = sqlite3.Row

    # Enable foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def get_cursor(
    db_path: Path | None = None,
    row_factory: bool = True
) -> Generator[sqlite3.Cursor, None, None]:
    """
    Context manager that provides a database cursor.

    Convenience wrapper around get_db_connection for direct cursor access.

    Args:
        db_path: Path to database file (defaults to get_db_path())
        row_factory: If True, use Row factory for dict-like access (default: True)

    Yields:
        sqlite3.Cursor: Database cursor

    Example:
        with get_cursor() as cursor:
            cursor.execute("SELECT * FROM vocabulary WHERE jlpt_level = ?", ("n5",))
            rows = cursor.fetchall()
    """
    with get_db_connection(db_path, row_factory) as conn:
        yield conn.cursor()


def execute_script(sql: str, db_path: Path | None = None) -> None:
    """
    Execute a SQL script (multiple statements).

    Useful for schema creation and migrations.

    Args:
        sql: SQL script to execute
        db_path: Path to database file (defaults to get_db_path())

    Raises:
        sqlite3.Error: On database errors
    """
    with get_db_connection(db_path, row_factory=False) as conn:
        conn.executescript(sql)


def database_exists(db_path: Path | None = None) -> bool:
    """
    Check if the database file exists.

    Args:
        db_path: Path to database file (defaults to get_db_path())

    Returns:
        bool: True if database file exists
    """
    if db_path is None:
        db_path = get_db_path()
    return db_path.exists()
