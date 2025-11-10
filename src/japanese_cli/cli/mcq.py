"""
CLI command for MCQ (Multiple Choice Question) review system.

Provides MCQ-based spaced repetition review sessions with intelligent
distractor selection. Independent from traditional flashcard reviews.
"""

import random
import time
from typing import Optional

import typer
from rich.console import Console

from ..database import (
    get_vocabulary_by_id,
    get_kanji_by_id,
    list_all_vocabulary,
    list_all_kanji,
)
from ..models import Vocabulary, Kanji, ItemType
from ..srs import MCQReviewScheduler
from ..srs.mcq_generator import MCQGenerator
from ..ui import (
    display_mcq_question,
    display_mcq_result,
    display_mcq_session_summary,
    prompt_mcq_option,
)

# Create console for rich output
console = Console()


def mcq(
    item_type: str = typer.Option(
        "both",
        "--type",
        "-t",
        help="Type of items to review (vocab, kanji, or both)"
    ),
    jlpt_level: Optional[str] = typer.Option(
        None,
        "--level",
        "-l",
        help="Filter by JLPT level (n5/n4/n3/n2/n1)"
    ),
    limit: int = typer.Option(
        20,
        "--limit",
        "-n",
        help="Maximum number of questions per session"
    ),
    question_type: str = typer.Option(
        "mixed",
        "--question-type",
        help="Question mode (word-to-meaning, meaning-to-word, or mixed)"
    ),
    language: str = typer.Option(
        "vi",
        "--language",
        help="Meaning language (vi or en)"
    ),
):
    """
    Start an interactive multiple-choice question (MCQ) review session.

    MCQ reviews use spaced repetition (FSRS algorithm) independently from flashcard reviews.
    Each question shows 4 options with intelligent distractors based on JLPT level,
    semantic similarity, phonetic similarity, and visual similarity (for kanji).

    Examples:
        japanese-cli mcq
        japanese-cli mcq --type vocab --level n5 --limit 10
        japanese-cli mcq --question-type word-to-meaning --language en
    """
    # Validate item type
    if item_type not in ["vocab", "kanji", "both"]:
        console.print(f"[red]Error: Invalid type '{item_type}'. Use 'vocab', 'kanji', or 'both'.[/red]")
        raise typer.Exit(code=1)

    # Validate JLPT level
    if jlpt_level and jlpt_level not in ["n5", "n4", "n3", "n2", "n1"]:
        console.print(f"[red]Error: Invalid JLPT level '{jlpt_level}'.[/red]")
        raise typer.Exit(code=1)

    # Validate question type
    if question_type not in ["word-to-meaning", "meaning-to-word", "mixed"]:
        console.print(f"[red]Error: Invalid question-type '{question_type}'. Use 'word-to-meaning', 'meaning-to-word', or 'mixed'.[/red]")
        raise typer.Exit(code=1)

    # Validate language
    if language not in ["vi", "en"]:
        console.print(f"[red]Error: Invalid language '{language}'. Use 'vi' or 'en'.[/red]")
        raise typer.Exit(code=1)

    try:
        _run_mcq_session(item_type, jlpt_level, limit, question_type, language)
    except KeyboardInterrupt:
        console.print("\n\n[yellow]MCQ session cancelled.[/yellow]")
        raise typer.Exit(code=0)
    except Exception as e:
        console.print(f"\n[red]Error during MCQ session:[/red] {e}")
        raise typer.Exit(code=1)


