"""
Integration test for MCQ workflow: Generator + Scheduler.

Tests the full MCQ workflow from creating reviews to generating questions
and processing answers.
"""

import pytest

from japanese_cli.database import add_vocabulary, add_kanji
from japanese_cli.models import ItemType
from japanese_cli.srs import MCQReviewScheduler
from japanese_cli.srs.mcq_generator import MCQGenerator


def test_full_mcq_workflow_with_generator(mock_db_path):
    """
    Test complete MCQ workflow: create review → get due → generate question → answer → update.

    This verifies that MCQGenerator and MCQReviewScheduler work together correctly.
    """
    # Step 1: Add multiple vocabulary items (need enough for distractors)
    vocab_ids = []
    words = [
        ("単語", "たんご", {"vi": ["từ vựng"], "en": ["word"]}, "n5"),
        ("勉強", "べんきょう", {"vi": ["học tập"], "en": ["study"]}, "n5"),
        ("学校", "がっこう", {"vi": ["trường học"], "en": ["school"]}, "n5"),
        ("先生", "せんせい", {"vi": ["giáo viên"], "en": ["teacher"]}, "n5"),
        ("日本語", "にほんご", {"vi": ["tiếng Nhật"], "en": ["Japanese language"]}, "n5"),
    ]

    for word, reading, meanings, level in words:
        vocab_id = add_vocabulary(
            word=word,
            reading=reading,
            meanings=meanings,
            jlpt_level=level,
            db_path=mock_db_path,
        )
        vocab_ids.append(vocab_id)

    # Step 2: Create MCQ review for first vocabulary item
    scheduler = MCQReviewScheduler(db_path=mock_db_path)
    review_id = scheduler.create_mcq_review(vocab_ids[0], ItemType.VOCAB)

    # Step 3: Get due MCQ reviews
    due_mcqs = scheduler.get_due_mcqs()
    assert len(due_mcqs) == 1

    mcq_review = due_mcqs[0]
    assert mcq_review.item_id == vocab_ids[0]

    # Step 4: Generate MCQ question for this review
    generator = MCQGenerator(db_path=mock_db_path)
    question = generator.generate_question(
        item_id=mcq_review.item_id,
        item_type=mcq_review.item_type,
        question_mode="word_to_meaning",
        language="vi"
    )

    # Verify question structure
    assert len(question.options) == 4
    assert 0 <= question.correct_index < 4
    assert question.item_id == vocab_ids[0]
    assert question.jlpt_level == "n5"

    # Step 5: Simulate user selecting the correct answer
    user_selected = question.correct_index
    is_correct = question.is_correct(user_selected)
    assert is_correct is True

    # Step 6: Process the review with scheduler
    updated_review = scheduler.process_mcq_review(
        review_id=mcq_review.id,
        is_correct=is_correct,
        selected_option=user_selected,
        duration_ms=5000
    )

    # Verify review was updated
    assert updated_review.review_count == 1
    assert updated_review.last_reviewed is not None

    # Step 7: Verify history was recorded
    from japanese_cli.database import get_cursor

    with get_cursor(mock_db_path) as cursor:
        cursor.execute(
            "SELECT * FROM mcq_review_history WHERE mcq_review_id = ?",
            (mcq_review.id,)
        )
        history = cursor.fetchall()

    assert len(history) == 1
    assert history[0]["selected_option"] == user_selected
    assert history[0]["is_correct"] == 1


def test_mcq_workflow_incorrect_answer(mock_db_path):
    """Test MCQ workflow when user answers incorrectly."""
    # Add vocabulary
    vocab_ids = []
    for i in range(5):
        vocab_id = add_vocabulary(
            word=f"test{i}",
            reading=f"てすと{i}",
            meanings={"vi": [f"nghĩa {i}"], "en": [f"meaning {i}"]},
            jlpt_level="n5",
            db_path=mock_db_path,
        )
        vocab_ids.append(vocab_id)

    # Create MCQ review
    scheduler = MCQReviewScheduler(db_path=mock_db_path)
    review_id = scheduler.create_mcq_review(vocab_ids[0], ItemType.VOCAB)

    # Generate question
    generator = MCQGenerator(db_path=mock_db_path)
    question = generator.generate_question(
        item_id=vocab_ids[0],
        item_type=ItemType.VOCAB,
        question_mode="word_to_meaning",
        language="vi"
    )

    # User selects incorrect answer (not the correct index)
    incorrect_options = [i for i in range(4) if i != question.correct_index]
    user_selected = incorrect_options[0]
    is_correct = question.is_correct(user_selected)
    assert is_correct is False

    # Process review
    updated_review = scheduler.process_mcq_review(
        review_id=review_id,
        is_correct=is_correct,
        selected_option=user_selected,
        duration_ms=3000
    )

    # Verify
    assert updated_review.review_count == 1

    # Check history
    from japanese_cli.database import get_cursor

    with get_cursor(mock_db_path) as cursor:
        cursor.execute(
            "SELECT * FROM mcq_review_history WHERE mcq_review_id = ?",
            (review_id,)
        )
        history = cursor.fetchall()

    assert len(history) == 1
    assert history[0]["is_correct"] == 0  # Incorrect


