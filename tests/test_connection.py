"""
Tests for database connection management.
"""

import sqlite3

import pytest

from japanese_cli.database.connection import (
    database_exists,
    ensure_data_directory,
    execute_script,
    get_cursor,
    get_db_connection,
)


def test_get_db_connection_success(temp_db_path):
    """Test that database connection is created successfully."""
    with get_db_connection(temp_db_path) as conn:
        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)


def test_get_db_connection_row_factory(temp_db_path):
    """Test that row factory returns dict-like Row objects."""
    with get_db_connection(temp_db_path, row_factory=True) as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE test (id INTEGER, name TEXT)")
        cursor.execute("INSERT INTO test VALUES (1, 'test')")
        cursor.execute("SELECT * FROM test")
        row = cursor.fetchone()

        # Row objects support both index and key access
        assert row[0] == 1
        assert row["id"] == 1
        assert row["name"] == "test"


def test_get_db_connection_commits_on_success(temp_db_path):
    """Test that connection commits changes on successful exit."""
    with get_db_connection(temp_db_path) as conn:
        conn.execute("CREATE TABLE test (id INTEGER)")
        conn.execute("INSERT INTO test VALUES (1)")

    # Verify data persisted
    with get_db_connection(temp_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM test")
        count = cursor.fetchone()[0]
        assert count == 1


def test_get_db_connection_rollback_on_exception(temp_db_path):
    """Test that connection rolls back on exception."""
    with get_db_connection(temp_db_path) as conn:
        conn.execute("CREATE TABLE test (id INTEGER)")

    try:
        with get_db_connection(temp_db_path) as conn:
            conn.execute("INSERT INTO test VALUES (1)")
            raise ValueError("Simulated error")
    except ValueError:
        pass

    # Verify data was NOT persisted
    with get_db_connection(temp_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM test")
        count = cursor.fetchone()[0]
        assert count == 0


def test_get_cursor_works(temp_db_path):
    """Test that get_cursor context manager works."""
    execute_script("CREATE TABLE test (id INTEGER)", temp_db_path)

    with get_cursor(temp_db_path) as cursor:
        cursor.execute("INSERT INTO test VALUES (1)")

    # Verify data persisted
    with get_cursor(temp_db_path) as cursor:
        cursor.execute("SELECT COUNT(*) FROM test")
        count = cursor.fetchone()[0]
        assert count == 1


def test_foreign_keys_enabled(temp_db_path):
    """Test that foreign key constraints are enabled."""
    with get_db_connection(temp_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys")
        fk_enabled = cursor.fetchone()[0]
        assert fk_enabled == 1


def test_database_exists(temp_db_path):
    """Test database_exists function."""
    from pathlib import Path

    # temp_db_path already exists (created by fixture), so it should return True
    assert database_exists(temp_db_path)

    # Test with non-existent path
    non_existent = Path("/tmp/definitely_does_not_exist_12345.db")
    assert not database_exists(non_existent)


def test_execute_script_multiple_statements(temp_db_path):
    """Test execute_script with multiple SQL statements."""
    script = """
        CREATE TABLE test1 (id INTEGER);
        CREATE TABLE test2 (id INTEGER);
        INSERT INTO test1 VALUES (1);
        INSERT INTO test2 VALUES (2);
    """
    execute_script(script, temp_db_path)

    # Verify both tables exist and have data
    with get_cursor(temp_db_path) as cursor:
        cursor.execute("SELECT COUNT(*) FROM test1")
        assert cursor.fetchone()[0] == 1

        cursor.execute("SELECT COUNT(*) FROM test2")
        assert cursor.fetchone()[0] == 1
