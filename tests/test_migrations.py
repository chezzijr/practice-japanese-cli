"""
Tests for database migration system.
"""

import pytest

from japanese_cli.database.connection import get_db_connection
from japanese_cli.database.migrations import (
    CURRENT_VERSION,
    get_schema_version,
    initialize_database,
    needs_migration,
    run_migrations,
    set_schema_version,
)


def test_initial_schema_version_is_zero(temp_db_path):
    """Test that a new database has version 0."""
    # Just create the file
    with get_db_connection(temp_db_path):
        pass

    version = get_schema_version(temp_db_path)
    assert version == 0


def test_initialize_database_sets_version(temp_db_path):
    """Test that initialize_database sets the correct version."""
    was_created = initialize_database(temp_db_path)

    assert was_created is True
    version = get_schema_version(temp_db_path)
    assert version == CURRENT_VERSION


def test_initialize_database_is_idempotent(temp_db_path):
    """Test that initialize_database can be run multiple times safely."""
    # First initialization
    was_created1 = initialize_database(temp_db_path)
    assert was_created1 is True

    # Second initialization
    was_created2 = initialize_database(temp_db_path)
    assert was_created2 is False  # Already existed

    # Version should still be correct
    version = get_schema_version(temp_db_path)
    assert version == CURRENT_VERSION


def test_set_schema_version(temp_db_path):
    """Test setting and getting schema version."""
    with get_db_connection(temp_db_path):
        pass

    set_schema_version(5, temp_db_path)
    version = get_schema_version(temp_db_path)
    assert version == 5


def test_needs_migration_on_new_db(temp_db_path):
    """Test that a new database needs migration."""
    with get_db_connection(temp_db_path):
        pass

    assert needs_migration(temp_db_path) is True


def test_needs_migration_on_current_db(clean_db):
    """Test that a current database doesn't need migration."""
    assert needs_migration(clean_db) is False


def test_run_migrations_updates_version(temp_db_path):
    """Test that run_migrations updates the schema version."""
    with get_db_connection(temp_db_path):
        pass

    migrations_run = run_migrations(temp_db_path)

    assert migrations_run == CURRENT_VERSION  # Should run all migrations
    assert get_schema_version(temp_db_path) == CURRENT_VERSION


def test_initialize_rejects_newer_version(temp_db_path):
    """Test that initialize_database rejects newer schema versions."""
    with get_db_connection(temp_db_path):
        pass

    # Set version to something higher than current
    set_schema_version(CURRENT_VERSION + 10, temp_db_path)

    # Should raise ValueError
    with pytest.raises(ValueError, match="newer than"):
        initialize_database(temp_db_path)


def test_migration_creates_all_tables(temp_db_path):
    """Test that migrations create all expected tables."""
    from japanese_cli.database.schema import get_table_names

    run_migrations(temp_db_path)

    expected_tables = get_table_names()

    with get_db_connection(temp_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        actual_tables = [row[0] for row in cursor.fetchall()]

    for table in expected_tables:
        assert table in actual_tables