def _auto_create_mcq_reviews(
    scheduler: MCQReviewScheduler,
    item_type: str,
    jlpt_level: Optional[str]
) -> int:
    """
    Auto-create MCQ review entries for items that don't have them yet.

    Args:
        scheduler: MCQReviewScheduler instance
        item_type: 'vocab', 'kanji', or 'both'
        jlpt_level: Optional JLPT level filter

    Returns:
        Number of MCQ reviews created
    """
    created_count = 0

    # Get db_path from scheduler
    db_path = scheduler.db_path

    # Determine which types to process
    types_to_process = []
    if item_type == "both":
        types_to_process = ["vocab", "kanji"]
    else:
        types_to_process = [item_type]

    for current_type in types_to_process:
        # Get ALL items of this type (not just flashcards)
        if current_type == "vocab":
            items = list_all_vocabulary(jlpt_level=jlpt_level, limit=None, offset=0, db_path=db_path)
            item_type_enum = ItemType.VOCAB
        else:  # kanji
            items = list_all_kanji(jlpt_level=jlpt_level, limit=None, offset=0, db_path=db_path)
            item_type_enum = ItemType.KANJI

        # For each item, check if MCQ review exists
        for item in items:
            item_id = item["id"]
            existing_review = scheduler.get_mcq_review_by_item(item_id, item_type_enum)

            if existing_review is None:
                # Create new MCQ review
                try:
                    scheduler.create_mcq_review(item_id, item_type_enum)
                    created_count += 1
                except Exception:
                    # Skip items that fail (e.g., invalid IDs)
                    continue

    return created_count


