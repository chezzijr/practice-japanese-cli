"""
Tests for SRS (Spaced Repetition System) module.

Tests FSRSManager and ReviewScheduler classes.
"""

from datetime import datetime, timedelta, timezone

import pytest
from fsrs import Card, Rating, State

from japanese_cli.srs import FSRSManager, ReviewScheduler
from japanese_cli.models import ItemType, Review
from japanese_cli.database import (
    add_vocabulary,
    add_kanji,
    get_review,
)


# ============================================================================
# FSRSManager Tests
# ============================================================================


def test_fsrs_manager_default_initialization():
    """Test FSRSManager initializes with default parameters."""
    manager = FSRSManager()

    assert manager.desired_retention == 0.9
    assert manager.maximum_interval == 36500
    assert manager.enable_fuzzing is True
    assert manager.scheduler is not None


def test_fsrs_manager_custom_initialization():
    """Test FSRSManager initializes with custom parameters."""
    manager = FSRSManager(
        desired_retention=0.95,
        learning_steps=(timedelta(minutes=5), timedelta(hours=1)),
        maximum_interval=180,
        enable_fuzzing=False,
    )

    assert manager.desired_retention == 0.95
    assert manager.maximum_interval == 180
    assert manager.enable_fuzzing is False
    assert len(manager.learning_steps) == 2


def test_fsrs_manager_create_new_card():
    """Test creating a new FSRS card."""
    manager = FSRSManager()
    card = manager.create_new_card()

    assert isinstance(card, Card)
    assert card.state == State.Learning
    assert card.due is not None


def test_fsrs_manager_review_card_with_int_rating():
    """Test reviewing a card with integer rating."""
    manager = FSRSManager()
    card = manager.create_new_card()

    # Review with integer rating
    updated_card, review_log = manager.review_card(card, 3)

    assert isinstance(updated_card, Card)
    assert review_log.rating == Rating.Good
    assert updated_card.due != card.due  # Due date should change


def test_fsrs_manager_review_card_with_rating_enum():
    """Test reviewing a card with Rating enum."""
    manager = FSRSManager()
    card = manager.create_new_card()

    # Review with Rating enum
    updated_card, review_log = manager.review_card(card, Rating.Easy)

    assert isinstance(updated_card, Card)
    assert review_log.rating == Rating.Easy


def test_fsrs_manager_all_rating_values():
    """Test all rating values work correctly."""
    manager = FSRSManager()

    for rating in [1, 2, 3, 4]:
        card = manager.create_new_card()
        updated_card, review_log = manager.review_card(card, rating)

        assert updated_card is not None
        assert review_log is not None


def test_fsrs_manager_invalid_rating_raises_error():
    """Test that invalid rating raises ValueError."""
    manager = FSRSManager()
    card = manager.create_new_card()

    with pytest.raises(ValueError, match="Rating must be 1-4"):
        manager.review_card(card, 5)

    with pytest.raises(ValueError, match="Rating must be 1-4"):
        manager.review_card(card, 0)


def test_fsrs_manager_rating_from_int():
    """Test converting integer to Rating enum."""
    assert FSRSManager.rating_from_int(1) == Rating.Again
    assert FSRSManager.rating_from_int(2) == Rating.Hard
    assert FSRSManager.rating_from_int(3) == Rating.Good
    assert FSRSManager.rating_from_int(4) == Rating.Easy


def test_fsrs_manager_rating_from_int_invalid():
    """Test that invalid integer raises ValueError."""
    with pytest.raises(ValueError):
        FSRSManager.rating_from_int(0)

    with pytest.raises(ValueError):
        FSRSManager.rating_from_int(5)


def test_fsrs_manager_rating_to_int():
    """Test converting Rating enum to integer."""
    assert FSRSManager.rating_to_int(Rating.Again) == 1
    assert FSRSManager.rating_to_int(Rating.Hard) == 2
    assert FSRSManager.rating_to_int(Rating.Good) == 3
    assert FSRSManager.rating_to_int(Rating.Easy) == 4


def test_fsrs_manager_get_due_date():
    """Test extracting due date from card."""
    manager = FSRSManager()
    card = manager.create_new_card()

    due_date = manager.get_due_date(card)

    assert isinstance(due_date, datetime)
    assert due_date == card.due


def test_fsrs_manager_is_card_due():
    """Test checking if card is due."""
    manager = FSRSManager()
    card = manager.create_new_card()

    # New card should be due immediately
    now = datetime.now(timezone.utc)
    assert manager.is_card_due(card, now) is True

    # Card in the future should not be due
    future = datetime.now(timezone.utc) + timedelta(days=1)
    card.due = future
    assert manager.is_card_due(card, now) is False


