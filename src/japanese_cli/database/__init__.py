"""
Database module for Japanese Learning CLI.

Provides database connection, schema management, and query utilities.
"""

from .connection import (
    database_exists,
    ensure_data_directory,
    execute_script,
    get_cursor,
    get_db_connection,
    get_db_path,
)
from .migrations import (
    get_schema_version,
    initialize_database,
    needs_migration,
    run_migrations,
)
from .queries import (
    add_grammar,
    add_kanji,
    add_review_history,
    add_vocabulary,
    create_review,
    delete_grammar,
    delete_kanji,
    delete_vocabulary,
    get_due_cards,
    get_grammar_by_id,
    get_kanji_by_character,
    get_kanji_by_id,
    get_progress,
    get_review,
    get_vocabulary_by_id,
    increment_streak,
    init_progress,
    list_grammar,
    list_kanji,
    list_vocabulary,
    search_kanji,
    search_kanji_by_reading,
    search_vocabulary,
    search_vocabulary_by_reading,
    update_grammar,
    update_kanji,
    update_progress,
    update_progress_level,
    update_review,
    update_vocabulary,
)
from .schema import get_schema_sql, get_table_names

__all__ = [
    # Connection
    "get_db_connection",
    "get_cursor",
    "get_db_path",
    "ensure_data_directory",
    "execute_script",
    "database_exists",
    # Migrations
    "initialize_database",
    "run_migrations",
    "get_schema_version",
    "needs_migration",
    # Schema
    "get_schema_sql",
    "get_table_names",
    # Vocabulary queries
    "add_vocabulary",
    "get_vocabulary_by_id",
    "list_vocabulary",
    "search_vocabulary",
    "search_vocabulary_by_reading",
    "update_vocabulary",
    "delete_vocabulary",
    # Kanji queries
    "add_kanji",
    "get_kanji_by_id",
    "get_kanji_by_character",
    "list_kanji",
    "search_kanji",
    "search_kanji_by_reading",
    "update_kanji",
    "delete_kanji",
    # Grammar queries
    "add_grammar",
    "get_grammar_by_id",
    "list_grammar",
    "update_grammar",
    "delete_grammar",
    # Review queries
    "create_review",
    "get_review",
    "update_review",
    "get_due_cards",
    "add_review_history",
    # Progress queries
    "get_progress",
    "init_progress",
    "update_progress",
    "update_progress_level",
    "increment_streak",
]