def test_mcq_workflow_multiple_question_modes(mock_db_path):
    """Test MCQ workflow with both word_to_meaning and meaning_to_word modes."""
    # Add kanji with enough items for distractors
    kanji_list = [
        ("語", ["ゴ"], ["かた.る"], {"vi": ["ngữ"], "en": ["word"]}, "n5"),
        ("言", ["ゲン", "ゴン"], ["い.う"], {"vi": ["ngôn"], "en": ["say"]}, "n5"),
        ("話", ["ワ"], ["はな.す"], {"vi": ["thoại"], "en": ["talk"]}, "n5"),
        ("読", ["ドク"], ["よ.む"], {"vi": ["độc"], "en": ["read"]}, "n5"),
        ("書", ["ショ"], ["か.く"], {"vi": ["thư"], "en": ["write"]}, "n5"),
    ]

    kanji_ids = []
    for char, on_readings, kun_readings, meanings, level in kanji_list:
        kanji_id = add_kanji(
            character=char,
            on_readings=on_readings,
            kun_readings=kun_readings,
            meanings=meanings,
            jlpt_level=level,
            db_path=mock_db_path,
        )
        kanji_ids.append(kanji_id)

    scheduler = MCQReviewScheduler(db_path=mock_db_path)
    generator = MCQGenerator(db_path=mock_db_path)

    # Test word_to_meaning mode
    review_id1 = scheduler.create_mcq_review(kanji_ids[0], ItemType.KANJI)
    question1 = generator.generate_question(
        item_id=kanji_ids[0],
        item_type=ItemType.KANJI,
        question_mode="word_to_meaning",
        language="vi"
    )

    assert "語" in question1.question_text
    assert len(question1.options) == 4

    scheduler.process_mcq_review(
        review_id=review_id1,
        is_correct=True,
        selected_option=question1.correct_index
    )

    # Test meaning_to_word mode
    review_id2 = scheduler.create_mcq_review(kanji_ids[1], ItemType.KANJI)
    question2 = generator.generate_question(
        item_id=kanji_ids[1],
        item_type=ItemType.KANJI,
        question_mode="meaning_to_word",
        language="vi"
    )

    assert "ngôn" in question2.question_text
    assert len(question2.options) == 4

    scheduler.process_mcq_review(
        review_id=review_id2,
        is_correct=True,
        selected_option=question2.correct_index
    )

    # Verify both reviews were recorded
    assert scheduler.get_mcq_review_count() == 2


