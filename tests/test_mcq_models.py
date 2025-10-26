"""
Tests for MCQ models (MCQQuestion, MCQReview, MCQReviewHistory).
"""

import json
import pytest
from datetime import datetime, timezone

from japanese_cli.models.mcq import MCQQuestion, MCQReview, MCQReviewHistory
from japanese_cli.models.review import ItemType
from fsrs import Card


# ============================================================================
# MCQQuestion Tests
# ============================================================================

def test_mcq_question_creation():
    """Test creating a valid MCQ question."""
    question = MCQQuestion(
        item_id=1,
        item_type=ItemType.VOCAB,
        question_text="What is the meaning of '単語'?",
        options=["word", "sentence", "grammar", "reading"],
        correct_index=0,
        jlpt_level="n5",
        explanation="単語 (たんご) means 'word' in Vietnamese: từ vựng"
    )

    assert question.item_id == 1
    assert question.item_type == ItemType.VOCAB
    assert question.question_text == "What is the meaning of '単語'?"
    assert len(question.options) == 4
    assert question.correct_index == 0
    assert question.jlpt_level == "n5"
    assert question.explanation is not None


def test_mcq_question_invalid_options_count():
    """Test that MCQ question requires exactly 4 options."""
    with pytest.raises(ValueError, match="exactly 4 options"):
        MCQQuestion(
            item_id=1,
            item_type=ItemType.VOCAB,
            question_text="Test question",
            options=["option1", "option2"],  # Only 2 options
            correct_index=0
        )


def test_mcq_question_invalid_correct_index():
    """Test that correct_index must be 0-3."""
    with pytest.raises(ValueError, match="correct_index must be 0-3"):
        MCQQuestion(
            item_id=1,
            item_type=ItemType.VOCAB,
            question_text="Test question",
            options=["a", "b", "c", "d"],
            correct_index=5  # Out of range
        )


def test_mcq_question_is_correct():
    """Test checking if selected answer is correct."""
    question = MCQQuestion(
        item_id=1,
        item_type=ItemType.KANJI,
        question_text="What is this kanji?",
        options=["語", "言", "話", "詰"],
        correct_index=0
    )

    assert question.is_correct(0) is True
    assert question.is_correct(1) is False
    assert question.is_correct(2) is False
    assert question.is_correct(3) is False


def test_mcq_question_get_correct_answer():
    """Test getting the correct answer text."""
    question = MCQQuestion(
        item_id=1,
        item_type=ItemType.VOCAB,
        question_text="Select the word",
        options=["単語", "文法", "読み", "書き"],
        correct_index=2
    )

    assert question.get_correct_answer() == "読み"


# ============================================================================
# MCQReview Tests
# ============================================================================

def test_mcq_review_creation():
    """Test creating a new MCQ review with FSRS card."""
    card = Card()
    card_state = card.to_dict()

    review = MCQReview(
        item_id=1,
        item_type=ItemType.VOCAB,
        fsrs_card_state=card_state,
        due_date=card.due
    )

    assert review.id is None  # Not yet saved to DB
    assert review.item_id == 1
    assert review.item_type == ItemType.VOCAB
    assert review.fsrs_card_state == card_state
    assert review.review_count == 0
    assert review.last_reviewed is None


def test_mcq_review_create_new():
    """Test creating a new MCQ review using create_new class method."""
    review = MCQReview.create_new(item_id=42, item_type=ItemType.KANJI)

    assert review.item_id == 42
    assert review.item_type == ItemType.KANJI
    assert review.review_count == 0
    assert review.last_reviewed is None
    assert 'due' in review.fsrs_card_state
    assert isinstance(review.due_date, datetime)


def test_mcq_review_get_card():
    """Test reconstructing FSRS Card from stored state."""
    review = MCQReview.create_new(item_id=1, item_type=ItemType.VOCAB)
    card = review.get_card()

    assert isinstance(card, Card)
    assert card.to_dict() == review.fsrs_card_state


def test_mcq_review_update_from_card():
    """Test updating review state from FSRS Card."""
    from fsrs import Scheduler, Rating

    review = MCQReview.create_new(item_id=1, item_type=ItemType.VOCAB)
    original_state = review.fsrs_card_state.copy()

    # Simulate a review
    card = review.get_card()
    scheduler = Scheduler()
    updated_card, _ = scheduler.review_card(card, Rating.Good)

    # Update review from card
    review.update_from_card(updated_card)

    # State should be updated
    assert review.fsrs_card_state != original_state
    assert 'due' in review.fsrs_card_state


