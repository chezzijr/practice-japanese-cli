"""
Database migration system for Japanese Learning CLI.

Manages database schema versioning and migrations using SQLite's PRAGMA user_version.
"""

from pathlib import Path
from typing import Callable

from .connection import get_db_connection, get_db_path, execute_script
from .schema import get_schema_sql


# Current schema version
CURRENT_VERSION = 1

# Migration functions: version -> migration function
MIGRATIONS: dict[int, Callable[[Path], None]] = {}


def register_migration(version: int):
    """
    Decorator to register a migration function.

    Args:
        version: The version this migration upgrades to

    Example:
        @register_migration(2)
        def migrate_to_v2(db_path: Path) -> None:
            # Migration logic here
            pass
    """
    def decorator(func: Callable[[Path], None]) -> Callable[[Path], None]:
        MIGRATIONS[version] = func
        return func
    return decorator


def get_schema_version(db_path: Path | None = None) -> int:
    """
    Get the current schema version from the database.

    Uses SQLite's PRAGMA user_version to track schema version.

    Args:
        db_path: Path to database file (defaults to get_db_path())

    Returns:
        int: Current schema version (0 if new database)
    """
    if db_path is None:
        db_path = get_db_path()

    with get_db_connection(db_path, row_factory=False) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA user_version")
        version = cursor.fetchone()[0]
        return version


def set_schema_version(version: int, db_path: Path | None = None) -> None:
    """
    Set the schema version in the database.

    Args:
        version: Schema version to set
        db_path: Path to database file (defaults to get_db_path())
    """
    if db_path is None:
        db_path = get_db_path()

    with get_db_connection(db_path, row_factory=False) as conn:
        # PRAGMA user_version doesn't support parameterized queries
        conn.execute(f"PRAGMA user_version = {int(version)}")


@register_migration(1)
def migrate_to_v1(db_path: Path) -> None:
    """
    Initial schema creation (v1).

    Creates all tables and indexes for the first time.

    Args:
        db_path: Path to database file
    """
    execute_script(get_schema_sql(), db_path)


def run_migrations(db_path: Path | None = None) -> int:
    """
    Run all pending migrations to bring database to current version.

    Args:
        db_path: Path to database file (defaults to get_db_path())

    Returns:
        int: Number of migrations executed

    Raises:
        ValueError: If a required migration is missing
    """
    if db_path is None:
        db_path = get_db_path()

    current_version = get_schema_version(db_path)
    migrations_run = 0

    # Run each migration in sequence
    for version in range(current_version + 1, CURRENT_VERSION + 1):
        if version not in MIGRATIONS:
            raise ValueError(
                f"Missing migration for version {version}. "
                f"Cannot upgrade from v{current_version} to v{CURRENT_VERSION}."
            )

        # Run the migration
        migration_func = MIGRATIONS[version]
        migration_func(db_path)

        # Update version
        set_schema_version(version, db_path)
        migrations_run += 1

    return migrations_run


def initialize_database(db_path: Path | None = None) -> bool:
    """
    Initialize a new database with the current schema.

    This is a convenience function that runs all migrations from version 0.

    Args:
        db_path: Path to database file (defaults to get_db_path())

    Returns:
        bool: True if database was newly created, False if already existed

    Raises:
        ValueError: If database exists but schema version is higher than current
    """
    if db_path is None:
        db_path = get_db_path()

    current_version = get_schema_version(db_path)

    if current_version > CURRENT_VERSION:
        raise ValueError(
            f"Database schema version (v{current_version}) is newer than "
            f"this application supports (v{CURRENT_VERSION}). "
            f"Please upgrade the application."
        )

    if current_version == CURRENT_VERSION:
        return False  # Already initialized

    # Run migrations
    run_migrations(db_path)
    return True


def needs_migration(db_path: Path | None = None) -> bool:
    """
    Check if database needs migration.

    Args:
        db_path: Path to database file (defaults to get_db_path())

    Returns:
        bool: True if migrations are needed
    """
    if db_path is None:
        db_path = get_db_path()

    current_version = get_schema_version(db_path)
    return current_version < CURRENT_VERSION