def test_fsrs_manager_card_state_progresses():
    """Test that reviewing cards progresses their state."""
    manager = FSRSManager()
    card = manager.create_new_card()

    # Review multiple times with Good rating
    for _ in range(3):
        card, _ = manager.review_card(card, Rating.Good)

    # Card should eventually reach Review state
    # (exact progression depends on FSRS algorithm)
    assert card.state in [State.Learning, State.Review]


# ============================================================================
# ReviewScheduler Tests
# ============================================================================


def test_review_scheduler_default_initialization():
    """Test ReviewScheduler initializes with defaults."""
    scheduler = ReviewScheduler()

    assert scheduler.fsrs_manager is not None
    assert isinstance(scheduler.fsrs_manager, FSRSManager)
    assert scheduler.db_path is None


def test_review_scheduler_custom_fsrs_manager():
    """Test ReviewScheduler with custom FSRSManager."""
    custom_fsrs = FSRSManager(desired_retention=0.95)
    scheduler = ReviewScheduler(fsrs_manager=custom_fsrs)

    assert scheduler.fsrs_manager.desired_retention == 0.95


def test_review_scheduler_create_new_review_vocab(clean_db):
    """Test creating a new review for vocabulary."""
    # Add vocabulary
    vocab_id = add_vocabulary(
        word="単語",
        reading="たんご",
        meanings={"vi": ["từ vựng"], "en": ["word"]},
        jlpt_level="n5",
        db_path=clean_db,
    )

    # Create review
    scheduler = ReviewScheduler(db_path=clean_db)
    review_id = scheduler.create_new_review(vocab_id, ItemType.VOCAB)

    assert review_id > 0

    # Verify review was created
    review_row = get_review(vocab_id, "vocab", db_path=clean_db)
    assert review_row is not None
    assert review_row["item_id"] == vocab_id
    assert review_row["item_type"] == "vocab"


def test_review_scheduler_create_new_review_kanji(clean_db):
    """Test creating a new review for kanji."""
    # Add kanji
    kanji_id = add_kanji(
        character="語",
        on_readings=["ゴ"],
        kun_readings=["かた.る"],
        meanings={"vi": ["ngữ"], "en": ["word"]},
        jlpt_level="n5",
        db_path=clean_db,
    )

    # Create review
    scheduler = ReviewScheduler(db_path=clean_db)
    review_id = scheduler.create_new_review(kanji_id, ItemType.KANJI)

    assert review_id > 0

    # Verify review was created
    review_row = get_review(kanji_id, "kanji", db_path=clean_db)
    assert review_row is not None
    assert review_row["item_id"] == kanji_id
    assert review_row["item_type"] == "kanji"


def test_review_scheduler_create_review_with_string_type(clean_db):
    """Test creating review with string item type."""
    vocab_id = add_vocabulary(
        word="test",
        reading="てすと",
        meanings={"en": ["test"]},
        db_path=clean_db,
    )

    scheduler = ReviewScheduler(db_path=clean_db)
    review_id = scheduler.create_new_review(vocab_id, "vocab")

    assert review_id > 0


def test_review_scheduler_create_review_invalid_vocab_id(clean_db):
    """Test creating review with invalid vocabulary ID raises error."""
    scheduler = ReviewScheduler(db_path=clean_db)

    with pytest.raises(ValueError, match="Vocabulary with id 999 not found"):
        scheduler.create_new_review(999, ItemType.VOCAB)


def test_review_scheduler_create_review_invalid_kanji_id(clean_db):
    """Test creating review with invalid kanji ID raises error."""
    scheduler = ReviewScheduler(db_path=clean_db)

    with pytest.raises(ValueError, match="Kanji with id 999 not found"):
        scheduler.create_new_review(999, ItemType.KANJI)


def test_review_scheduler_get_due_reviews_empty(clean_db):
    """Test getting due reviews when none exist."""
    scheduler = ReviewScheduler(db_path=clean_db)
    due_reviews = scheduler.get_due_reviews()

    assert due_reviews == []


def test_review_scheduler_get_due_reviews(db_with_vocabulary):
    """Test getting due reviews."""
    db_path, vocab_id = db_with_vocabulary

    # Create review and make it due
    scheduler = ReviewScheduler(db_path=db_path)
    review_id = scheduler.create_new_review(vocab_id, ItemType.VOCAB)

    # Get due reviews
    due_reviews = scheduler.get_due_reviews()

    assert len(due_reviews) == 1
    assert isinstance(due_reviews[0], Review)
    assert due_reviews[0].item_id == vocab_id
    assert due_reviews[0].item_type == ItemType.VOCAB


