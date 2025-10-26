"""
Pytest configuration and shared fixtures for Japanese Learning CLI tests.
"""

import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from japanese_cli.database import (
    add_kanji,
    add_vocabulary,
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
