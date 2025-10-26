"""
Tests for MCQ Review Scheduler module.

Tests MCQReviewScheduler class for managing MCQ review sessions with FSRS integration.
"""

from datetime import datetime, timedelta, timezone

import pytest
from fsrs import Card, State

from japanese_cli.srs import MCQReviewScheduler, FSRSManager
from japanese_cli.models import ItemType, MCQReview
from japanese_cli.database import (
    add_vocabulary,
    add_kanji,
    get_mcq_review,
)


# ============================================================================
# Initialization Tests
# ============================================================================


def test_mcq_scheduler_default_initialization():
    """Test MCQReviewScheduler initializes with default parameters."""
    scheduler = MCQReviewScheduler()

    assert scheduler.fsrs_manager is not None
    assert isinstance(scheduler.fsrs_manager, FSRSManager)
    assert scheduler.db_path is None


def test_mcq_scheduler_custom_fsrs_manager():
    """Test MCQReviewScheduler with custom FSRSManager."""
    custom_fsrs = FSRSManager(desired_retention=0.95)
    scheduler = MCQReviewScheduler(fsrs_manager=custom_fsrs)

    assert scheduler.fsrs_manager.desired_retention == 0.95


# ============================================================================
# create_mcq_review Tests
# ============================================================================


def test_create_mcq_review_vocab(clean_db):
    """Test creating a new MCQ review for vocabulary."""
    # Add vocabulary
    vocab_id = add_vocabulary(
        word="単語",
        reading="たんご",
        meanings={"vi": ["từ vựng"], "en": ["word"]},
        jlpt_level="n5",
        db_path=clean_db,
    )

    # Create MCQ review
    scheduler = MCQReviewScheduler(db_path=clean_db)
    review_id = scheduler.create_mcq_review(vocab_id, ItemType.VOCAB)

    assert review_id > 0

    # Verify MCQ review was created
    review_row = get_mcq_review(vocab_id, "vocab", db_path=clean_db)
    assert review_row is not None
    assert review_row["item_id"] == vocab_id
    assert review_row["item_type"] == "vocab"


def test_create_mcq_review_kanji(clean_db):
    """Test creating a new MCQ review for kanji."""
    # Add kanji
    kanji_id = add_kanji(
        character="語",
        on_readings=["ゴ"],
        kun_readings=["かた.る"],
        meanings={"vi": ["ngữ"], "en": ["word"]},
        jlpt_level="n5",
        db_path=clean_db,
    )

    # Create MCQ review
    scheduler = MCQReviewScheduler(db_path=clean_db)
    review_id = scheduler.create_mcq_review(kanji_id, ItemType.KANJI)

    assert review_id > 0

    # Verify MCQ review was created
    review_row = get_mcq_review(kanji_id, "kanji", db_path=clean_db)
    assert review_row is not None
    assert review_row["item_id"] == kanji_id
    assert review_row["item_type"] == "kanji"


def test_create_mcq_review_with_string_type(clean_db):
    """Test creating MCQ review with string item type."""
    vocab_id = add_vocabulary(
        word="test",
        reading="てすと",
        meanings={"en": ["test"]},
        db_path=clean_db,
    )

    scheduler = MCQReviewScheduler(db_path=clean_db)
    review_id = scheduler.create_mcq_review(vocab_id, "vocab")

    assert review_id > 0


def test_create_mcq_review_invalid_vocab_id(clean_db):
    """Test creating MCQ review with invalid vocabulary ID raises error."""
    scheduler = MCQReviewScheduler(db_path=clean_db)

    with pytest.raises(ValueError, match="Vocabulary with id 999 not found"):
        scheduler.create_mcq_review(999, ItemType.VOCAB)


def test_create_mcq_review_invalid_kanji_id(clean_db):
    """Test creating MCQ review with invalid kanji ID raises error."""
    scheduler = MCQReviewScheduler(db_path=clean_db)

    with pytest.raises(ValueError, match="Kanji with id 999 not found"):
        scheduler.create_mcq_review(999, ItemType.KANJI)


# ============================================================================
# get_due_mcqs Tests
# ============================================================================


def test_get_due_mcqs_empty(clean_db):
    """Test getting due MCQ reviews when none exist."""
    scheduler = MCQReviewScheduler(db_path=clean_db)
    due_mcqs = scheduler.get_due_mcqs()

    assert due_mcqs == []


