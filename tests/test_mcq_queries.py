"""
Tests for MCQ database queries.
"""

import pytest
from datetime import datetime, timezone, timedelta
from fsrs import Card

from japanese_cli.database.mcq_queries import (
    create_mcq_review,
    get_mcq_review,
    get_mcq_review_by_id,
    update_mcq_review,
    get_due_mcq_cards,
    delete_mcq_review,
    add_mcq_review_history,
    get_mcq_review_history,
    get_mcq_stats
)


# ============================================================================
# MCQ Review Queries Tests
# ============================================================================

def test_create_mcq_review(db_with_vocabulary):
    """Test creating a new MCQ review entry."""
    db_path, vocab_id = db_with_vocabulary

    card = Card()
    card_state = card.to_dict()

    review_id = create_mcq_review(
        item_id=vocab_id,
        item_type="vocab",
        fsrs_card_state=card_state,
        due_date=card.due,
        db_path=db_path
    )

    assert review_id > 0


def test_get_mcq_review(db_with_vocabulary):
    """Test retrieving an MCQ review by item."""
    db_path, vocab_id = db_with_vocabulary

    # Create MCQ review
    card = Card()
    review_id = create_mcq_review(
        item_id=vocab_id,
        item_type="vocab",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=db_path
    )

    # Retrieve it
    review = get_mcq_review(item_id=vocab_id, item_type="vocab", db_path=db_path)

    assert review is not None
    assert review['id'] == review_id
    assert review['item_id'] == vocab_id
    assert review['item_type'] == 'vocab'
    assert review['review_count'] == 0


def test_get_mcq_review_nonexistent(clean_db):
    """Test getting non-existent MCQ review returns None."""
    review = get_mcq_review(item_id=999, item_type="vocab", db_path=clean_db)
    assert review is None


def test_get_mcq_review_by_id(db_with_vocabulary):
    """Test retrieving MCQ review by ID."""
    db_path, vocab_id = db_with_vocabulary

    # Create MCQ review
    card = Card()
    review_id = create_mcq_review(
        item_id=vocab_id,
        item_type="vocab",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=db_path
    )

    # Retrieve by ID
    review = get_mcq_review_by_id(review_id=review_id, db_path=db_path)

    assert review is not None
    assert review['id'] == review_id
    assert review['item_id'] == vocab_id


def test_update_mcq_review(db_with_vocabulary):
    """Test updating MCQ review state."""
    from fsrs import Scheduler, Rating

    db_path, vocab_id = db_with_vocabulary

    # Create MCQ review
    card = Card()
    review_id = create_mcq_review(
        item_id=vocab_id,
        item_type="vocab",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=db_path
    )

    # Update after review
    scheduler = Scheduler()
    updated_card, _ = scheduler.review_card(card, Rating.Good)

    success = update_mcq_review(
        review_id=review_id,
        fsrs_card_state=updated_card.to_dict(),
        due_date=updated_card.due,
        db_path=db_path
    )

    assert success is True

    # Verify update
    review = get_mcq_review_by_id(review_id, db_path)
    assert review['review_count'] == 1
    assert review['last_reviewed'] is not None


def test_update_mcq_review_nonexistent(clean_db):
    """Test updating non-existent MCQ review returns False."""
    card = Card()
    success = update_mcq_review(
        review_id=999,
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=clean_db
    )
    assert success is False


def test_delete_mcq_review(db_with_vocabulary):
    """Test deleting an MCQ review."""
    db_path, vocab_id = db_with_vocabulary

    # Create MCQ review
    card = Card()
    create_mcq_review(
        item_id=vocab_id,
        item_type="vocab",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=db_path
    )

    # Delete it
    success = delete_mcq_review(item_id=vocab_id, item_type="vocab", db_path=db_path)
    assert success is True

    # Verify deletion
    review = get_mcq_review(item_id=vocab_id, item_type="vocab", db_path=db_path)
    assert review is None


def test_delete_mcq_review_nonexistent(clean_db):
    """Test deleting non-existent MCQ review returns False."""
    success = delete_mcq_review(item_id=999, item_type="vocab", db_path=clean_db)
    assert success is False


# ============================================================================
# Get Due MCQ Cards Tests
# ============================================================================

def test_get_due_mcq_cards_vocab(db_with_vocabulary):
    """Test getting due MCQ cards for vocabulary."""
    db_path, vocab_id = db_with_vocabulary

    # Create MCQ review with due date in the past
    card = Card()
    card.due = datetime.now(timezone.utc) - timedelta(hours=1)
    create_mcq_review(
        item_id=vocab_id,
        item_type="vocab",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=db_path
    )

    # Get due cards
    due_cards = get_due_mcq_cards(item_type="vocab", db_path=db_path)

    assert len(due_cards) == 1
    assert due_cards[0]['item_id'] == vocab_id
    assert due_cards[0]['content'] == "単語"


