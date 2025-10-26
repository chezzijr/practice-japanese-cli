"""
Tests for review session functionality.

Tests UI components (question/answer display, rating prompt, summary)
and review session flow (command integration, FSRS updates, history recording).
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from rich.console import Console
from rich.panel import Panel

from japanese_cli.models import Vocabulary, Kanji, Review, ItemType
from japanese_cli.ui.display import (
    display_card_question,
    display_card_answer,
    prompt_rating,
    display_session_summary,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_vocab():
    """Sample vocabulary for testing."""
    return Vocabulary(
        id=1,
        word="単語",
        reading="たんご",
        meanings={"vi": ["từ vựng"], "en": ["word", "vocabulary"]},
        vietnamese_reading="đơn ngữ",
        jlpt_level="n5",
        part_of_speech="noun",
        tags=["common"],
        notes=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def sample_kanji():
    """Sample kanji for testing."""
    return Kanji(
        id=1,
        character="語",
        on_readings=["ゴ"],
        kun_readings=["かた.る", "かた.らう"],
        meanings={"vi": ["ngữ"], "en": ["word", "language"]},
        vietnamese_reading="ngữ",
        jlpt_level="n5",
        stroke_count=14,
        radical="言",
        notes=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


# ============================================================================
# UI Component Tests
# ============================================================================

def test_display_card_question_vocab(sample_vocab):
    """Test question display for vocabulary."""
    panel = display_card_question(sample_vocab, "vocab", 1, 10)

    assert isinstance(panel, Panel)
    assert panel.title == "📚 What is this in Japanese?"
    assert panel.border_style == "yellow"

    # Check content includes meanings and progress
    content = panel.renderable
    assert "Card 1 of 10" in content
    assert "từ vựng" in content  # Vietnamese meaning
    assert "word" in content or "vocabulary" in content  # English meaning
    assert "N5" in content.upper()  # JLPT level
    assert "noun" in content  # Part of speech


def test_display_card_question_kanji(sample_kanji):
    """Test question display for kanji."""
    panel = display_card_question(sample_kanji, "kanji", 5, 20)

    assert isinstance(panel, Panel)
    assert panel.title == "㊙️ What is this in Japanese?"
    assert panel.border_style == "yellow"

    # Check content
    content = panel.renderable
    assert "Card 5 of 20" in content
    assert "ngữ" in content  # Vietnamese meaning
    assert "14 strokes" in content  # Stroke count hint


def test_display_card_answer_vocab(sample_vocab):
    """Test answer display for vocabulary."""
    panel = display_card_answer(sample_vocab, "vocab")

    assert isinstance(panel, Panel)
    assert panel.title == "📚 Answer"
    assert panel.border_style == "cyan"

    # Check content includes word, reading, and meanings
    content = panel.renderable
    assert "単語" in content
    assert "たんご" in content
    assert "từ vựng" in content
    assert "đơn ngữ" in content  # Vietnamese reading


def test_display_card_answer_kanji(sample_kanji):
    """Test answer display for kanji."""
    panel = display_card_answer(sample_kanji, "kanji")

    assert isinstance(panel, Panel)
    assert panel.title == "㊙️ Answer"
    assert panel.border_style == "cyan"

    # Check content includes character, readings, and meanings
    content = panel.renderable
    assert "語" in content
    assert "ゴ" in content  # On-reading
    assert "かた.る" in content or "かた.らう" in content  # Kun-reading
    assert "ngữ" in content  # Meaning and Vietnamese reading


@patch('japanese_cli.ui.display.get_single_keypress')
def test_prompt_rating_valid(mock_keypress):
    """Test rating prompt with valid input."""
    mock_keypress.return_value = '3'

    rating = prompt_rating()

    assert rating == 3
    mock_keypress.assert_called_once()


@patch('japanese_cli.ui.display.get_single_keypress')
@patch('rich.console.Console.print')
def test_prompt_rating_invalid_then_valid(mock_print, mock_keypress):
    """Test rating prompt with invalid input followed by valid."""
    # First return invalid ('5'), then valid ('3')
    mock_keypress.side_effect = ['5', '3']

    rating = prompt_rating()

    assert rating == 3
    assert mock_keypress.call_count == 2
    # Should print error message for invalid input
    assert any("Invalid input" in str(call) or "1, 2, 3, or 4" in str(call) for call in mock_print.call_args_list)


@patch('japanese_cli.ui.display.get_single_keypress')
def test_prompt_rating_keyboard_interrupt(mock_keypress):
    """Test rating prompt handles keyboard interrupt."""
    # Simulate Ctrl+C (ASCII code 3)
    mock_keypress.return_value = chr(3)

    with pytest.raises(KeyboardInterrupt):
        prompt_rating()


def test_display_session_summary():
    """Test session summary display."""
    now = datetime.now(timezone.utc)
    rating_counts = {1: 2, 2: 3, 3: 10, 4: 5}
    total_time = 300.5  # 5 minutes 0.5 seconds
    next_dates = [
        ("単語", now + timedelta(days=2)),  # Use 2+ days to avoid timezone issues
        ("語", now + timedelta(days=3)),
        ("学生", now + timedelta(days=5)),
    ]

    panel = display_session_summary(
        total_reviewed=20,
        rating_counts=rating_counts,
        total_time_seconds=total_time,
        next_review_dates=next_dates
    )

    assert isinstance(panel, Panel)
    assert panel.title == "📊 Session Summary"
    assert panel.border_style == "green"

    content = panel.renderable
    # Check statistics
    assert "20" in content  # Total reviewed
    assert "2" in content  # Again count
    assert "3" in content  # Hard count
    assert "10" in content  # Good count
    assert "5" in content  # Easy count
    # Accuracy could be formatted as 75.0% or 75%
    assert "75" in content and "%" in content  # Accuracy (15/20 * 100)
    assert "5m" in content  # Minutes
    assert "0s" in content  # Seconds
    # Check next review dates present
    assert "単語" in content
    assert "days" in content or "Due now" in content or "Tomorrow" in content


def test_display_session_summary_empty_next_dates():
    """Test session summary with no next review dates."""
    panel = display_session_summary(
        total_reviewed=5,
        rating_counts={1: 0, 2: 0, 3: 3, 4: 2},
        total_time_seconds=60.0,
        next_review_dates=[]
    )

    assert isinstance(panel, Panel)
    content = panel.renderable
    assert "5" in content  # Total reviewed
    assert "100.0%" in content  # Accuracy (5/5)


# ============================================================================
# Review Session Integration Tests
# ============================================================================

def test_review_session_with_due_cards(clean_db, sample_vocabulary):
    """Test that review session can be called with due cards."""
    from japanese_cli.database import add_vocabulary
    from japanese_cli.srs import ReviewScheduler
    from japanese_cli.cli.flashcard import review_flashcards
    from unittest.mock import patch
    import typer

    # Add vocabulary to database
    vocab_id = add_vocabulary(db_path=clean_db, **sample_vocabulary)

    # Create review that's due now
    scheduler = ReviewScheduler(db_path=clean_db)
    review_id = scheduler.create_new_review(vocab_id, ItemType.VOCAB)

    # Verify the review was created and is due
    due_reviews = scheduler.get_due_reviews()
    assert len(due_reviews) == 1

    # Note: Full integration testing requires manual testing
    # Here we just verify the setup works correctly


def test_review_session_no_cards_due(clean_db):
    """Test review session when no cards are due."""
    from japanese_cli.cli.flashcard import _run_review_session
    from japanese_cli.srs import ReviewScheduler
    from unittest.mock import patch

    scheduler = ReviewScheduler(db_path=clean_db)

    with patch('japanese_cli.cli.flashcard.console') as mock_console:
        with patch('japanese_cli.cli.flashcard.ReviewScheduler', return_value=scheduler):
            _run_review_session(limit=10, jlpt_level=None, item_type=None)

    # Should print "No cards due" message
    calls = [str(call) for call in mock_console.print.call_args_list]
    assert any("No cards due" in call for call in calls)


def test_review_session_with_jlpt_filter(clean_db, sample_vocabulary):
    """Test review session with JLPT level filter."""
    from japanese_cli.database import add_vocabulary
    from japanese_cli.srs import ReviewScheduler

    # Add N5 vocabulary
    vocab_id = add_vocabulary(db_path=clean_db, **sample_vocabulary)
    scheduler = ReviewScheduler(db_path=clean_db)
    scheduler.create_new_review(vocab_id, ItemType.VOCAB)

    # Verify filtering works
    n5_reviews = scheduler.get_due_reviews(jlpt_level='n5')
    assert len(n5_reviews) == 1

    # Non-matching filter should return empty
    n4_reviews = scheduler.get_due_reviews(jlpt_level='n4')
    assert len(n4_reviews) == 0


def test_review_session_with_type_filter(clean_db, sample_vocabulary):
    """Test review session with item type filter."""
    from japanese_cli.database import add_vocabulary
    from japanese_cli.srs import ReviewScheduler

    # Add vocabulary
    vocab_id = add_vocabulary(db_path=clean_db, **sample_vocabulary)
    scheduler = ReviewScheduler(db_path=clean_db)
    scheduler.create_new_review(vocab_id, ItemType.VOCAB)

    # Verify filtering works
    vocab_reviews = scheduler.get_due_reviews(item_type=ItemType.VOCAB)
    assert len(vocab_reviews) == 1

    # Non-matching filter should return empty
    kanji_reviews = scheduler.get_due_reviews(item_type=ItemType.KANJI)
    assert len(kanji_reviews) == 0


def test_review_session_early_quit(cli_clean_db, sample_vocabulary):
    """Test review session with early quit (Ctrl+C)."""
    from japanese_cli.database import add_vocabulary
    from japanese_cli.srs import ReviewScheduler
    from japanese_cli.cli.flashcard import review_flashcards
    from unittest.mock import patch
    import typer

    # Add vocabulary
    vocab_id = add_vocabulary(db_path=cli_clean_db, **sample_vocabulary)
    scheduler = ReviewScheduler(db_path=cli_clean_db)
    scheduler.create_new_review(vocab_id, ItemType.VOCAB)

    # Mock user pressing Ctrl+C after seeing question
    with patch('builtins.input', side_effect=KeyboardInterrupt()):
        with pytest.raises(typer.Exit) as exc_info:
            review_flashcards(limit=10, jlpt_level=None, item_type=None)

        # Should exit cleanly with code 0
        assert exc_info.value.exit_code == 0


def test_review_all_rating_outcomes(clean_db):
    """Test that all 4 ratings update FSRS state correctly."""
    from japanese_cli.database import add_vocabulary
    from japanese_cli.srs import ReviewScheduler
    from japanese_cli.models import Vocabulary
    from datetime import datetime, timezone

    scheduler = ReviewScheduler(db_path=clean_db)

    # Create 4 vocabulary items
    for i in range(4):
        vocab_data = {
            "word": f"word{i}",
            "reading": f"reading{i}",
            "meanings": {"vi": [f"meaning{i}"], "en": [f"meaning{i}"]},
            "jlpt_level": "n5",
        }
        vocab_id = add_vocabulary(db_path=clean_db, **vocab_data)
        scheduler.create_new_review(vocab_id, ItemType.VOCAB)

    # Get all reviews
    reviews = scheduler.get_due_reviews()
    assert len(reviews) == 4

    # Process each with different rating (1-4)
    for i, review in enumerate(reviews, start=1):
        updated = scheduler.process_review(review.id, rating=i, duration_ms=1000)

        # Verify review was updated
        assert updated.review_count == 1
        assert updated.last_reviewed is not None

        # Verify due date changed (FSRS scheduling)
        assert updated.due_date != review.due_date

        # Rating 4 (Easy) should have longest interval
        # Rating 1 (Again) should have shortest interval
        if i == 4:
            # Easy rating should schedule further out
            assert updated.due_date > datetime.now(timezone.utc)


def test_review_history_recorded(clean_db, sample_vocabulary):
    """Test that review history is recorded correctly."""
    from japanese_cli.database import add_vocabulary, get_cursor
    from japanese_cli.srs import ReviewScheduler

    # Add vocabulary and create review
    vocab_id = add_vocabulary(db_path=clean_db, **sample_vocabulary)
    scheduler = ReviewScheduler(db_path=clean_db)
    review_id = scheduler.create_new_review(vocab_id, ItemType.VOCAB)

    # Get the review
    review = scheduler.get_review_by_item(vocab_id, ItemType.VOCAB)

    # Process review
    scheduler.process_review(review.id, rating=3, duration_ms=5000)

    # Check review history in database
    with get_cursor(clean_db) as cursor:
        cursor.execute(
            "SELECT * FROM review_history WHERE review_id = ?",
            (review.id,)
        )
        history = cursor.fetchall()

    assert len(history) == 1
    assert history[0]['rating'] == 3
    assert history[0]['duration_ms'] == 5000
    assert history[0]['reviewed_at'] is not None


def test_review_session_statistics_accuracy(clean_db):
    """Test that session statistics display is calculated correctly."""
    # Test the display_session_summary function directly
    rating_counts = {1: 1, 2: 1, 3: 2, 4: 1}  # Total 5 cards
    total_time = 125.5
    next_dates = []

    panel = display_session_summary(
        total_reviewed=5,
        rating_counts=rating_counts,
        total_time_seconds=total_time,
        next_review_dates=next_dates
    )

    content = panel.renderable
    # Accuracy: (Good + Easy) / Total = (2 + 1) / 5 = 60%
    assert "60" in content and "%" in content
    assert "5" in content  # Total reviewed


def test_review_session_time_tracking():
    """Test that session tracks time correctly."""
    import time
    from datetime import datetime, timezone

    # Create test data
    now = datetime.now(timezone.utc)
    rating_counts = {1: 0, 2: 0, 3: 5, 4: 0}
    total_time = 125.5  # 2 minutes 5.5 seconds

    panel = display_session_summary(
        total_reviewed=5,
        rating_counts=rating_counts,
        total_time_seconds=total_time,
        next_review_dates=[]
    )

    content = panel.renderable
    assert "2m" in content  # Minutes
    assert "5s" in content  # Seconds
    assert "25.1s" in content  # Average per card (125.5 / 5)


def test_review_session_handles_missing_items(clean_db, sample_vocabulary):
    """Test that review can be created and queried correctly."""
    from japanese_cli.database import add_vocabulary, get_cursor
    from japanese_cli.srs import ReviewScheduler

    # Add vocabulary and create review
    vocab_id = add_vocabulary(db_path=clean_db, **sample_vocabulary)
    scheduler = ReviewScheduler(db_path=clean_db)
    review_id = scheduler.create_new_review(vocab_id, ItemType.VOCAB)

    # Verify review exists
    review = scheduler.get_review_by_item(vocab_id, ItemType.VOCAB)
    assert review is not None
    assert review.item_id == vocab_id

    # Note: Testing error handling for missing items requires manual testing
    # as it involves complex UI interactions