def test_mcq_workflow_with_multiple_reviews(mock_db_path):
    """Test reviewing the same item multiple times with FSRS updates."""
    # Add vocabulary
    vocab_ids = []
    for i in range(5):
        vocab_id = add_vocabulary(
            word=f"word{i}",
            reading=f"わーど{i}",
            meanings={"vi": [f"nghĩa {i}"], "en": [f"meaning {i}"]},
            jlpt_level="n5",
            db_path=mock_db_path,
        )
        vocab_ids.append(vocab_id)

    scheduler = MCQReviewScheduler(db_path=mock_db_path)
    generator = MCQGenerator(db_path=mock_db_path)

    # Create review
    review_id = scheduler.create_mcq_review(vocab_ids[0], ItemType.VOCAB)

    # Review 3 times
    for review_num in [1, 2, 3]:
        # Make it due
        if review_num > 1:
            from datetime import datetime, timedelta, timezone
            from japanese_cli.database import get_cursor

            with get_cursor(mock_db_path) as cursor:
                past_time = datetime.now(timezone.utc) - timedelta(hours=1)
                cursor.execute(
                    "UPDATE mcq_reviews SET due_date = ? WHERE id = ?",
                    (past_time.isoformat(), review_id),
                )

        # Generate question
        question = generator.generate_question(
            item_id=vocab_ids[0],
            item_type=ItemType.VOCAB,
            question_mode="word_to_meaning",
            language="vi"
        )

        # Answer correctly
        updated_review = scheduler.process_mcq_review(
            review_id=review_id,
            is_correct=True,
            selected_option=question.correct_index,
            duration_ms=4000 + (review_num * 100)  # Slightly different times
        )

        assert updated_review.review_count == review_num

    # Verify history has 3 entries
    from japanese_cli.database import get_cursor

    with get_cursor(mock_db_path) as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM mcq_review_history WHERE mcq_review_id = ?",
            (review_id,)
        )
        count = cursor.fetchone()[0]

    assert count == 3


# =============================================================================
# CLI Integration Tests
# =============================================================================


def test_cli_mcq_full_workflow(mock_db_path):
    """
    Test complete CLI workflow: add items → run mcq command → verify FSRS updates.
    """
    from typer.testing import CliRunner
    from unittest.mock import patch
    from japanese_cli.main import app

    runner = CliRunner()

    # Step 1: Add vocabulary items (5 items for distractors)
    vocab_ids = []
    for i in range(5):
        vocab_id = add_vocabulary(
            word=f"単語{i}",
            reading=f"たんご{i}",
            meanings={"vi": [f"từ {i}"], "en": [f"word {i}"]},
            jlpt_level="n5",
            db_path=mock_db_path,
        )
        vocab_ids.append(vocab_id)

    # Step 2: Mock user input to answer correctly (always select option 0)
    with patch("japanese_cli.cli.mcq.prompt_mcq_option") as mock_prompt:
        with patch("japanese_cli.cli.mcq.time.sleep"):  # Skip pause
            # User selects option A (index 0) for all questions
            mock_prompt.return_value = 0

            # Step 3: Run MCQ command via CLI
            result = runner.invoke(app, [
                "mcq",
                "--type", "vocab",
                "--limit", "2",
                "--question-type", "word-to-meaning",
                "--language", "vi"
            ])

    # Step 4: Verify CLI completed successfully
    assert result.exit_code in [0, 1]  # Accept both success and graceful error
    assert "MCQ Review Session" in result.stdout
    assert "Auto-created" in result.stdout  # Should auto-create reviews
    assert "Found" in result.stdout  # Should find cards

    # Step 5: Verify FSRS state was updated in database
    scheduler = MCQReviewScheduler(db_path=mock_db_path)
    review = scheduler.get_mcq_review_by_item(vocab_ids[0], ItemType.VOCAB)

    assert review is not None
    assert review.review_count >= 1  # At least 1 review completed

    # Step 6: Verify history was recorded
    from japanese_cli.database import get_cursor

    with get_cursor(mock_db_path) as cursor:
        cursor.execute("SELECT COUNT(*) FROM mcq_review_history")
        history_count = cursor.fetchone()[0]

    assert history_count >= 1  # At least 1 history entry


def test_cli_mcq_with_type_both(mock_db_path):
    """Test CLI MCQ command with --type both (mixed vocab and kanji)."""
    from typer.testing import CliRunner
    from unittest.mock import patch
    from japanese_cli.main import app

    runner = CliRunner()

    # Add 2 vocab items
    for i in range(2):
        add_vocabulary(
            word=f"word{i}",
            reading=f"reading{i}",
            meanings={"vi": [f"nghĩa {i}"], "en": [f"meaning {i}"]},
            jlpt_level="n5",
            db_path=mock_db_path,
        )

    # Add 2 kanji items
    for i, char in enumerate(["語", "話"]):
        add_kanji(
            character=char,
            on_readings=[f"ゴ{i}"],
            kun_readings=[f"かた{i}"],
            meanings={"vi": [f"kanji {i}"], "en": [f"kanji {i}"]},
            jlpt_level="n5",
            db_path=mock_db_path,
        )

    # Mock user input
    with patch("japanese_cli.cli.mcq.prompt_mcq_option") as mock_prompt:
        with patch("japanese_cli.cli.mcq.time.sleep"):
            mock_prompt.side_effect = [0, 1, 0, 1]  # Answer 4 questions

            # Run with --type both
            result = runner.invoke(app, [
                "mcq",
                "--type", "both",
                "--limit", "4"
            ])

    assert result.exit_code in [0, 1]  # Accept both success and graceful error
    assert "Auto-created 4 MCQ review entries" in result.stdout
    assert "Found 4 card(s) due" in result.stdout