def test_get_due_mcq_cards_kanji(db_with_kanji):
    """Test getting due MCQ cards for kanji."""
    db_path, kanji_id = db_with_kanji

    # Create MCQ review with due date in the past
    card = Card()
    card.due = datetime.now(timezone.utc) - timedelta(hours=1)
    create_mcq_review(
        item_id=kanji_id,
        item_type="kanji",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=db_path
    )

    # Get due cards
    due_cards = get_due_mcq_cards(item_type="kanji", db_path=db_path)

    assert len(due_cards) == 1
    assert due_cards[0]['item_id'] == kanji_id
    assert due_cards[0]['content'] == "語"


def test_get_due_mcq_cards_both_types(db_with_vocabulary, sample_kanji):
    """Test getting due MCQ cards for both vocab and kanji."""
    from japanese_cli.database import add_kanji

    vocab_db_path, vocab_id = db_with_vocabulary

    # Add kanji to same database
    kanji_id = add_kanji(**sample_kanji, db_path=vocab_db_path)

    # Create MCQ reviews for both
    card = Card()
    card.due = datetime.now(timezone.utc) - timedelta(hours=1)

    create_mcq_review(
        item_id=vocab_id,
        item_type="vocab",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=vocab_db_path
    )

    create_mcq_review(
        item_id=kanji_id,
        item_type="kanji",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=vocab_db_path
    )

    # Get all due cards (no type filter)
    due_cards = get_due_mcq_cards(db_path=vocab_db_path)

    assert len(due_cards) == 2


def test_get_due_mcq_cards_jlpt_filter(db_with_vocabulary, sample_vocabulary):
    """Test filtering due MCQ cards by JLPT level."""
    from japanese_cli.database import add_vocabulary

    db_path, n5_vocab_id = db_with_vocabulary

    # Add N4 vocabulary
    n4_vocab = sample_vocabulary.copy()
    n4_vocab['word'] = "新しい"
    n4_vocab['reading'] = "あたらしい"
    n4_vocab['jlpt_level'] = "n4"
    n4_vocab_id = add_vocabulary(**n4_vocab, db_path=db_path)

    # Create MCQ reviews for both
    card = Card()
    card.due = datetime.now(timezone.utc) - timedelta(hours=1)

    for vocab_id in [n5_vocab_id, n4_vocab_id]:
        create_mcq_review(
            item_id=vocab_id,
            item_type="vocab",
            fsrs_card_state=card.to_dict(),
            due_date=card.due,
            db_path=db_path
        )

    # Filter by N5
    n5_cards = get_due_mcq_cards(jlpt_level="n5", db_path=db_path)
    assert len(n5_cards) == 1
    assert n5_cards[0]['item_id'] == n5_vocab_id

    # Filter by N4
    n4_cards = get_due_mcq_cards(jlpt_level="n4", db_path=db_path)
    assert len(n4_cards) == 1
    assert n4_cards[0]['item_id'] == n4_vocab_id


def test_get_due_mcq_cards_limit(db_with_vocabulary, sample_vocabulary):
    """Test limiting number of due MCQ cards."""
    from japanese_cli.database import add_vocabulary

    db_path, vocab_id1 = db_with_vocabulary

    # Add more vocabulary
    vocab2 = sample_vocabulary.copy()
    vocab2['word'] = "文法"
    vocab_id2 = add_vocabulary(**vocab2, db_path=db_path)

    # Create MCQ reviews
    card = Card()
    card.due = datetime.now(timezone.utc) - timedelta(hours=1)

    for vocab_id in [vocab_id1, vocab_id2]:
        create_mcq_review(
            item_id=vocab_id,
            item_type="vocab",
            fsrs_card_state=card.to_dict(),
            due_date=card.due,
            db_path=db_path
        )

    # Get with limit
    due_cards = get_due_mcq_cards(limit=1, db_path=db_path)
    assert len(due_cards) == 1


def test_get_due_mcq_cards_not_due_yet(db_with_vocabulary):
    """Test that MCQ cards not yet due are not returned."""
    db_path, vocab_id = db_with_vocabulary

    # Create MCQ review with future due date
    card = Card()
    card.due = datetime.now(timezone.utc) + timedelta(days=1)
    create_mcq_review(
        item_id=vocab_id,
        item_type="vocab",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=db_path
    )

    # Should not return any cards
    due_cards = get_due_mcq_cards(db_path=db_path)
    assert len(due_cards) == 0