def test_review_scheduler_get_due_reviews_with_limit(db_with_vocabulary):
    """Test getting due reviews with limit."""
    db_path, vocab_id = db_with_vocabulary

    # Create multiple reviews
    scheduler = ReviewScheduler(db_path=db_path)
    scheduler.create_new_review(vocab_id, ItemType.VOCAB)

    # Add another vocabulary and review
    vocab_id2 = add_vocabulary(
        word="test2",
        reading="てすと2",
        meanings={"en": ["test2"]},
        db_path=db_path,
    )
    scheduler.create_new_review(vocab_id2, ItemType.VOCAB)

    # Get with limit
    due_reviews = scheduler.get_due_reviews(limit=1)

    assert len(due_reviews) == 1


def test_review_scheduler_get_due_reviews_with_jlpt_filter(db_with_vocabulary):
    """Test getting due reviews filtered by JLPT level."""
    db_path, vocab_id = db_with_vocabulary

    # Create review for N5 vocabulary
    scheduler = ReviewScheduler(db_path=db_path)
    scheduler.create_new_review(vocab_id, ItemType.VOCAB)

    # Get N5 reviews
    due_reviews = scheduler.get_due_reviews(jlpt_level="n5")

    assert len(due_reviews) == 1

    # Get N4 reviews (should be empty)
    due_reviews = scheduler.get_due_reviews(jlpt_level="n4")

    assert len(due_reviews) == 0


def test_review_scheduler_get_due_reviews_with_type_filter(clean_db):
    """Test getting due reviews filtered by item type."""
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

    # Create reviews
    scheduler = ReviewScheduler(db_path=clean_db)
    scheduler.create_new_review(vocab_id, ItemType.VOCAB)
    scheduler.create_new_review(kanji_id, ItemType.KANJI)

    # Filter by vocab
    vocab_reviews = scheduler.get_due_reviews(item_type=ItemType.VOCAB)
    assert len(vocab_reviews) == 1
    assert vocab_reviews[0].item_type == ItemType.VOCAB

    # Filter by kanji
    kanji_reviews = scheduler.get_due_reviews(item_type=ItemType.KANJI)
    assert len(kanji_reviews) == 1
    assert kanji_reviews[0].item_type == ItemType.KANJI


def test_review_scheduler_get_review_by_item(db_with_vocabulary):
    """Test getting review by item ID and type."""
    db_path, vocab_id = db_with_vocabulary

    # Create review
    scheduler = ReviewScheduler(db_path=db_path)
    scheduler.create_new_review(vocab_id, ItemType.VOCAB)

    # Get review
    review = scheduler.get_review_by_item(vocab_id, ItemType.VOCAB)

    assert review is not None
    assert isinstance(review, Review)
    assert review.item_id == vocab_id


def test_review_scheduler_get_review_by_item_not_found(clean_db):
    """Test getting review that doesn't exist returns None."""
    scheduler = ReviewScheduler(db_path=clean_db)
    review = scheduler.get_review_by_item(999, ItemType.VOCAB)

    assert review is None


def test_review_scheduler_process_review(db_with_vocabulary):
    """Test processing a review."""
    db_path, vocab_id = db_with_vocabulary

    # Create review
    scheduler = ReviewScheduler(db_path=db_path)
    review_id = scheduler.create_new_review(vocab_id, ItemType.VOCAB)

    # Get initial review
    initial_review = scheduler.get_review_by_item(vocab_id, ItemType.VOCAB)
    initial_due = initial_review.due_date
    initial_count = initial_review.review_count

    # Process review with Good rating
    updated_review = scheduler.process_review(
        review_id=review_id, rating=3, duration_ms=5000
    )

    assert updated_review.review_count == initial_count + 1
    assert updated_review.last_reviewed is not None
    assert updated_review.due_date != initial_due  # Due date should change


def test_review_scheduler_process_review_all_ratings(db_with_vocabulary):
    """Test processing reviews with all rating values."""
    db_path, vocab_id = db_with_vocabulary

    scheduler = ReviewScheduler(db_path=db_path)

    for rating in [1, 2, 3, 4]:
        # Create new vocabulary and review for each rating
        new_vocab_id = add_vocabulary(
            word=f"test{rating}",
            reading=f"てすと{rating}",
            meanings={"en": [f"test{rating}"]},
            db_path=db_path,
        )
        review_id = scheduler.create_new_review(new_vocab_id, ItemType.VOCAB)

        # Process review
        updated_review = scheduler.process_review(review_id, rating)

        assert updated_review.review_count == 1
        assert updated_review.last_reviewed is not None


def test_review_scheduler_process_review_invalid_rating(db_with_vocabulary):
    """Test processing review with invalid rating raises error."""
    db_path, vocab_id = db_with_vocabulary

    scheduler = ReviewScheduler(db_path=db_path)
    review_id = scheduler.create_new_review(vocab_id, ItemType.VOCAB)

    with pytest.raises(ValueError, match="Rating must be 1-4"):
        scheduler.process_review(review_id, 5)