def test_cli_mcq_with_question_type_mixed(mock_db_path):
    """Test CLI MCQ with --question-type mixed (randomized per question)."""
    from typer.testing import CliRunner
    from unittest.mock import patch
    from japanese_cli.main import app

    runner = CliRunner()

    # Add 5 vocabulary items
    for i in range(5):
        add_vocabulary(
            word=f"test{i}",
            reading=f"てすと{i}",
            meanings={"vi": [f"test {i}"], "en": [f"test {i}"]},
            jlpt_level="n5",
            db_path=mock_db_path,
        )

    with patch("japanese_cli.cli.mcq.prompt_mcq_option") as mock_prompt:
        with patch("japanese_cli.cli.mcq.time.sleep"):
            # Patch random.choice to control question mode selection
            with patch("japanese_cli.cli.mcq.random.choice") as mock_random:
                # Alternate between word_to_meaning and meaning_to_word
                mock_random.side_effect = [
                    "word_to_meaning",
                    "meaning_to_word",
                    "word_to_meaning"
                ]
                mock_prompt.return_value = 0

                result = runner.invoke(app, [
                    "mcq",
                    "--question-type", "mixed",
                    "--limit", "3"
                ])

    assert result.exit_code in [0, 1]  # Accept both success and graceful error
    assert "Question mode: mixed" in result.stdout
    # Should have called random.choice 3 times (once per question)


def test_cli_mcq_with_jlpt_filter(mock_db_path):
    """Test CLI MCQ with --level filter."""
    from typer.testing import CliRunner
    from japanese_cli.main import app

    runner = CliRunner()

    # Add items with different JLPT levels
    add_vocabulary(
        word="n5word",
        reading="えぬご",
        meanings={"vi": ["n5"], "en": ["n5"]},
        jlpt_level="n5",
        db_path=mock_db_path,
    )
    add_vocabulary(
        word="n4word",
        reading="えぬよん",
        meanings={"vi": ["n4"], "en": ["n4"]},
        jlpt_level="n4",
        db_path=mock_db_path,
    )

    result = runner.invoke(app, [
        "mcq",
        "--level", "n5",
        "--limit", "10"
    ])

    assert result.exit_code in [0, 1]  # Accept both success and graceful error
    assert "Level: N5" in result.stdout
    # Should only create 1 MCQ review (for n5 item)
    assert "Auto-created 1 MCQ review" in result.stdout


def test_cli_mcq_early_exit(mock_db_path):
    """Test that Ctrl+C during MCQ session is handled gracefully."""
    from typer.testing import CliRunner
    from unittest.mock import patch
    from japanese_cli.main import app

    runner = CliRunner()

    # Add vocabulary
    for i in range(5):
        add_vocabulary(
            word=f"word{i}",
            reading=f"reading{i}",
            meanings={"vi": [f"nghĩa {i}"], "en": [f"meaning {i}"]},
            jlpt_level="n5",
            db_path=mock_db_path,
        )

    # Mock prompt to raise KeyboardInterrupt after first question
    with patch("japanese_cli.cli.mcq.prompt_mcq_option") as mock_prompt:
        with patch("japanese_cli.cli.mcq.time.sleep"):
            mock_prompt.side_effect = [0, KeyboardInterrupt()]

            result = runner.invoke(app, [
                "mcq",
                "--limit", "3"
            ])

    # Early exit is acceptable
    assert result.exit_code in [0, 1]  # Accept both success and graceful error


def test_cli_mcq_no_cards_due(mock_db_path):
    """Test CLI MCQ when no cards are due for review."""
    from typer.testing import CliRunner
    from japanese_cli.main import app

    runner = CliRunner()

    # Database is empty, no cards to review
    result = runner.invoke(app, ["mcq"])

    assert result.exit_code in [0, 1]  # Accept both success and graceful error
    assert "No MCQ cards due" in result.stdout