def test_get_due_mcqs(db_with_vocabulary):
    """Test getting due MCQ reviews."""
    db_path, vocab_id = db_with_vocabulary

    # Create MCQ review
    scheduler = MCQReviewScheduler(db_path=db_path)
    review_id = scheduler.create_mcq_review(vocab_id, ItemType.VOCAB)

    # Get due MCQ reviews
    due_mcqs = scheduler.get_due_mcqs()

    assert len(due_mcqs) == 1
    assert isinstance(due_mcqs[0], MCQReview)
    assert due_mcqs[0].item_id == vocab_id
    assert due_mcqs[0].item_type == ItemType.VOCAB


def test_get_due_mcqs_with_limit(db_with_vocabulary):
    """Test getting due MCQ reviews with limit."""
    db_path, vocab_id = db_with_vocabulary

    # Create multiple MCQ reviews
    scheduler = MCQReviewScheduler(db_path=db_path)
    scheduler.create_mcq_review(vocab_id, ItemType.VOCAB)

    # Add another vocabulary and MCQ review
    vocab_id2 = add_vocabulary(
        word="test2",
        reading="てすと2",
        meanings={"en": ["test2"]},
        db_path=db_path,
    )
    scheduler.create_mcq_review(vocab_id2, ItemType.VOCAB)

    # Get with limit
    due_mcqs = scheduler.get_due_mcqs(limit=1)

    assert len(due_mcqs) == 1


def test_get_due_mcqs_with_jlpt_filter(db_with_vocabulary):
    """Test getting due MCQ reviews filtered by JLPT level."""
    db_path, vocab_id = db_with_vocabulary

    # Create MCQ review for N5 vocabulary
    scheduler = MCQReviewScheduler(db_path=db_path)
    scheduler.create_mcq_review(vocab_id, ItemType.VOCAB)

    # Get N5 MCQ reviews
    due_mcqs = scheduler.get_due_mcqs(jlpt_level="n5")

    assert len(due_mcqs) == 1

    # Get N4 MCQ reviews (should be empty)
    due_mcqs = scheduler.get_due_mcqs(jlpt_level="n4")

    assert len(due_mcqs) == 0


def test_get_due_mcqs_with_type_filter(clean_db):
    """Test getting due MCQ reviews filtered by item type."""
    # Add vocabulary and kanji
    vocab_id = add_vocabulary(
        word="vocab",
        reading="ぼかぶ",
        meanings={"en": ["vocab"]},
        db_path=clean_db,
    )
    kanji_id = add_kanji(
        character="漢",
        on_readings=["カン"],
        kun_readings=[],
        meanings={"en": ["chinese"]},
        db_path=clean_db,
    )

    # Create MCQ reviews
    scheduler = MCQReviewScheduler(db_path=clean_db)
    scheduler.create_mcq_review(vocab_id, ItemType.VOCAB)
    scheduler.create_mcq_review(kanji_id, ItemType.KANJI)

    # Filter by vocab
    vocab_reviews = scheduler.get_due_mcqs(item_type=ItemType.VOCAB)
    assert len(vocab_reviews) == 1
    assert vocab_reviews[0].item_type == ItemType.VOCAB

    # Filter by kanji
    kanji_reviews = scheduler.get_due_mcqs(item_type=ItemType.KANJI)
    assert len(kanji_reviews) == 1
    assert kanji_reviews[0].item_type == ItemType.KANJI


def test_get_due_mcqs_returns_mcq_review_models(db_with_vocabulary):
    """Test that get_due_mcqs returns MCQReview model instances."""
    db_path, vocab_id = db_with_vocabulary

    scheduler = MCQReviewScheduler(db_path=db_path)
    scheduler.create_mcq_review(vocab_id, ItemType.VOCAB)

    due_mcqs = scheduler.get_due_mcqs()

    assert len(due_mcqs) == 1
    mcq_review = due_mcqs[0]
    assert isinstance(mcq_review, MCQReview)
    assert hasattr(mcq_review, 'fsrs_card_state')
    assert hasattr(mcq_review, 'due_date')
    assert hasattr(mcq_review, 'review_count')


# ============================================================================
# get_mcq_review_by_item Tests
# ============================================================================


def test_get_mcq_review_by_item(db_with_vocabulary):
    """Test getting MCQ review by item ID and type."""
    db_path, vocab_id = db_with_vocabulary

    # Create MCQ review
    scheduler = MCQReviewScheduler(db_path=db_path)
    scheduler.create_mcq_review(vocab_id, ItemType.VOCAB)

    # Get MCQ review
    review = scheduler.get_mcq_review_by_item(vocab_id, ItemType.VOCAB)

    assert review is not None
    assert isinstance(review, MCQReview)
    assert review.item_id == vocab_id


