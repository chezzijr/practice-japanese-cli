"""
Tests for database schema creation and constraints.
"""

import sqlite3

import pytest

from japanese_cli.database import add_kanji, add_vocabulary, create_review
from japanese_cli.database.connection import get_cursor
from japanese_cli.database.schema import get_table_names


def test_all_tables_created(clean_db):
    """Test that all 6 tables are created."""
    expected_tables = get_table_names()

    with get_cursor(clean_db) as cursor:
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        actual_tables = [row["name"] for row in cursor.fetchall()]

    for table in expected_tables:
        assert table in actual_tables


def test_all_indexes_created(clean_db):
    """Test that all performance indexes are created."""
    expected_indexes = [
        "idx_vocabulary_jlpt",
        "idx_vocabulary_word",
        "idx_kanji_jlpt",
        "idx_grammar_jlpt",
        "idx_reviews_due",
        "idx_reviews_item",
        "idx_history_review",
        "idx_history_date",
    ]

    with get_cursor(clean_db) as cursor:
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        actual_indexes = [row["name"] for row in cursor.fetchall()]

    for index in expected_indexes:
        assert index in actual_indexes


def test_vocabulary_table_structure(clean_db):
    """Test vocabulary table has correct columns."""
    with get_cursor(clean_db) as cursor:
        cursor.execute("PRAGMA table_info(vocabulary)")
        columns = {row["name"]: row["type"] for row in cursor.fetchall()}

    assert "id" in columns
    assert "word" in columns
    assert "reading" in columns
    assert "meanings" in columns
    assert "jlpt_level" in columns
    assert "created_at" in columns
    assert "updated_at" in columns


def test_kanji_table_structure(clean_db):
    """Test kanji table has correct columns."""
    with get_cursor(clean_db) as cursor:
        cursor.execute("PRAGMA table_info(kanji)")
        columns = {row["name"]: row["type"] for row in cursor.fetchall()}

    assert "id" in columns
    assert "character" in columns
    assert "on_readings" in columns
    assert "kun_readings" in columns
    assert "vietnamese_reading" in columns
    assert "stroke_count" in columns


def test_reviews_table_structure(clean_db):
    """Test reviews table has correct columns."""
    with get_cursor(clean_db) as cursor:
        cursor.execute("PRAGMA table_info(reviews)")
        columns = {row["name"]: row["type"] for row in cursor.fetchall()}

    assert "id" in columns
    assert "item_id" in columns
    assert "item_type" in columns
    assert "fsrs_card_state" in columns
    assert "due_date" in columns
    assert "review_count" in columns


def test_kanji_unique_constraint(clean_db, sample_kanji):
    """Test that duplicate kanji character violates UNIQUE constraint."""
    # Insert first kanji
    add_kanji(**sample_kanji, db_path=clean_db)

    # Attempt to insert duplicate - should fail
    with pytest.raises(sqlite3.IntegrityError):
        add_kanji(**sample_kanji, db_path=clean_db)


def test_review_unique_constraint(clean_db, db_with_vocabulary):
    """Test that duplicate review (item_id, item_type) violates UNIQUE constraint."""
    from fsrs import Card
    from datetime import datetime, timezone

    db_path, vocab_id = db_with_vocabulary
    card = Card()

    # Create first review
    create_review(
        item_id=vocab_id,
        item_type="vocab",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=db_path
    )

    # Attempt to create duplicate - should fail
    with pytest.raises(sqlite3.IntegrityError):
        create_review(
            item_id=vocab_id,
            item_type="vocab",
            fsrs_card_state=card.to_dict(),
            due_date=card.due,
            db_path=db_path
        )


def test_progress_unique_user_id(clean_db):
    """Test that duplicate user_id in progress violates UNIQUE constraint."""
    from japanese_cli.database import init_progress

    # Create first progress entry
    init_progress(user_id="test_user", db_path=clean_db)

    # Attempt to create duplicate - should fail
    with pytest.raises(sqlite3.IntegrityError):
        init_progress(user_id="test_user", db_path=clean_db)


def test_review_history_foreign_key(clean_db):
    """Test that review_history has foreign key constraint to reviews."""
    from japanese_cli.database import add_review_history

    # Attempt to add review history for non-existent review
    # Should fail due to foreign key constraint
    with pytest.raises(sqlite3.IntegrityError):
        add_review_history(
            review_id=9999,  # Non-existent
            rating=3,
            db_path=clean_db
        )
