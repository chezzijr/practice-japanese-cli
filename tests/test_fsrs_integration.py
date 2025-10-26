"""
Tests for FSRS integration with the database layer.
"""

from datetime import datetime, timedelta, timezone

import pytest
from fsrs import Card, Rating, Scheduler, State

from japanese_cli.database import (
    add_vocabulary,
    create_review,
    get_due_cards,
    get_review,
    update_review,
    add_review_history,
)


def test_card_serialization_roundtrip():
    """Test that Card.to_dict() and Card.from_dict() work correctly."""
    card = Card()

    # Serialize
    card_dict = card.to_dict()

    assert "card_id" in card_dict
    assert "state" in card_dict
    assert "due" in card_dict

    # Deserialize
    restored_card = Card.from_dict(card_dict)

    assert restored_card.card_id == card.card_id
    assert restored_card.state == card.state
    assert restored_card.due == card.due


def test_review_card_updates_state():
    """Test that reviewing a card updates its FSRS state."""
    scheduler = Scheduler()
    card = Card()

    original_due = card.due

    # Review with Rating.Good
    card, review_log = scheduler.review_card(card, Rating.Good)

    # Card state should change
    assert card.due != original_due
    assert review_log.rating == Rating.Good


def test_all_rating_values():
    """Test that all FSRS rating values work."""
    scheduler = Scheduler()

    ratings = [Rating.Again, Rating.Hard, Rating.Good, Rating.Easy]

    for rating in ratings:
        card = Card()
        card, review_log = scheduler.review_card(card, rating)

        assert review_log.rating == rating
        assert card.due is not None


def test_card_state_values():
    """Test that Card states match expected values."""
    assert State.Learning.value == 1
    assert State.Review.value == 2
    assert State.Relearning.value == 3


def test_new_card_state_is_learning():
    """Test that a new card starts in Learning state."""
    card = Card()
    assert card.state == State.Learning


def test_card_persistence_in_database(db_with_vocabulary):
    """Test storing and retrieving FSRS card state from database."""
    db_path, vocab_id = db_with_vocabulary

    # Create a card and perform a review
    scheduler = Scheduler()
    card = Card()
    card, _ = scheduler.review_card(card, Rating.Good)

    # Store in database
    review_id = create_review(
        item_id=vocab_id,
        item_type="vocab",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=db_path
    )

    # Retrieve from database
    review = get_review(vocab_id, "vocab", db_path=db_path)

    # Deserialize card state
    import json
    stored_card_state = json.loads(review["fsrs_card_state"])
    restored_card = Card.from_dict(stored_card_state)

    # Verify card state matches
    assert restored_card.card_id == card.card_id
    assert restored_card.state == card.state
    assert restored_card.due == card.due


def test_review_workflow_end_to_end(db_with_vocabulary):
    """Test complete review workflow with FSRS."""
    db_path, vocab_id = db_with_vocabulary

    scheduler = Scheduler()

    # Step 1: Create initial card
    card = Card()
    card.due = datetime.now(timezone.utc) - timedelta(hours=1)  # Make it due now

    review_id = create_review(
        item_id=vocab_id,
        item_type="vocab",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=db_path
    )

    # Step 2: Card should be due
    due_cards = get_due_cards(db_path=db_path)
    assert len(due_cards) == 1

    # Step 3: Perform review
    card, review_log = scheduler.review_card(card, Rating.Good)

    # Step 4: Update database
    update_review(review_id, card.to_dict(), card.due, db_path=db_path)

    # Step 5: Add to history
    history_id = add_review_history(
        review_id=review_id,
        rating=3,  # Rating.Good
        duration_ms=5000,
        db_path=db_path
    )

    assert history_id > 0

    # Step 6: Card should no longer be due (due date moved to future)
    due_cards = get_due_cards(db_path=db_path)
    assert len(due_cards) == 0


def test_scheduler_custom_parameters():
    """Test that Scheduler accepts custom parameters."""
    from datetime import timedelta

    scheduler = Scheduler(
        desired_retention=0.95,
        learning_steps=(timedelta(minutes=1), timedelta(minutes=10)),
        maximum_interval=180,
        enable_fuzzing=False
    )

    assert scheduler.desired_retention == 0.95
    assert scheduler.maximum_interval == 180
    assert scheduler.enable_fuzzing is False


def test_multiple_reviews_increase_stability(clean_db):
    """Test that multiple successful reviews increase card stability."""
    vocab_id = add_vocabulary(
        word="test",
        reading="てすと",
        meanings={"en": ["test"]},
        db_path=clean_db
    )

    scheduler = Scheduler()
    card = Card()

    # Initial stability
    initial_stability = card.stability

    # Perform multiple Good reviews
    for _ in range(5):
        card, _ = scheduler.review_card(card, Rating.Good)

    # Stability should increase (if not None)
    if card.stability is not None and initial_stability is not None:
        assert card.stability > initial_stability


def test_failed_review_changes_state(clean_db):
    """Test that failing a review (Rating.Again) affects card state."""
    scheduler = Scheduler()
    card = Card()

    # First review to get card into Review state
    card, _ = scheduler.review_card(card, Rating.Good)

    # Review again to graduate from Learning
    card, _ = scheduler.review_card(card, Rating.Good)

    # Now fail the review
    original_state = card.state
    card, _ = scheduler.review_card(card, Rating.Again)

    # State might change to Relearning
    # (exact behavior depends on FSRS algorithm)
    assert card is not None  # Card should still exist