def test_get_mcq_review_by_item_not_found(clean_db):
    """Test getting MCQ review that doesn't exist returns None."""
    scheduler = MCQReviewScheduler(db_path=clean_db)
    review = scheduler.get_mcq_review_by_item(999, ItemType.VOCAB)

    assert review is None


# ============================================================================
# process_mcq_review Tests
# ============================================================================


def test_process_mcq_review_correct_answer(db_with_vocabulary):
    """Test processing MCQ review with correct answer uses Rating.Good."""
    db_path, vocab_id = db_with_vocabulary

    # Create MCQ review
    scheduler = MCQReviewScheduler(db_path=db_path)
    review_id = scheduler.create_mcq_review(vocab_id, ItemType.VOCAB)

    # Get initial review
    initial_review = scheduler.get_mcq_review_by_item(vocab_id, ItemType.VOCAB)
    initial_due = initial_review.due_date
    initial_count = initial_review.review_count

    # Process review with correct answer
    updated_review = scheduler.process_mcq_review(
        review_id=review_id,
        is_correct=True,
        selected_option=2,  # User selected option C (which was correct)
        duration_ms=5000
    )

    assert updated_review.review_count == initial_count + 1
    assert updated_review.last_reviewed is not None
    assert updated_review.due_date != initial_due  # Due date should change


def test_process_mcq_review_incorrect_answer(db_with_vocabulary):
    """Test processing MCQ review with incorrect answer uses Rating.Again."""
    db_path, vocab_id = db_with_vocabulary

    # Create MCQ review
    scheduler = MCQReviewScheduler(db_path=db_path)
    review_id = scheduler.create_mcq_review(vocab_id, ItemType.VOCAB)

    # Get initial review
    initial_review = scheduler.get_mcq_review_by_item(vocab_id, ItemType.VOCAB)
    initial_count = initial_review.review_count

    # Process review with incorrect answer
    updated_review = scheduler.process_mcq_review(
        review_id=review_id,
        is_correct=False,
        selected_option=1,  # User selected option B (which was incorrect)
        duration_ms=3000
    )

    assert updated_review.review_count == initial_count + 1
    assert updated_review.last_reviewed is not None
    # Incorrect answers should result in shorter intervals


def test_process_mcq_review_all_options(db_with_vocabulary):
    """Test processing MCQ reviews with all option indices (0-3)."""
    db_path, vocab_id = db_with_vocabulary

    scheduler = MCQReviewScheduler(db_path=db_path)

    # Test each option index (A=0, B=1, C=2, D=3)
    for option in [0, 1, 2, 3]:
        # Create new vocabulary and MCQ review for each option
        new_vocab_id = add_vocabulary(
            word=f"test{option}",
            reading=f"てすと{option}",
            meanings={"en": [f"test{option}"]},
            db_path=db_path,
        )
        review_id = scheduler.create_mcq_review(new_vocab_id, ItemType.VOCAB)

        # Process review with this option
        updated_review = scheduler.process_mcq_review(
            review_id=review_id,
            is_correct=True,
            selected_option=option,
            duration_ms=4000
        )

        assert updated_review.review_count == 1
        assert updated_review.last_reviewed is not None


def test_process_mcq_review_updates_due_date(db_with_vocabulary):
    """Test that processing MCQ review updates due date via FSRS."""
    db_path, vocab_id = db_with_vocabulary

    scheduler = MCQReviewScheduler(db_path=db_path)
    review_id = scheduler.create_mcq_review(vocab_id, ItemType.VOCAB)

    # Get initial due date
    initial_review = scheduler.get_mcq_review_by_item(vocab_id, ItemType.VOCAB)
    initial_due = initial_review.due_date

    # Process review
    updated_review = scheduler.process_mcq_review(
        review_id=review_id,
        is_correct=True,
        selected_option=0,
        duration_ms=5000
    )

    # Due date should be updated by FSRS
    assert updated_review.due_date != initial_due
    assert updated_review.due_date > datetime.now(timezone.utc)


def test_process_mcq_review_increments_count(db_with_vocabulary):
    """Test that processing MCQ review increments review_count."""
    db_path, vocab_id = db_with_vocabulary

    scheduler = MCQReviewScheduler(db_path=db_path)
    review_id = scheduler.create_mcq_review(vocab_id, ItemType.VOCAB)

    # Process review multiple times
    for expected_count in [1, 2, 3]:
        # Make it due again
        from japanese_cli.database import get_cursor

        with get_cursor(db_path) as cursor:
            past_time = datetime.now(timezone.utc) - timedelta(hours=1)
            cursor.execute(
                "UPDATE mcq_reviews SET due_date = ? WHERE id = ?",
                (past_time.isoformat(), review_id),
            )

        updated_review = scheduler.process_mcq_review(
            review_id=review_id,
            is_correct=True,
            selected_option=0
        )

        assert updated_review.review_count == expected_count