def test_mcq_review_to_db_dict():
    """Test converting MCQ review to database dictionary."""
    review = MCQReview.create_new(item_id=1, item_type=ItemType.VOCAB)
    db_dict = review.to_db_dict(exclude_id=True)

    assert 'id' not in db_dict
    assert db_dict['item_id'] == 1
    assert db_dict['item_type'] == 'vocab'  # Enum converted to string
    assert isinstance(db_dict['fsrs_card_state'], str)  # JSON string
    assert db_dict['review_count'] == 0

    # With ID
    review.id = 123
    db_dict_with_id = review.to_db_dict(exclude_id=False)
    assert db_dict_with_id['id'] == 123


def test_mcq_review_from_db_row():
    """Test creating MCQ review from database row."""
    db_row = {
        'id': 1,
        'item_id': 42,
        'item_type': 'kanji',
        'fsrs_card_state': json.dumps(Card().to_dict()),
        'due_date': datetime.now(timezone.utc).isoformat(),
        'last_reviewed': None,
        'review_count': 3,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'updated_at': datetime.now(timezone.utc).isoformat()
    }

    review = MCQReview.from_db_row(db_row)

    assert review.id == 1
    assert review.item_id == 42
    assert review.item_type == ItemType.KANJI
    assert isinstance(review.fsrs_card_state, dict)  # JSON parsed
    assert review.review_count == 3


def test_mcq_review_datetime_parsing():
    """Test parsing datetime fields from various formats."""
    # ISO string
    iso_str = "2024-10-26T10:00:00+00:00"
    db_row = {
        'id': 1,
        'item_id': 1,
        'item_type': 'vocab',
        'fsrs_card_state': json.dumps(Card().to_dict()),
        'due_date': iso_str,
        'last_reviewed': iso_str,
        'review_count': 0,
        'created_at': iso_str,
        'updated_at': iso_str
    }

    review = MCQReview.from_db_row(db_row)
    assert isinstance(review.due_date, datetime)
    assert isinstance(review.last_reviewed, datetime)


# ============================================================================
# MCQReviewHistory Tests
# ============================================================================

def test_mcq_review_history_creation():
    """Test creating MCQ review history entry."""
    history = MCQReviewHistory(
        mcq_review_id=1,
        selected_option=2,
        is_correct=True,
        duration_ms=3500
    )

    assert history.id is None  # Not yet saved
    assert history.mcq_review_id == 1
    assert history.selected_option == 2
    assert history.is_correct is True
    assert history.duration_ms == 3500
    assert isinstance(history.reviewed_at, datetime)


def test_mcq_review_history_validation():
    """Test MCQ review history field validation."""
    # Selected option must be 0-3
    with pytest.raises(Exception):  # Pydantic validation error
        MCQReviewHistory(
            mcq_review_id=1,
            selected_option=5,  # Invalid
            is_correct=False
        )


def test_mcq_review_history_to_db_dict():
    """Test converting MCQ review history to database dictionary."""
    history = MCQReviewHistory(
        mcq_review_id=1,
        selected_option=1,
        is_correct=False,
        duration_ms=2000
    )

    db_dict = history.to_db_dict(exclude_id=True)

    assert 'id' not in db_dict
    assert db_dict['mcq_review_id'] == 1
    assert db_dict['selected_option'] == 1
    assert db_dict['is_correct'] == 0  # Boolean to int for SQLite
    assert db_dict['duration_ms'] == 2000


def test_mcq_review_history_from_db_row():
    """Test creating MCQ review history from database row."""
    db_row = {
        'id': 123,
        'mcq_review_id': 5,
        'selected_option': 3,
        'is_correct': 1,  # SQLite integer
        'duration_ms': 4500,
        'reviewed_at': datetime.now(timezone.utc).isoformat()
    }

    history = MCQReviewHistory.from_db_row(db_row)

    assert history.id == 123
    assert history.mcq_review_id == 5
    assert history.selected_option == 3
    assert history.is_correct is True  # Converted to boolean
    assert history.duration_ms == 4500


def test_mcq_review_history_boolean_conversion():
    """Test boolean <-> integer conversion for SQLite."""
    # Test True -> 1
    history_correct = MCQReviewHistory(
        mcq_review_id=1,
        selected_option=0,
        is_correct=True
    )
    assert history_correct.to_db_dict()['is_correct'] == 1

    # Test False -> 0
    history_incorrect = MCQReviewHistory(
        mcq_review_id=1,
        selected_option=2,
        is_correct=False
    )
    assert history_incorrect.to_db_dict()['is_correct'] == 0

    # Test 0 -> False
    from_db_false = MCQReviewHistory.from_db_row({
        'mcq_review_id': 1,
        'selected_option': 1,
        'is_correct': 0,
        'reviewed_at': datetime.now(timezone.utc).isoformat()
    })
    assert from_db_false.is_correct is False

    # Test 1 -> True
    from_db_true = MCQReviewHistory.from_db_row({
        'mcq_review_id': 1,
        'selected_option': 1,
        'is_correct': 1,
        'reviewed_at': datetime.now(timezone.utc).isoformat()
    })
    assert from_db_true.is_correct is True