# ============================================================================
# MCQ Review History Tests
# ============================================================================

def test_add_mcq_review_history(db_with_vocabulary):
    """Test adding MCQ review history entry."""
    db_path, vocab_id = db_with_vocabulary

    # Create MCQ review
    card = Card()
    review_id = create_mcq_review(
        item_id=vocab_id,
        item_type="vocab",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=db_path
    )

    # Add history entry
    history_id = add_mcq_review_history(
        mcq_review_id=review_id,
        selected_option=2,
        is_correct=True,
        duration_ms=3000,
        db_path=db_path
    )

    assert history_id > 0


def test_get_mcq_review_history(db_with_vocabulary):
    """Test retrieving MCQ review history."""
    db_path, vocab_id = db_with_vocabulary

    # Create MCQ review
    card = Card()
    review_id = create_mcq_review(
        item_id=vocab_id,
        item_type="vocab",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=db_path
    )

    # Add multiple history entries
    for i in range(3):
        add_mcq_review_history(
            mcq_review_id=review_id,
            selected_option=i,
            is_correct=(i == 0),
            duration_ms=2000 + i * 500,
            db_path=db_path
        )

    # Get history
    history = get_mcq_review_history(mcq_review_id=review_id, db_path=db_path)

    assert len(history) == 3
    # Verify all entries are present (ordered by most recent first)
    selected_options = {h['selected_option'] for h in history}
    assert selected_options == {0, 1, 2}


def test_get_mcq_review_history_with_limit(db_with_vocabulary):
    """Test limiting MCQ review history results."""
    db_path, vocab_id = db_with_vocabulary

    # Create MCQ review
    card = Card()
    review_id = create_mcq_review(
        item_id=vocab_id,
        item_type="vocab",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=db_path
    )

    # Add multiple history entries
    for i in range(5):
        add_mcq_review_history(
            mcq_review_id=review_id,
            selected_option=0,
            is_correct=True,
            db_path=db_path
        )

    # Get with limit
    history = get_mcq_review_history(mcq_review_id=review_id, limit=2, db_path=db_path)
    assert len(history) == 2


# ============================================================================
# MCQ Statistics Tests
# ============================================================================

def test_get_mcq_stats(db_with_vocabulary):
    """Test getting MCQ statistics."""
    db_path, vocab_id = db_with_vocabulary

    # Create MCQ review
    card = Card()
    review_id = create_mcq_review(
        item_id=vocab_id,
        item_type="vocab",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=db_path
    )

    # Add history entries (3 correct, 2 incorrect)
    for i in range(5):
        add_mcq_review_history(
            mcq_review_id=review_id,
            selected_option=0,
            is_correct=(i < 3),  # First 3 correct
            db_path=db_path
        )

    # Get stats
    stats = get_mcq_stats(db_path=db_path)

    assert stats['total_reviews'] == 5
    assert stats['correct_count'] == 3
    assert stats['incorrect_count'] == 2
    assert stats['accuracy_rate'] == 60.0


def test_get_mcq_stats_by_item_type(db_with_vocabulary, sample_kanji):
    """Test MCQ stats filtered by item type."""
    from japanese_cli.database import add_kanji

    db_path, vocab_id = db_with_vocabulary
    kanji_id = add_kanji(**sample_kanji, db_path=db_path)

    # Create MCQ reviews
    card = Card()
    vocab_review_id = create_mcq_review(
        item_id=vocab_id,
        item_type="vocab",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=db_path
    )

    kanji_review_id = create_mcq_review(
        item_id=kanji_id,
        item_type="kanji",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=db_path
    )

    # Add history
    add_mcq_review_history(vocab_review_id, 0, True, db_path=db_path)
    add_mcq_review_history(kanji_review_id, 0, False, db_path=db_path)

    # Get vocab stats
    vocab_stats = get_mcq_stats(item_type="vocab", db_path=db_path)
    assert vocab_stats['total_reviews'] == 1
    assert vocab_stats['accuracy_rate'] == 100.0

    # Get kanji stats
    kanji_stats = get_mcq_stats(item_type="kanji", db_path=db_path)
    assert kanji_stats['total_reviews'] == 1
    assert kanji_stats['accuracy_rate'] == 0.0


def test_get_mcq_stats_empty(clean_db):
    """Test MCQ stats with no review history."""
    stats = get_mcq_stats(db_path=clean_db)

    assert stats['total_reviews'] == 0
    assert stats['correct_count'] == 0
    assert stats['incorrect_count'] == 0
    assert stats['accuracy_rate'] == 0.0