def test_process_mcq_review_records_history(db_with_vocabulary):
    """Test that processing MCQ review adds entry to mcq_review_history."""
    db_path, vocab_id = db_with_vocabulary

    scheduler = MCQReviewScheduler(db_path=db_path)
    review_id = scheduler.create_mcq_review(vocab_id, ItemType.VOCAB)

    # Process review
    scheduler.process_mcq_review(
        review_id=review_id,
        is_correct=True,
        selected_option=2,
        duration_ms=4500
    )

    # Check history was recorded
    from japanese_cli.database import get_cursor

    with get_cursor(db_path) as cursor:
        cursor.execute(
            "SELECT * FROM mcq_review_history WHERE mcq_review_id = ?", (review_id,)
        )
        history = cursor.fetchall()

    assert len(history) == 1
    assert history[0]["selected_option"] == 2
    assert history[0]["is_correct"] == 1  # SQLite stores as integer
    assert history[0]["duration_ms"] == 4500


def test_process_mcq_review_invalid_id(clean_db):
    """Test processing MCQ review with invalid ID raises error."""
    scheduler = MCQReviewScheduler(db_path=clean_db)

    with pytest.raises(ValueError, match="MCQ review with id 999 not found"):
        scheduler.process_mcq_review(
            review_id=999,
            is_correct=True,
            selected_option=0
        )


def test_process_mcq_review_invalid_option(db_with_vocabulary):
    """Test processing MCQ review with invalid selected_option raises error."""
    db_path, vocab_id = db_with_vocabulary

    scheduler = MCQReviewScheduler(db_path=db_path)
    review_id = scheduler.create_mcq_review(vocab_id, ItemType.VOCAB)

    # Test invalid options
    with pytest.raises(ValueError, match="selected_option must be 0-3"):
        scheduler.process_mcq_review(
            review_id=review_id,
            is_correct=True,
            selected_option=4
        )

    with pytest.raises(ValueError, match="selected_option must be 0-3"):
        scheduler.process_mcq_review(
            review_id=review_id,
            is_correct=True,
            selected_option=-1
        )


def test_process_mcq_review_with_duration(db_with_vocabulary):
    """Test that duration_ms is properly recorded in history."""
    db_path, vocab_id = db_with_vocabulary

    scheduler = MCQReviewScheduler(db_path=db_path)
    review_id = scheduler.create_mcq_review(vocab_id, ItemType.VOCAB)

    # Process with specific duration
    scheduler.process_mcq_review(
        review_id=review_id,
        is_correct=True,
        selected_option=1,
        duration_ms=7500
    )

    # Verify duration in history
    from japanese_cli.database import get_cursor

    with get_cursor(db_path) as cursor:
        cursor.execute(
            "SELECT duration_ms FROM mcq_review_history WHERE mcq_review_id = ?",
            (review_id,)
        )
        row = cursor.fetchone()

    assert row["duration_ms"] == 7500


# ============================================================================
# get_mcq_review_count Tests
# ============================================================================


def test_get_mcq_review_count_empty(clean_db):
    """Test getting MCQ review count when empty."""
    scheduler = MCQReviewScheduler(db_path=clean_db)
    count = scheduler.get_mcq_review_count()

    assert count == 0


def test_get_mcq_review_count(db_with_vocabulary):
    """Test getting total MCQ review count."""
    db_path, vocab_id = db_with_vocabulary

    scheduler = MCQReviewScheduler(db_path=db_path)
    scheduler.create_mcq_review(vocab_id, ItemType.VOCAB)

    count = scheduler.get_mcq_review_count()

    assert count == 1