def _run_mcq_session(
    item_type: str,
    jlpt_level: Optional[str],
    limit: int,
    question_type: str,
    language: str
):
    """Run the interactive MCQ review session."""
    import sys

    scheduler = MCQReviewScheduler()
    generator = MCQGenerator()

    # Step 1: Auto-create MCQ reviews for items without them
    console.print("\n[bold cyan]Preparing MCQ session...[/bold cyan]")
    sys.stdout.flush()

    created_count = _auto_create_mcq_reviews(scheduler, item_type, jlpt_level)
    if created_count > 0:
        console.print(f"[dim]Auto-created {created_count} MCQ review entries[/dim]")
        sys.stdout.flush()

    # Step 2: Get due MCQ reviews
    console.print("[bold cyan]Loading due MCQ cards...[/bold cyan]")
    sys.stdout.flush()

    due_mcqs = []
    if item_type == "both":
        # Get both vocab and kanji, then shuffle them together
        vocab_mcqs = scheduler.get_due_mcqs(
            limit=limit,
            jlpt_level=jlpt_level,
            item_type=ItemType.VOCAB
        )
        kanji_mcqs = scheduler.get_due_mcqs(
            limit=limit,
            jlpt_level=jlpt_level,
            item_type=ItemType.KANJI
        )
        due_mcqs = vocab_mcqs + kanji_mcqs
        # Random interleaving
        random.shuffle(due_mcqs)
        # Apply limit after shuffling
        due_mcqs = due_mcqs[:limit]
    else:
        # Single type
        item_type_enum = ItemType.VOCAB if item_type == "vocab" else ItemType.KANJI
        due_mcqs = scheduler.get_due_mcqs(
            limit=limit,
            jlpt_level=jlpt_level,
            item_type=item_type_enum
        )

    # Check if any MCQs are due
    if not due_mcqs:
        console.print("\n[green]✓ No MCQ cards due for review![/green]")
        console.print("[dim]Great job keeping up with your studies![/dim]")
        sys.stdout.flush()
        return

    # Step 3: Show session intro
    total_questions = len(due_mcqs)
    console.print(f"\n[bold green]MCQ Review Session[/bold green]")
    console.print(f"[dim]Found {total_questions} card(s) due for review[/dim]")

    if jlpt_level:
        console.print(f"[dim]Level: {jlpt_level.upper()}[/dim]")
    if item_type != "both":
        console.print(f"[dim]Type: {item_type.capitalize()}[/dim]")
    console.print(f"[dim]Question mode: {question_type}[/dim]")
    console.print(f"[dim]Language: {language.upper()}[/dim]")

    console.print("\n[dim]Press Ctrl+C at any time to quit (progress will be saved)[/dim]")
    console.print()
    sys.stdout.flush()

    # Session statistics
    session_start_time = time.time()
    correct_count = 0
    incorrect_count = 0
    next_review_dates = []
    questions_answered = 0

    # Step 4: Review each MCQ
    for i, mcq_review in enumerate(due_mcqs, start=1):
        try:
            # Get the vocabulary or kanji item
            if mcq_review.item_type == ItemType.VOCAB:
                item_dict = get_vocabulary_by_id(mcq_review.item_id)
                if item_dict is None:
                    console.print(f"[yellow]Warning: Vocabulary #{mcq_review.item_id} not found, skipping[/yellow]")
                    continue
                item = Vocabulary.from_db_row(item_dict)
                item_type_str = "vocab"
            else:  # ItemType.KANJI
                item_dict = get_kanji_by_id(mcq_review.item_id)
                if item_dict is None:
                    console.print(f"[yellow]Warning: Kanji #{mcq_review.item_id} not found, skipping[/yellow]")
                    continue
                item = Kanji.from_db_row(item_dict)
                item_type_str = "kanji"

            # Determine question mode for this question
            if question_type == "mixed":
                # Random per-question
                question_mode = random.choice(["word_to_meaning", "meaning_to_word"])
            else:
                # Convert hyphenated to underscore
                question_mode = question_type.replace("-", "_")

            # Start timing for this question
            question_start_time = time.time()

            # Generate MCQ question
            try:
                mcq_question = generator.generate_question(
                    item_id=mcq_review.item_id,
                    item_type=mcq_review.item_type,
                    question_mode=question_mode,
                    language=language
                )
            except ValueError as e:
                console.print(f"[yellow]Warning: Could not generate question for item #{mcq_review.item_id}: {e}[/yellow]")
                console.print("[yellow]Skipping to next card...[/yellow]\n")
                continue

            # Display question
            question_panel = display_mcq_question(
                question=mcq_question,
                current=i,
                total=total_questions
            )
            console.print(question_panel)
            sys.stdout.flush()

            # Get user input (A/B/C/D)
            selected_index = prompt_mcq_option()

            # Check correctness
            is_correct = mcq_question.is_correct(selected_index)

            # Calculate time spent on this question
            question_duration_ms = int((time.time() - question_start_time) * 1000)

            # Display result
            result_panel = display_mcq_result(
                question=mcq_question,
                selected_index=selected_index,
                is_correct=is_correct
            )
            console.print(result_panel)
            sys.stdout.flush()

            # Process review (update FSRS state)
            updated_review = scheduler.process_mcq_review(
                review_id=mcq_review.id,
                is_correct=is_correct,
                selected_option=selected_index,
                duration_ms=question_duration_ms
            )

            # Update statistics
            if is_correct:
                correct_count += 1
            else:
                incorrect_count += 1
            questions_answered += 1

            # Store next review date
            word_text = item.word if item_type_str == "vocab" else item.character
            next_review_dates.append((word_text, updated_review.due_date))

            # Brief pause for readability
            time.sleep(0.5)

            # Clear screen for next question (show separator)
            console.print("\n" + "─" * 60 + "\n")

        except KeyboardInterrupt:
            # User wants to quit early
            raise
        except Exception as e:
            console.print(f"[red]Error processing question:[/red] {e}")
            console.print("[yellow]Skipping to next card...[/yellow]\n")
            continue

    # Calculate total session time
    total_time_seconds = time.time() - session_start_time

    # Step 5: Display session summary
    if questions_answered > 0:
        accuracy_rate = (correct_count / questions_answered) * 100 if questions_answered > 0 else 0
        summary_panel = display_mcq_session_summary(
            total_reviewed=questions_answered,
            correct_count=correct_count,
            incorrect_count=incorrect_count,
            total_time_seconds=total_time_seconds,
            accuracy_rate=accuracy_rate,
            next_review_dates=next_review_dates[:5]  # Show first 5
        )
        console.print(summary_panel)
        sys.stdout.flush()
    else:
        console.print("\n[yellow]No questions were answered.[/yellow]")
        sys.stdout.flush()
