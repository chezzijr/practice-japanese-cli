"""
Tests for MCQ UI display functions.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from rich.panel import Panel

from japanese_cli.models.mcq import MCQQuestion
from japanese_cli.models.review import ItemType
from japanese_cli.ui.display import (
    display_mcq_question,
    display_mcq_result,
    display_mcq_session_summary,
    prompt_mcq_option,
    JLPT_COLORS,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_mcq_question_vocab():
    """Sample MCQ question for vocabulary."""
    return MCQQuestion(
        item_id=1,
        item_type=ItemType.VOCAB,
        question_text="What is the meaning of '単語' (たんご)?",
        options=["từ vựng", "kanji", "ngữ pháp", "đọc"],
        correct_index=0,
        jlpt_level="n5",
        explanation="単語 (たんご) means 'vocabulary' or 'word' in Vietnamese: từ vựng"
    )


@pytest.fixture
def sample_mcq_question_kanji():
    """Sample MCQ question for kanji."""
    return MCQQuestion(
        item_id=5,
        item_type=ItemType.KANJI,
        question_text="What is the meaning of '語'?",
        options=["ngữ (word, language)", "học (study)", "viết (write)", "nói (speak)"],
        correct_index=0,
        jlpt_level="n4"
    )


@pytest.fixture
def sample_mcq_question_no_level():
    """Sample MCQ question without JLPT level."""
    return MCQQuestion(
        item_id=10,
        item_type=ItemType.VOCAB,
        question_text="What word means 'từ điển' in Japanese?",
        options=["辞書", "単語", "文法", "読む"],
        correct_index=0,
        jlpt_level=None
    )


@pytest.fixture
def sample_next_review_dates():
    """Sample next review dates for summary."""
    now = datetime.now(timezone.utc)
    return [
        ("単語", now + timedelta(days=0)),  # Due now
        ("語", now + timedelta(days=1)),    # Tomorrow
        ("読む", now + timedelta(days=3)),   # In 3 days
        ("書く", now + timedelta(days=7)),   # In 7 days
        ("話す", now + timedelta(days=14)),  # In 14 days
        ("聞く", now + timedelta(days=21)),  # In 21 days
    ]


# ============================================================================
# display_mcq_question() Tests
# ============================================================================

def test_display_mcq_question_vocab(sample_mcq_question_vocab):
    """Test displaying MCQ question for vocabulary."""
    panel = display_mcq_question(sample_mcq_question_vocab, current=1, total=20)

    assert isinstance(panel, Panel)
    assert "Question 1 of 20" in panel.renderable
    assert "単語" in panel.renderable or "たんご" in panel.renderable
    assert "[A]" in panel.renderable
    assert "[B]" in panel.renderable
    assert "[C]" in panel.renderable
    assert "[D]" in panel.renderable
    assert "từ vựng" in panel.renderable
    # Check for the instruction text (case insensitive)
    assert "press a, b, c, or d" in panel.renderable.lower()


def test_display_mcq_question_kanji(sample_mcq_question_kanji):
    """Test displaying MCQ question for kanji."""
    panel = display_mcq_question(sample_mcq_question_kanji, current=5, total=10)

    assert isinstance(panel, Panel)
    assert "Question 5 of 10" in panel.renderable
    assert "語" in panel.renderable
    assert "ngữ" in panel.renderable


def test_display_mcq_question_with_jlpt_level(sample_mcq_question_vocab):
    """Test MCQ question displays JLPT level with correct color."""
    panel = display_mcq_question(sample_mcq_question_vocab, current=1, total=10)

    assert "N5" in panel.renderable.upper()
    # Check that the JLPT level is displayed


def test_display_mcq_question_without_jlpt_level(sample_mcq_question_no_level):
    """Test MCQ question without JLPT level."""
    panel = display_mcq_question(sample_mcq_question_no_level, current=1, total=10)

    assert isinstance(panel, Panel)
    assert "辞書" in panel.renderable


def test_display_mcq_question_options_order(sample_mcq_question_vocab):
    """Test that all 4 options are displayed in order."""
    panel = display_mcq_question(sample_mcq_question_vocab, current=1, total=10)

    content = panel.renderable
    # Check all options are present
    for option in sample_mcq_question_vocab.options:
        assert option in content


def test_display_mcq_question_border_style(sample_mcq_question_vocab):
    """Test that question panel has yellow border."""
    panel = display_mcq_question(sample_mcq_question_vocab, current=1, total=10)

    assert panel.border_style == "yellow"


# ============================================================================
# display_mcq_result() Tests
# ============================================================================

def test_display_mcq_result_correct(sample_mcq_question_vocab):
    """Test displaying correct answer result."""
    panel = display_mcq_result(
        question=sample_mcq_question_vocab,
        selected_index=0,
        is_correct=True
    )

    assert isinstance(panel, Panel)
    assert "Correct" in panel.renderable
    assert panel.border_style == "green"
    assert "[A]" in panel.renderable
    assert "từ vựng" in panel.renderable


def test_display_mcq_result_incorrect(sample_mcq_question_vocab):
    """Test displaying incorrect answer result."""
    panel = display_mcq_result(
        question=sample_mcq_question_vocab,
        selected_index=2,  # Wrong answer
        is_correct=False
    )

    assert isinstance(panel, Panel)
    assert "Incorrect" in panel.renderable
    assert panel.border_style == "red"
    # Should show both selected and correct answers
    assert "[C]" in panel.renderable  # Selected
    assert "[A]" in panel.renderable  # Correct


def test_display_mcq_result_with_explanation(sample_mcq_question_vocab):
    """Test result displays explanation when available."""
    panel = display_mcq_result(
        question=sample_mcq_question_vocab,
        selected_index=0,
        is_correct=True
    )

    assert sample_mcq_question_vocab.explanation in panel.renderable


def test_display_mcq_result_without_explanation(sample_mcq_question_no_level):
    """Test result without explanation (None)."""
    panel = display_mcq_result(
        question=sample_mcq_question_no_level,
        selected_index=0,
        is_correct=True
    )

    assert isinstance(panel, Panel)
    # Should not crash when explanation is None


def test_display_mcq_result_incorrect_shows_correct_answer(sample_mcq_question_kanji):
    """Test incorrect result shows the correct answer."""
    panel = display_mcq_result(
        question=sample_mcq_question_kanji,
        selected_index=1,  # Wrong
        is_correct=False
    )

    # Should show correct answer
    correct_answer = sample_mcq_question_kanji.get_correct_answer()
    assert correct_answer in panel.renderable
    assert "Correct answer" in panel.renderable


def test_display_mcq_result_all_options(sample_mcq_question_vocab):
    """Test result for all 4 option selections."""
    for i in range(4):
        is_correct = (i == sample_mcq_question_vocab.correct_index)
        panel = display_mcq_result(
            question=sample_mcq_question_vocab,
            selected_index=i,
            is_correct=is_correct
        )
        assert isinstance(panel, Panel)


# ============================================================================
# display_mcq_session_summary() Tests
# ============================================================================

def test_display_mcq_session_summary_basic(sample_next_review_dates):
    """Test basic MCQ session summary."""
    panel = display_mcq_session_summary(
        total_reviewed=20,
        correct_count=17,
        incorrect_count=3,
        total_time_seconds=300.5,
        accuracy_rate=85.0,
        next_review_dates=sample_next_review_dates
    )

    assert isinstance(panel, Panel)
    assert "20" in panel.renderable  # Total reviewed
    assert "17" in panel.renderable  # Correct count
    assert "3" in panel.renderable   # Incorrect count
    assert "85.0%" in panel.renderable
    assert panel.border_style == "green"


def test_display_mcq_session_summary_perfect_score(sample_next_review_dates):
    """Test summary with 100% accuracy."""
    panel = display_mcq_session_summary(
        total_reviewed=10,
        correct_count=10,
        incorrect_count=0,
        total_time_seconds=120.0,
        accuracy_rate=100.0,
        next_review_dates=sample_next_review_dates
    )

    assert "100.0%" in panel.renderable
    assert "10" in panel.renderable  # Correct
    assert "0" in panel.renderable   # Incorrect


def test_display_mcq_session_summary_poor_score(sample_next_review_dates):
    """Test summary with low accuracy (red color)."""
    panel = display_mcq_session_summary(
        total_reviewed=20,
        correct_count=10,
        incorrect_count=10,
        total_time_seconds=400.0,
        accuracy_rate=50.0,
        next_review_dates=sample_next_review_dates
    )

    assert "50.0%" in panel.renderable
    # Low score should have different emoji than high score


def test_display_mcq_session_summary_time_formatting(sample_next_review_dates):
    """Test time formatting in summary."""
    panel = display_mcq_session_summary(
        total_reviewed=10,
        correct_count=8,
        incorrect_count=2,
        total_time_seconds=125.0,  # 2m 5s
        accuracy_rate=80.0,
        next_review_dates=sample_next_review_dates
    )

    # Should show minutes and seconds
    assert "2m" in panel.renderable
    assert "5s" in panel.renderable
    assert "12.5s" in panel.renderable  # Average per question


def test_display_mcq_session_summary_next_reviews():
    """Test next reviews preview in summary."""
    # Create dates relative to function call time
    now = datetime.now(timezone.utc)
    next_review_dates = [
        ("単語", now + timedelta(days=0)),   # Due now
        ("語", now + timedelta(days=1)),     # Tomorrow
        ("読む", now + timedelta(days=3)),    # In 3 days
        ("書く", now + timedelta(days=7)),    # In 7 days
        ("話す", now + timedelta(days=14)),   # In 14 days
        ("聞く", now + timedelta(days=21)),   # In 21 days
    ]

    panel = display_mcq_session_summary(
        total_reviewed=20,
        correct_count=17,
        incorrect_count=3,
        total_time_seconds=300.0,
        accuracy_rate=85.0,
        next_review_dates=next_review_dates
    )

    # Should show first 5 items
    assert "単語" in panel.renderable
    # Check for either "Due now" or "Tomorrow" depending on timing
    assert ("Due now" in panel.renderable or "Tomorrow" in panel.renderable)
    # Should show "... and X more" for remaining items
    assert "more" in panel.renderable.lower()


def test_display_mcq_session_summary_empty_next_reviews():
    """Test summary with no next reviews."""
    panel = display_mcq_session_summary(
        total_reviewed=5,
        correct_count=4,
        incorrect_count=1,
        total_time_seconds=60.0,
        accuracy_rate=80.0,
        next_review_dates=[]
    )

    assert isinstance(panel, Panel)
    # Should not crash with empty list


def test_display_mcq_session_summary_accuracy_colors():
    """Test accuracy rate color coding."""
    # High accuracy (>=85%) - green
    panel_high = display_mcq_session_summary(
        total_reviewed=20, correct_count=18, incorrect_count=2,
        total_time_seconds=200.0, accuracy_rate=90.0, next_review_dates=[]
    )
    assert "🎯" in panel_high.renderable  # High score emoji

    # Medium accuracy (70-85%) - yellow
    panel_medium = display_mcq_session_summary(
        total_reviewed=20, correct_count=15, incorrect_count=5,
        total_time_seconds=200.0, accuracy_rate=75.0, next_review_dates=[]
    )
    assert "👍" in panel_medium.renderable  # Medium score emoji

    # Low accuracy (<70%) - red
    panel_low = display_mcq_session_summary(
        total_reviewed=20, correct_count=10, incorrect_count=10,
        total_time_seconds=200.0, accuracy_rate=50.0, next_review_dates=[]
    )
    assert "📚" in panel_low.renderable  # Low score emoji


# ============================================================================
# prompt_mcq_option() Tests
# ============================================================================

def test_prompt_mcq_option_valid_inputs():
    """Test prompt with valid A/B/C/D inputs."""
    test_cases = [
        ('A', 0),
        ('B', 1),
        ('C', 2),
        ('D', 3),
        ('a', 0),  # Lowercase
        ('b', 1),
        ('c', 2),
        ('d', 3),
    ]

    for key, expected_index in test_cases:
        with patch('japanese_cli.ui.display.get_single_keypress', return_value=key):
            result = prompt_mcq_option()
            assert result == expected_index


def test_prompt_mcq_option_invalid_then_valid():
    """Test prompt with invalid input followed by valid input."""
    # First return invalid 'X', then valid 'B'
    with patch('japanese_cli.ui.display.get_single_keypress', side_effect=['X', 'B']):
        result = prompt_mcq_option()
        assert result == 1  # B → 1


def test_prompt_mcq_option_ctrl_c():
    """Test prompt raises KeyboardInterrupt on Ctrl+C."""
    # ASCII 3 is Ctrl+C
    with patch('japanese_cli.ui.display.get_single_keypress', return_value=chr(3)):
        with pytest.raises(KeyboardInterrupt):
            prompt_mcq_option()


def test_prompt_mcq_option_fallback():
    """Test fallback to standard input on error."""
    # Simulate exception then fallback
    with patch('japanese_cli.ui.display.get_single_keypress', side_effect=Exception("Terminal error")):
        with patch('rich.prompt.Prompt.ask', return_value='C'):
            result = prompt_mcq_option()
            assert result == 2  # C → 2


def test_prompt_mcq_option_case_insensitive():
    """Test that prompt accepts both uppercase and lowercase."""
    for key in ['a', 'A']:
        with patch('japanese_cli.ui.display.get_single_keypress', return_value=key):
            result = prompt_mcq_option()
            assert result == 0


# ============================================================================
# Integration Tests
# ============================================================================

def test_full_mcq_workflow(sample_mcq_question_vocab, sample_next_review_dates):
    """Test full workflow: question → answer → result → summary."""
    # 1. Display question
    question_panel = display_mcq_question(sample_mcq_question_vocab, 1, 5)
    assert isinstance(question_panel, Panel)

    # 2. Get user answer
    with patch('japanese_cli.ui.display.get_single_keypress', return_value='A'):
        selected = prompt_mcq_option()
        assert selected == 0

    # 3. Check correctness
    is_correct = sample_mcq_question_vocab.is_correct(selected)
    assert is_correct is True

    # 4. Display result
    result_panel = display_mcq_result(sample_mcq_question_vocab, selected, is_correct)
    assert isinstance(result_panel, Panel)
    assert "Correct" in result_panel.renderable

    # 5. Display summary
    summary_panel = display_mcq_session_summary(
        total_reviewed=5,
        correct_count=4,
        incorrect_count=1,
        total_time_seconds=60.0,
        accuracy_rate=80.0,
        next_review_dates=sample_next_review_dates
    )
    assert isinstance(summary_panel, Panel)


def test_mcq_question_all_jlpt_levels():
    """Test MCQ questions with all JLPT levels."""
    levels = ["n5", "n4", "n3", "n2", "n1"]

    for level in levels:
        question = MCQQuestion(
            item_id=1,
            item_type=ItemType.VOCAB,
            question_text=f"Test question for {level}",
            options=["A", "B", "C", "D"],
            correct_index=0,
            jlpt_level=level
        )
        panel = display_mcq_question(question, 1, 10)
        assert level.upper() in panel.renderable