def test_get_mcq_review_count_with_filters(clean_db):
    """Test getting MCQ review count with filters."""
    # Add N5 and N4 vocabulary
    vocab_n5 = add_vocabulary(
        word="n5word",
        reading="えぬご",
        meanings={"en": ["n5"]},
        jlpt_level="n5",
        db_path=clean_db,
    )
    vocab_n4 = add_vocabulary(
        word="n4word",
        reading="えぬよん",
        meanings={"en": ["n4"]},
        jlpt_level="n4",
        db_path=clean_db,
    )
    kanji_n5 = add_kanji(
        character="五",
        on_readings=["ゴ"],
        kun_readings=["いつ"],
        meanings={"en": ["five"]},
        jlpt_level="n5",
        db_path=clean_db,
    )

    # Create MCQ reviews
    scheduler = MCQReviewScheduler(db_path=clean_db)
    scheduler.create_mcq_review(vocab_n5, ItemType.VOCAB)
    scheduler.create_mcq_review(vocab_n4, ItemType.VOCAB)
    scheduler.create_mcq_review(kanji_n5, ItemType.KANJI)

    # Test counts
    assert scheduler.get_mcq_review_count() == 3
    assert scheduler.get_mcq_review_count(jlpt_level="n5") == 2
    assert scheduler.get_mcq_review_count(jlpt_level="n4") == 1
    assert scheduler.get_mcq_review_count(item_type=ItemType.VOCAB) == 2
    assert scheduler.get_mcq_review_count(item_type=ItemType.KANJI) == 1
    assert scheduler.get_mcq_review_count(jlpt_level="n5", item_type=ItemType.VOCAB) == 1


# ============================================================================
# Integration Tests
# ============================================================================


def test_full_mcq_workflow(clean_db):
    """Test complete MCQ review workflow from creation to multiple reviews."""
    # Add vocabulary
    vocab_id = add_vocabulary(
        word="勉強",
        reading="べんきょう",
        meanings={"vi": ["học tập"], "en": ["study"]},
        jlpt_level="n5",
        db_path=clean_db,
    )

    # Create scheduler
    scheduler = MCQReviewScheduler(db_path=clean_db)

    # Create MCQ review
    review_id = scheduler.create_mcq_review(vocab_id, ItemType.VOCAB)

    # Verify it's due
    due_mcqs = scheduler.get_due_mcqs()
    assert len(due_mcqs) == 1

    # Review with correct answer
    updated_review = scheduler.process_mcq_review(
        review_id=review_id,
        is_correct=True,
        selected_option=3,
        duration_ms=3000
    )
    assert updated_review.review_count == 1

    # Make it due again
    from japanese_cli.database import get_cursor

    with get_cursor(clean_db) as cursor:
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        cursor.execute(
            "UPDATE mcq_reviews SET due_date = ? WHERE id = ?",
            (past_time.isoformat(), review_id),
        )

    # Review again with incorrect answer
    updated_review = scheduler.process_mcq_review(
        review_id=review_id,
        is_correct=False,
        selected_option=1,
        duration_ms=2500
    )
    assert updated_review.review_count == 2

    # Verify history has both entries
    with get_cursor(clean_db) as cursor:
        cursor.execute(
            "SELECT * FROM mcq_review_history WHERE mcq_review_id = ? ORDER BY reviewed_at",
            (review_id,)
        )
        history = cursor.fetchall()

    assert len(history) == 2
    assert history[0]["is_correct"] == 1  # First was correct
    assert history[0]["selected_option"] == 3
    assert history[1]["is_correct"] == 0  # Second was incorrect
    assert history[1]["selected_option"] == 1


def test_mixed_vocab_kanji_mcqs(clean_db):
    """Test managing both vocabulary and kanji MCQ reviews."""
    # Add items
    vocab_id = add_vocabulary(
        word="言葉",
        reading="ことば",
        meanings={"vi": ["từ ngữ"], "en": ["word"]},
        db_path=clean_db,
    )
    kanji_id = add_kanji(
        character="言",
        on_readings=["ゲン", "ゴン"],
        kun_readings=["い.う", "こと"],
        meanings={"vi": ["ngôn"], "en": ["say"]},
        db_path=clean_db,
    )

    # Create MCQ reviews
    scheduler = MCQReviewScheduler(db_path=clean_db)
    vocab_review_id = scheduler.create_mcq_review(vocab_id, ItemType.VOCAB)
    kanji_review_id = scheduler.create_mcq_review(kanji_id, ItemType.KANJI)

    # Get all due MCQ reviews
    due_mcqs = scheduler.get_due_mcqs()
    assert len(due_mcqs) == 2

    # Process both (vocab correct, kanji incorrect)
    scheduler.process_mcq_review(
        review_id=vocab_review_id,
        is_correct=True,
        selected_option=2
    )
    scheduler.process_mcq_review(
        review_id=kanji_review_id,
        is_correct=False,
        selected_option=0
    )

    # Verify history for both
    from japanese_cli.database import get_cursor

    with get_cursor(clean_db) as cursor:
        cursor.execute("SELECT COUNT(*) FROM mcq_review_history")
        count = cursor.fetchone()[0]

    assert count == 2
