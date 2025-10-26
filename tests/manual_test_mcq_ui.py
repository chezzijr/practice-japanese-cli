#!/usr/bin/env python3
"""
Manual testing script for MCQ UI components.

Run this script to see the UI components in action:
    python tests/manual_test_mcq_ui.py
"""

from datetime import datetime, timezone, timedelta
from rich.console import Console

from japanese_cli.models.mcq import MCQQuestion
from japanese_cli.models.review import ItemType
from japanese_cli.ui import (
    display_mcq_question,
    display_mcq_result,
    display_mcq_session_summary,
    prompt_mcq_option,
)

console = Console()


def test_mcq_question_display():
    """Test displaying an MCQ question."""
    console.print("\n[bold cyan]═══ Test 1: MCQ Question Display ═══[/bold cyan]\n")

    question = MCQQuestion(
        item_id=1,
        item_type=ItemType.VOCAB,
        question_text="What is the meaning of '単語' (たんご)?",
        options=[
            "từ vựng (vocabulary)",
            "kanji (Chinese character)",
            "ngữ pháp (grammar)",
            "đọc (read)",
        ],
        correct_index=0,
        jlpt_level="n5",
        explanation="単語 (たんご) means 'vocabulary' or 'word' in Vietnamese: từ vựng",
    )

    panel = display_mcq_question(question, current=1, total=5)
    console.print(panel)


def test_mcq_result_correct():
    """Test displaying correct answer result."""
    console.print("\n[bold cyan]═══ Test 2: Correct Answer Result ═══[/bold cyan]\n")

    question = MCQQuestion(
        item_id=1,
        item_type=ItemType.VOCAB,
        question_text="What is the meaning of '単語' (たんご)?",
        options=[
            "từ vựng (vocabulary)",
            "kanji (Chinese character)",
            "ngữ pháp (grammar)",
            "đọc (read)",
        ],
        correct_index=0,
        jlpt_level="n5",
        explanation="単語 (たんご) means 'vocabulary' or 'word' in Vietnamese: từ vựng",
    )

    panel = display_mcq_result(question, selected_index=0, is_correct=True)
    console.print(panel)


def test_mcq_result_incorrect():
    """Test displaying incorrect answer result."""
    console.print("\n[bold cyan]═══ Test 3: Incorrect Answer Result ═══[/bold cyan]\n")

    question = MCQQuestion(
        item_id=2,
        item_type=ItemType.KANJI,
        question_text="What is the meaning of '語'?",
        options=[
            "ngữ (word, language)",
            "học (study)",
            "viết (write)",
            "nói (speak)",
        ],
        correct_index=0,
        jlpt_level="n4",
        explanation="語 means 'word' or 'language', with Sino-Vietnamese reading 'ngữ'",
    )

    panel = display_mcq_result(question, selected_index=2, is_correct=False)
    console.print(panel)


def test_mcq_session_summary():
    """Test displaying session summary."""
    console.print("\n[bold cyan]═══ Test 4: Session Summary ═══[/bold cyan]\n")

    now = datetime.now(timezone.utc)
    next_review_dates = [
        ("単語", now + timedelta(days=0)),  # Due now
        ("語", now + timedelta(days=1)),  # Tomorrow
        ("読む", now + timedelta(days=3)),  # In 3 days
        ("書く", now + timedelta(days=7)),  # In 7 days
        ("話す", now + timedelta(days=14)),  # In 14 days
        ("聞く", now + timedelta(days=21)),  # In 21 days
    ]

    panel = display_mcq_session_summary(
        total_reviewed=20,
        correct_count=17,
        incorrect_count=3,
        total_time_seconds=315.5,
        accuracy_rate=85.0,
        next_review_dates=next_review_dates,
    )
    console.print(panel)


def test_all_jlpt_levels():
    """Test displaying questions with all JLPT levels."""
    console.print("\n[bold cyan]═══ Test 5: All JLPT Levels ═══[/bold cyan]\n")

    levels = ["n5", "n4", "n3", "n2", "n1"]

    for i, level in enumerate(levels, 1):
        question = MCQQuestion(
            item_id=i,
            item_type=ItemType.VOCAB,
            question_text=f"Sample question for {level.upper()}",
            options=["Option A", "Option B", "Option C", "Option D"],
            correct_index=0,
            jlpt_level=level,
        )
        panel = display_mcq_question(question, current=i, total=5)
        console.print(panel)
        console.print()


def test_interactive_prompt():
    """Test interactive option prompt (requires user input)."""
    console.print("\n[bold cyan]═══ Test 6: Interactive Prompt ═══[/bold cyan]\n")
    console.print("[yellow]This test requires user input. Press Ctrl+C to skip.[/yellow]\n")

    try:
        selected = prompt_mcq_option()
        console.print(f"\n[green]You selected option index: {selected}[/green]")

        # Convert to letter
        letters = ["A", "B", "C", "D"]
        console.print(f"[green]That's option [{letters[selected]}][/green]")
    except KeyboardInterrupt:
        console.print("\n[yellow]Skipped interactive test[/yellow]")


def main():
    """Run all manual tests."""
    console.print("\n[bold magenta]MCQ UI Components - Manual Testing[/bold magenta]")
    console.print("[dim]═" * 50 + "[/dim]\n")

    test_mcq_question_display()
    test_mcq_result_correct()
    test_mcq_result_incorrect()
    test_mcq_session_summary()
    test_all_jlpt_levels()
    test_interactive_prompt()

    console.print("\n[bold green]✓ All manual tests completed![/bold green]\n")


if __name__ == "__main__":
    main()