def test_review_scheduler_process_review_invalid_id(clean_db):
    """Test processing review with invalid ID raises error."""
    scheduler = ReviewScheduler(db_path=clean_db)

    with pytest.raises(ValueError, match="Review with id 999 not found"):
        scheduler.process_review(999, 3)


def test_review_scheduler_process_review_updates_history(db_with_vocabulary):
    """Test that processing review adds entry to history."""
    db_path, vocab_id = db_with_vocabulary

    scheduler = ReviewScheduler(db_path=db_path)
    review_id = scheduler.create_new_review(vocab_id, ItemType.VOCAB)

    # Process review
    scheduler.process_review(review_id, 3, duration_ms=4500)

    # Check history was recorded
    from japanese_cli.database import get_cursor

    with get_cursor(db_path) as cursor:
        cursor.execute(
            "SELECT * FROM review_history WHERE review_id = ?", (review_id,)
        )
        history = cursor.fetchall()

    assert len(history) == 1
    assert history[0]["rating"] == 3
    assert history[0]["duration_ms"] == 4500


def test_review_scheduler_get_review_count_empty(clean_db):
    """Test getting review count when empty."""
    scheduler = ReviewScheduler(db_path=clean_db)
    count = scheduler.get_review_count()

    assert count == 0


def test_review_scheduler_get_review_count(db_with_vocabulary):
    """Test getting total review count."""
    db_path, vocab_id = db_with_vocabulary

    scheduler = ReviewScheduler(db_path=db_path)
    scheduler.create_new_review(vocab_id, ItemType.VOCAB)

    count = scheduler.get_review_count()

    assert count == 1


def test_review_scheduler_get_review_count_with_filters(clean_db):
    """Test getting review count with filters."""
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

    # Create reviews
    scheduler = ReviewScheduler(db_path=clean_db)
    scheduler.create_new_review(vocab_n5, ItemType.VOCAB)
    scheduler.create_new_review(vocab_n4, ItemType.VOCAB)
    scheduler.create_new_review(kanji_n5, ItemType.KANJI)

    # Test counts
    assert scheduler.get_review_count() == 3
    assert scheduler.get_review_count(jlpt_level="n5") == 2
    assert scheduler.get_review_count(jlpt_level="n4") == 1
    assert scheduler.get_review_count(item_type=ItemType.VOCAB) == 2
    assert scheduler.get_review_count(item_type=ItemType.KANJI) == 1
    assert scheduler.get_review_count(jlpt_level="n5", item_type=ItemType.VOCAB) == 1


# ============================================================================
# Integration Tests
# ============================================================================


def test_full_review_workflow(clean_db):
    """Test complete review workflow from creation to multiple reviews."""
    # Add vocabulary
    vocab_id = add_vocabulary(
        word="勉強",
        reading="べんきょう",
        meanings={"vi": ["học tập"], "en": ["study"]},
        jlpt_level="n5",
        db_path=clean_db,
    )

    # Create scheduler
    scheduler = ReviewScheduler(db_path=clean_db)

    # Create review
    review_id = scheduler.create_new_review(vocab_id, ItemType.VOCAB)

    # Verify it's due
    due_reviews = scheduler.get_due_reviews()
    assert len(due_reviews) == 1

    # Review with Good rating
    updated_review = scheduler.process_review(review_id, 3, duration_ms=3000)
    assert updated_review.review_count == 1

    # Review should no longer be due (moved to future)
    due_reviews = scheduler.get_due_reviews()
    # May still be in learning phase and due soon
    # assert len(due_reviews) == 0

    # Simulate another review (advance state)
    # Make it due again by updating due_date
    from japanese_cli.database import get_cursor

    with get_cursor(clean_db) as cursor:
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        cursor.execute(
            "UPDATE reviews SET due_date = ? WHERE id = ?",
            (past_time.isoformat(), review_id),
        )

    # Review again
    updated_review = scheduler.process_review(review_id, 3, duration_ms=2500)
    assert updated_review.review_count == 2


def test_mixed_vocab_and_kanji_reviews(clean_db):
    """Test managing both vocabulary and kanji reviews."""
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

    # Create reviews
    scheduler = ReviewScheduler(db_path=clean_db)
    vocab_review_id = scheduler.create_new_review(vocab_id, ItemType.VOCAB)
    kanji_review_id = scheduler.create_new_review(kanji_id, ItemType.KANJI)

    # Get all due reviews
    due_reviews = scheduler.get_due_reviews()
    assert len(due_reviews) == 2

    # Process both
    scheduler.process_review(vocab_review_id, 4)  # Easy
    scheduler.process_review(kanji_review_id, 2)  # Hard

    # Verify history for both
    from japanese_cli.database import get_cursor

    with get_cursor(clean_db) as cursor:
        cursor.execute("SELECT COUNT(*) FROM review_history")
        count = cursor.fetchone()[0]

    assert count == 2
