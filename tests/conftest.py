"""
Pytest configuration and shared fixtures for Japanese Learning CLI tests.
"""

import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from japanese_cli.database import (
    add_kanji,
    add_vocabulary,
    add_grammar,
    create_review,
    initialize_database,
)


@pytest.fixture
def temp_db_path():
    """
    Create a temporary database file path.

    Yields:
        Path: Temporary database file path
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = Path(tmp.name)

    yield db_path

    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def clean_db(temp_db_path):
    """
    Create a fresh initialized database for each test.

    Args:
        temp_db_path: Temporary database path fixture

    Returns:
        Path: Path to initialized test database
    """
    from japanese_cli.database import init_progress

    initialize_database(temp_db_path)
    # Initialize progress for default user
    init_progress(db_path=temp_db_path)
    return temp_db_path


@pytest.fixture
def mock_db_path(clean_db, monkeypatch):
    """
    Monkeypatch get_db_path() to return the temp database for CLI tests.

    This ensures CLI commands never touch the production database during tests.

    Args:
        clean_db: Clean database fixture (temp database path)
        monkeypatch: Pytest monkeypatch fixture

    Returns:
        Path: Temporary database path (same as clean_db)

    Usage:
        def test_cli_command(mock_db_path):
            # CLI commands will now use the temp database
            result = runner.invoke(app, ["some-command"])
    """
    import japanese_cli.database.connection as conn_module

    # Patch get_db_path at the module level where it's actually called
    monkeypatch.setattr(conn_module, 'get_db_path', lambda: clean_db)

    # Also patch PROJECT_DB_PATH to point to temp database
    monkeypatch.setattr(conn_module, 'PROJECT_DB_PATH', clean_db)

    return clean_db


@pytest.fixture
def sample_vocabulary():
    """
    Sample vocabulary data for testing.

    Returns:
        dict: Sample vocabulary data
    """
    return {
        "word": "単語",
        "reading": "たんご",
        "meanings": {"vi": ["từ vựng"], "en": ["word", "vocabulary"]},
        "vietnamese_reading": "đơn ngữ",
        "jlpt_level": "n5",
        "part_of_speech": "noun",
        "tags": ["common", "basic"],
        "notes": "Basic word for vocabulary"
    }


@pytest.fixture
def sample_kanji():
    """
    Sample kanji data for testing.

    Returns:
        dict: Sample kanji data
    """
    return {
        "character": "語",
        "on_readings": ["ゴ"],
        "kun_readings": ["かた.る", "かた.らう"],
        "meanings": {"vi": ["ngữ"], "en": ["word", "language"]},
        "vietnamese_reading": "ngữ",
        "jlpt_level": "n5",
        "stroke_count": 14,
        "radical": "言",
        "notes": "Language kanji"
    }


@pytest.fixture
def sample_grammar():
    """
    Sample grammar data for testing.

    Returns:
        dict: Sample grammar data
    """
    return {
        "title": "は (wa) particle",
        "structure": "Noun + は + Predicate",
        "explanation": "Topic marker particle in Japanese",
        "jlpt_level": "n5",
        "examples": [
            {
                "jp": "私は学生です",
                "vi": "Tôi là học sinh",
                "en": "I am a student"
            },
            {
                "jp": "これは本です",
                "vi": "Đây là sách",
                "en": "This is a book"
            }
        ],
        "related_grammar": [],
        "notes": "Basic topic marker"
    }


@pytest.fixture
def db_with_vocabulary(clean_db, sample_vocabulary):
    """
    Database with sample vocabulary already inserted.

    Args:
        clean_db: Clean database fixture
        sample_vocabulary: Sample vocabulary data

    Returns:
        tuple: (db_path, vocabulary_id)
    """
    vocab_id = add_vocabulary(**sample_vocabulary, db_path=clean_db)
    return clean_db, vocab_id


@pytest.fixture
def db_with_kanji(clean_db, sample_kanji):
    """
    Database with sample kanji already inserted.

    Args:
        clean_db: Clean database fixture
        sample_kanji: Sample kanji data

    Returns:
        tuple: (db_path, kanji_id)
    """
    kanji_id = add_kanji(**sample_kanji, db_path=clean_db)
    return clean_db, kanji_id


@pytest.fixture
def db_with_grammar(clean_db, sample_grammar):
    """
    Database with sample grammar already inserted.

    Args:
        clean_db: Clean database fixture
        sample_grammar: Sample grammar data

    Returns:
        tuple: (db_path, grammar_id)
    """
    grammar_id = add_grammar(**sample_grammar, db_path=clean_db)
    return clean_db, grammar_id


@pytest.fixture
def db_with_review(db_with_vocabulary):
    """
    Database with vocabulary and a review entry.

    Args:
        db_with_vocabulary: Database with vocabulary fixture

    Returns:
        tuple: (db_path, vocabulary_id, review_id)
    """
    from fsrs import Card

    db_path, vocab_id = db_with_vocabulary

    # Create FSRS card with due date in the past
    card = Card()
    card.due = datetime.now(timezone.utc)

    review_id = create_review(
        item_id=vocab_id,
        item_type="vocab",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=db_path
    )

    return db_path, vocab_id, review_id


# ============================================================================
# CLI Test Fixtures with Database Isolation
# ============================================================================


@pytest.fixture
def cli_clean_db(mock_db_path):
    """
    Clean database for CLI tests with automatic path monkeypatching.

    Use this instead of clean_db for CLI command tests to ensure isolation.

    Returns:
        Path: Temporary database path
    """
    return mock_db_path


@pytest.fixture
def cli_db_with_vocabulary(mock_db_path, sample_vocabulary):
    """
    Database with vocabulary for CLI tests with automatic path monkeypatching.

    Args:
        mock_db_path: Monkeypatched database path
        sample_vocabulary: Sample vocabulary data

    Returns:
        tuple: (db_path, vocabulary_id)
    """
    vocab_id = add_vocabulary(**sample_vocabulary, db_path=mock_db_path)
    return mock_db_path, vocab_id


@pytest.fixture
def cli_db_with_kanji(mock_db_path, sample_kanji):
    """
    Database with kanji for CLI tests with automatic path monkeypatching.

    Args:
        mock_db_path: Monkeypatched database path
        sample_kanji: Sample kanji data

    Returns:
        tuple: (db_path, kanji_id)
    """
    kanji_id = add_kanji(**sample_kanji, db_path=mock_db_path)
    return mock_db_path, kanji_id


@pytest.fixture
def cli_db_with_grammar(mock_db_path, sample_grammar):
    """
    Database with grammar for CLI tests with automatic path monkeypatching.

    Args:
        mock_db_path: Monkeypatched database path
        sample_grammar: Sample grammar data

    Returns:
        tuple: (db_path, grammar_id)
    """
    grammar_id = add_grammar(**sample_grammar, db_path=mock_db_path)
    return mock_db_path, grammar_id


@pytest.fixture
def cli_db_with_vocabulary_flashcard(mock_db_path, sample_vocabulary):
    """
    Database with vocabulary AND review entry for CLI flashcard tests.

    Args:
        mock_db_path: Monkeypatched database path
        sample_vocabulary: Sample vocabulary data

    Returns:
        tuple: (db_path, vocabulary_id, review_id)
    """
    from fsrs import Card

    vocab_id = add_vocabulary(**sample_vocabulary, db_path=mock_db_path)

    card = Card()
    review_id = create_review(
        item_id=vocab_id,
        item_type="vocab",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=mock_db_path
    )

    return mock_db_path, vocab_id, review_id


@pytest.fixture
def cli_db_with_kanji_flashcard(mock_db_path, sample_kanji):
    """
    Database with kanji AND review entry for CLI flashcard tests.

    Args:
        mock_db_path: Monkeypatched database path
        sample_kanji: Sample kanji data

    Returns:
        tuple: (db_path, kanji_id, review_id)
    """
    from fsrs import Card

    kanji_id = add_kanji(**sample_kanji, db_path=mock_db_path)

    card = Card()
    review_id = create_review(
        item_id=kanji_id,
        item_type="kanji",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=mock_db_path
    )

    return mock_db_path, kanji_id, review_id
