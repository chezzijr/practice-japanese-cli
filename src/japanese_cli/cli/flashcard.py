"""
CLI commands for flashcard management.

Provides commands to add, list, edit, and review flashcards (vocabulary and kanji).
"""

import random
import time
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from ..database import (
    add_vocabulary,
    add_kanji,
    get_vocabulary_by_id,
    get_kanji_by_id,
    list_vocabulary,
    list_kanji,
    update_vocabulary,
    update_kanji,
    get_review,
    has_review_entry,
)
from ..models import Vocabulary, Kanji, ItemType
from ..srs import ReviewScheduler
from ..ui import (
    prompt_vocabulary_data,
    prompt_kanji_data,
    confirm_action,
    format_vocabulary_table,
    format_kanji_table,
    format_vocabulary_panel,
    format_kanji_panel,
    display_card_question,
    display_card_answer,
    prompt_rating,
    display_session_summary,
)

# Create Typer app for flashcard commands
app = typer.Typer(
    name="flashcard",
    help="Manage flashcards (vocabulary and kanji)",
    no_args_is_help=True,
)

console = Console()


@app.command(name="add")
def add_flashcard(
    item_type: str = typer.Option(
        "vocab",
        "--type",
        "-t",
        help="Type of flashcard (vocab or kanji)"
    ),
):
    """
    Add a new flashcard interactively.

    Prompts for all required and optional fields, validates input,
    and optionally creates a review entry for spaced repetition.

    Examples:
        japanese-cli flashcard add --type vocab
        japanese-cli flashcard add --type kanji
    """
    # Validate item type
    if item_type not in ["vocab", "kanji"]:
        console.print(f"[red]Error: Invalid type '{item_type}'. Use 'vocab' or 'kanji'.[/red]")
        raise typer.Exit(code=1)

    try:
        if item_type == "vocab":
            _add_vocabulary()
        else:
            _add_kanji()

    except Exception as e:
        console.print(f"\n[red]Error adding flashcard:[/red] {e}")
        raise typer.Exit(code=1)


def _add_vocabulary():
    """Add vocabulary flashcard interactively."""
    # Collect data
    data = prompt_vocabulary_data()

    if data is None:
        console.print("[yellow]No vocabulary added.[/yellow]")
        return

    # Check if this is an existing vocabulary (auto-filled from database)
    if 'id' in data:
        vocab_id = data.pop('id')  # Extract ID and remove from data dict
        console.print(f"\n[yellow]Vocabulary already exists in database (ID: {vocab_id})[/yellow]")
    else:
        # Add to database (new vocabulary)
        vocab_id = add_vocabulary(**data)
        console.print(f"\n[green]✓ Vocabulary added successfully![/green] (ID: {vocab_id})")

    # Ask if user wants to add to review queue
    if confirm_action("Add to review queue for spaced repetition?", default=True):
        scheduler = ReviewScheduler()
        try:
            scheduler.create_new_review(vocab_id, ItemType.VOCAB)
            console.print("[green]✓ Added to review queue[/green]")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not add to review queue: {e}[/yellow]")

    # Show summary
    vocab_dict = get_vocabulary_by_id(vocab_id)
    if vocab_dict:
        vocab = Vocabulary.from_db_row(vocab_dict)
        panel = format_vocabulary_panel(vocab)
        console.print("\n")
        console.print(panel)


def _add_kanji():
    """Add kanji flashcard interactively."""
    # Collect data
    data = prompt_kanji_data()

    if data is None:
        console.print("[yellow]No kanji added.[/yellow]")
        return

    # Check if this is an existing kanji (auto-filled from database)
    if 'id' in data:
        kanji_id = data.pop('id')  # Extract ID and remove from data dict
        console.print(f"\n[yellow]Kanji already exists in database (ID: {kanji_id})[/yellow]")
    else:
        # Add to database (new kanji)
        kanji_id = add_kanji(**data)
        console.print(f"\n[green]✓ Kanji added successfully![/green] (ID: {kanji_id})")

    # Ask if user wants to add to review queue
    if confirm_action("Add to review queue for spaced repetition?", default=True):
        scheduler = ReviewScheduler()
        try:
            scheduler.create_new_review(kanji_id, ItemType.KANJI)
            console.print("[green]✓ Added to review queue[/green]")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not add to review queue: {e}[/yellow]")

    # Show summary
    kanji_dict = get_kanji_by_id(kanji_id)
    if kanji_dict:
        kanji = Kanji.from_db_row(kanji_dict)
        panel = format_kanji_panel(kanji)
        console.print("\n")
        console.print(panel)


@app.command(name="list")
def list_flashcards(
    item_type: str = typer.Option(
        "vocab",
        "--type",
        "-t",
        help="Type of flashcard (vocab or kanji)"
    ),
    jlpt_level: Optional[str] = typer.Option(
        None,
        "--level",
        "-l",
        help="Filter by JLPT level (n5/n4/n3/n2/n1)"
    ),
    limit: int = typer.Option(
        50,
        "--limit",
        help="Maximum number of items to display"
    ),
    offset: int = typer.Option(
        0,
        "--offset",
        help="Number of items to skip (for pagination)"
    ),
):
    """
    List flashcards with optional filters.

    Displays a Rich table of vocabulary or kanji with review status.

    Examples:
        japanese-cli flashcard list --type vocab
        japanese-cli flashcard list --type kanji --level n5
        japanese-cli flashcard list --type vocab --limit 20 --offset 20
    """
    # Validate item type
    if item_type not in ["vocab", "kanji"]:
        console.print(f"[red]Error: Invalid type '{item_type}'. Use 'vocab' or 'kanji'.[/red]")
        raise typer.Exit(code=1)

    # Validate JLPT level
    if jlpt_level and jlpt_level not in ["n5", "n4", "n3", "n2", "n1"]:
        console.print(f"[red]Error: Invalid JLPT level '{jlpt_level}'.[/red]")
        raise typer.Exit(code=1)

    try:
        if item_type == "vocab":
            _list_vocabulary(jlpt_level, limit, offset)
        else:
            _list_kanji(jlpt_level, limit, offset)

    except Exception as e:
        console.print(f"\n[red]Error listing flashcards:[/red] {e}")
        raise typer.Exit(code=1)


def _list_vocabulary(jlpt_level: Optional[str], limit: int, offset: int):
    """List vocabulary flashcards."""
    # Get vocabulary from database
    vocab_dicts = list_vocabulary(
        jlpt_level=jlpt_level,
        limit=limit,
        offset=offset
    )

    if not vocab_dicts:
        console.print("[yellow]No vocabulary found.[/yellow]")
        return

    # Convert to Vocabulary objects
    vocab_list = [Vocabulary.from_db_row(v) for v in vocab_dicts]

    # Get review status for each item
    reviews = {}
    scheduler = ReviewScheduler()
    for vocab in vocab_list:
        review = scheduler.get_review_by_item(vocab.id, ItemType.VOCAB)
        if review:
            reviews[vocab.id] = review

    # Display table
    table = format_vocabulary_table(vocab_list, reviews, show_review_status=True)
    console.print("\n")
    console.print(table)

    # Show pagination info
    if len(vocab_list) == limit:
        console.print(f"\n[dim]Showing items {offset + 1}-{offset + len(vocab_list)}[/dim]")
        console.print(f"[dim]Use --offset {offset + limit} to see more[/dim]")


def _list_kanji(jlpt_level: Optional[str], limit: int, offset: int):
    """List kanji flashcards."""
    # Get kanji from database
    kanji_dicts = list_kanji(
        jlpt_level=jlpt_level,
        limit=limit,
        offset=offset
    )

    if not kanji_dicts:
        console.print("[yellow]No kanji found.[/yellow]")
        return

    # Convert to Kanji objects
    kanji_list = [Kanji.from_db_row(k) for k in kanji_dicts]

    # Get review status for each item
    reviews = {}
    scheduler = ReviewScheduler()
    for kanji in kanji_list:
        review = scheduler.get_review_by_item(kanji.id, ItemType.KANJI)
        if review:
            reviews[kanji.id] = review

    # Display table
    table = format_kanji_table(kanji_list, reviews, show_review_status=True)
    console.print("\n")
    console.print(table)

    # Show pagination info
    if len(kanji_list) == limit:
        console.print(f"\n[dim]Showing items {offset + 1}-{offset + len(kanji_list)}[/dim]")
        console.print(f"[dim]Use --offset {offset + limit} to see more[/dim]")


@app.command(name="show")
def show_flashcard(
    flashcard_id: int = typer.Argument(..., help="ID of flashcard to show"),
    item_type: str = typer.Option(
        "vocab",
        "--type",
        "-t",
        help="Type of flashcard (vocab or kanji)"
    ),
):
    """
    Show detailed information for a single flashcard.

    Displays all fields including meanings, readings, review status, and notes.

    Examples:
        japanese-cli flashcard show 1 --type vocab
        japanese-cli flashcard show 5 --type kanji
    """
    # Validate item type
    if item_type not in ["vocab", "kanji"]:
        console.print(f"[red]Error: Invalid type '{item_type}'. Use 'vocab' or 'kanji'.[/red]")
        raise typer.Exit(code=1)

    try:
        if item_type == "vocab":
            _show_vocabulary(flashcard_id)
        else:
            _show_kanji(flashcard_id)

    except Exception as e:
        console.print(f"\n[red]Error showing flashcard:[/red] {e}")
        raise typer.Exit(code=1)


def _show_vocabulary(vocab_id: int):
    """Show detailed vocabulary information."""
    # Get vocabulary from database
    vocab_dict = get_vocabulary_by_id(vocab_id)

    if vocab_dict is None:
        console.print(f"[red]Error: Vocabulary with ID {vocab_id} not found.[/red]")
        raise typer.Exit(code=1)

    # Check if item has a review entry (is a flashcard)
    if not has_review_entry(vocab_id, "vocab"):
        console.print(f"[yellow]Warning: Vocabulary with ID {vocab_id} exists in database but is not added as a flashcard.[/yellow]")
        console.print("[dim]Use 'flashcard add --type vocab' to add it to the review queue.[/dim]")
        raise typer.Exit(code=1)

    # Convert to Vocabulary object
    vocab = Vocabulary.from_db_row(vocab_dict)

    # Get review status
    scheduler = ReviewScheduler()
    review = scheduler.get_review_by_item(vocab_id, ItemType.VOCAB)

    # Display panel
    panel = format_vocabulary_panel(vocab, review)
    console.print("\n")
    console.print(panel)


def _show_kanji(kanji_id: int):
    """Show detailed kanji information."""
    # Get kanji from database
    kanji_dict = get_kanji_by_id(kanji_id)

    if kanji_dict is None:
        console.print(f"[red]Error: Kanji with ID {kanji_id} not found.[/red]")
        raise typer.Exit(code=1)

    # Check if item has a review entry (is a flashcard)
    if not has_review_entry(kanji_id, "kanji"):
        console.print(f"[yellow]Warning: Kanji with ID {kanji_id} exists in database but is not added as a flashcard.[/yellow]")
        console.print("[dim]Use 'flashcard add --type kanji' to add it to the review queue.[/dim]")
        raise typer.Exit(code=1)

    # Convert to Kanji object
    kanji = Kanji.from_db_row(kanji_dict)

    # Get review status
    scheduler = ReviewScheduler()
    review = scheduler.get_review_by_item(kanji_id, ItemType.KANJI)

    # Display panel
    panel = format_kanji_panel(kanji, review)
    console.print("\n")
    console.print(panel)


@app.command(name="edit")
def edit_flashcard(
    flashcard_id: int = typer.Argument(..., help="ID of flashcard to edit"),
    item_type: str = typer.Option(
        "vocab",
        "--type",
        "-t",
        help="Type of flashcard (vocab or kanji)"
    ),
):
    """
    Edit an existing flashcard interactively.

    Prompts for all fields with current values pre-filled.
    Only updates fields that are changed.

    Examples:
        japanese-cli flashcard edit 1 --type vocab
        japanese-cli flashcard edit 5 --type kanji
    """
    # Validate item type
    if item_type not in ["vocab", "kanji"]:
        console.print(f"[red]Error: Invalid type '{item_type}'. Use 'vocab' or 'kanji'.[/red]")
        raise typer.Exit(code=1)

    try:
        if item_type == "vocab":
            _edit_vocabulary(flashcard_id)
        else:
            _edit_kanji(flashcard_id)

    except Exception as e:
        console.print(f"\n[red]Error editing flashcard:[/red] {e}")
        raise typer.Exit(code=1)


def _edit_vocabulary(vocab_id: int):
    """Edit vocabulary flashcard interactively."""
    # Get existing vocabulary
    vocab_dict = get_vocabulary_by_id(vocab_id)

    if vocab_dict is None:
        console.print(f"[red]Error: Vocabulary with ID {vocab_id} not found.[/red]")
        raise typer.Exit(code=1)

    # Convert to Vocabulary object
    existing_vocab = Vocabulary.from_db_row(vocab_dict)

    # Show current data
    console.print("\n[bold]Current vocabulary:[/bold]")
    panel = format_vocabulary_panel(existing_vocab)
    console.print(panel)
    console.print()

    # Collect updated data
    data = prompt_vocabulary_data(existing=existing_vocab)

    if data is None:
        console.print("[yellow]Edit cancelled.[/yellow]")
        return

    # Confirm update
    if not confirm_action(f"Update vocabulary #{vocab_id}?", default=True):
        console.print("[yellow]Edit cancelled.[/yellow]")
        return

    # Update database
    success = update_vocabulary(vocab_id, **data)

    if success:
        console.print(f"\n[green]✓ Vocabulary #{vocab_id} updated successfully![/green]")

        # Show updated data
        vocab_dict = get_vocabulary_by_id(vocab_id)
        if vocab_dict:
            vocab = Vocabulary.from_db_row(vocab_dict)
            panel = format_vocabulary_panel(vocab)
            console.print("\n")
            console.print(panel)
    else:
        console.print(f"[red]Error: Failed to update vocabulary #{vocab_id}.[/red]")
        raise typer.Exit(code=1)


def _edit_kanji(kanji_id: int):
    """Edit kanji flashcard interactively."""
    # Get existing kanji
    kanji_dict = get_kanji_by_id(kanji_id)

    if kanji_dict is None:
        console.print(f"[red]Error: Kanji with ID {kanji_id} not found.[/red]")
        raise typer.Exit(code=1)

    # Convert to Kanji object
    existing_kanji = Kanji.from_db_row(kanji_dict)

    # Show current data
    console.print("\n[bold]Current kanji:[/bold]")
    panel = format_kanji_panel(existing_kanji)
    console.print(panel)
    console.print()

    # Collect updated data
    data = prompt_kanji_data(existing=existing_kanji)

    if data is None:
        console.print("[yellow]Edit cancelled.[/yellow]")
        return

    # Confirm update
    if not confirm_action(f"Update kanji #{kanji_id}?", default=True):
        console.print("[yellow]Edit cancelled.[/yellow]")
        return

    # Update database
    success = update_kanji(kanji_id, **data)

    if success:
        console.print(f"\n[green]✓ Kanji #{kanji_id} updated successfully![/green]")

        # Show updated data
        kanji_dict = get_kanji_by_id(kanji_id)
        if kanji_dict:
            kanji = Kanji.from_db_row(kanji_dict)
            panel = format_kanji_panel(kanji)
            console.print("\n")
            console.print(panel)
    else:
        console.print(f"[red]Error: Failed to update kanji #{kanji_id}.[/red]")
        raise typer.Exit(code=1)


@app.command(name="review")
def review_flashcards(
    limit: int = typer.Option(
        20,
        "--limit",
        "-n",
        help="Maximum number of cards to review"
    ),
    jlpt_level: Optional[str] = typer.Option(
        None,
        "--level",
        "-l",
        help="Filter by JLPT level (n5/n4/n3/n2/n1)"
    ),
    item_type: Optional[str] = typer.Option(
        None,
        "--type",
        "-t",
        help="Filter by type (vocab or kanji)"
    ),
):
    """
    Start an interactive review session with due flashcards.

    Reviews cards using spaced repetition (FSRS algorithm). For each card,
    you'll see the meaning and try to recall the Japanese word, then rate
    how well you remembered it (1-4).

    Examples:
        japanese-cli flashcard review
        japanese-cli flashcard review --limit 10 --level n5
        japanese-cli flashcard review --type vocab
    """
    # Validate JLPT level
    if jlpt_level and jlpt_level not in ["n5", "n4", "n3", "n2", "n1"]:
        console.print(f"[red]Error: Invalid JLPT level '{jlpt_level}'.[/red]")
        raise typer.Exit(code=1)

    # Validate item type
    if item_type and item_type not in ["vocab", "kanji"]:
        console.print(f"[red]Error: Invalid type '{item_type}'. Use 'vocab' or 'kanji'.[/red]")
        raise typer.Exit(code=1)

    try:
        _run_review_session(limit, jlpt_level, item_type)
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Review session cancelled.[/yellow]")
        raise typer.Exit(code=0)
    except Exception as e:
        console.print(f"\n[red]Error during review session:[/red] {e}")
        raise typer.Exit(code=1)


def _run_review_session(
    limit: int,
    jlpt_level: Optional[str],
    item_type: Optional[str]
):
    """Run the interactive review session."""
    import sys

    scheduler = ReviewScheduler()

    # Convert item_type to ItemType enum if needed
    item_type_enum = None
    if item_type:
        item_type_enum = ItemType.VOCAB if item_type == "vocab" else ItemType.KANJI

    # Get due reviews - with explicit flushing
    console.print("\n[bold cyan]Loading due cards...[/bold cyan]")
    sys.stdout.flush()  # Force output to display immediately

    due_reviews = scheduler.get_due_reviews(
        limit=limit,
        jlpt_level=jlpt_level,
        item_type=item_type_enum
    )

    # Check if any cards are due
    if not due_reviews:
        console.print("\n[green]✓ No cards due for review![/green]")
        console.print("[dim]Great job keeping up with your studies![/dim]")
        sys.stdout.flush()
        return

    # Show session intro
    total_cards = len(due_reviews)
    console.print(f"\n[bold green]Review Session[/bold green]")
    console.print(f"[dim]Found {total_cards} card(s) due for review[/dim]")

    if jlpt_level:
        console.print(f"[dim]Level: {jlpt_level.upper()}[/dim]")
    if item_type:
        console.print(f"[dim]Type: {item_type.capitalize()}[/dim]")

    console.print("\n[dim]Press Ctrl+C at any time to quit (progress will be saved)[/dim]")
    console.print()
    sys.stdout.flush()  # Ensure all intro text is displayed

    # Session statistics
    session_start_time = time.time()
    rating_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    next_review_dates = []
    cards_reviewed = 0

    # Review each card
    for i, review in enumerate(due_reviews, start=1):
        try:
            # Get the vocabulary or kanji item
            if review.item_type == ItemType.VOCAB:
                item_dict = get_vocabulary_by_id(review.item_id)
                if item_dict is None:
                    console.print(f"[yellow]Warning: Vocabulary #{review.item_id} not found, skipping[/yellow]")
                    continue
                item = Vocabulary.from_db_row(item_dict)
                item_type_str = "vocab"
            else:  # ItemType.KANJI
                item_dict = get_kanji_by_id(review.item_id)
                if item_dict is None:
                    console.print(f"[yellow]Warning: Kanji #{review.item_id} not found, skipping[/yellow]")
                    continue
                item = Kanji.from_db_row(item_dict)
                item_type_str = "kanji"

            # Start timing for this card
            card_start_time = time.time()

            # Display question
            question_panel = display_card_question(item, item_type_str, i, total_cards)
            console.print(question_panel)
            sys.stdout.flush()  # Ensure question is displayed

            # Wait for user to press Enter
            input()  # Wait for Enter key
            console.print()

            # Display answer
            answer_panel = display_card_answer(item, item_type_str)
            console.print(answer_panel)
            sys.stdout.flush()  # Ensure answer is displayed

            # Prompt for rating
            rating = prompt_rating()

            # Calculate time spent on this card
            card_duration_ms = int((time.time() - card_start_time) * 1000)

            # Process review
            updated_review = scheduler.process_review(
                review_id=review.id,
                rating=rating,
                duration_ms=card_duration_ms
            )

            # Update statistics
            rating_counts[rating] += 1
            cards_reviewed += 1

            # Store next review date
            word_text = item.word if item_type_str == "vocab" else item.character
            next_review_dates.append((word_text, updated_review.due_date))

            # Clear screen for next card (show separator)
            console.print("\n" + "─" * 60 + "\n")

        except KeyboardInterrupt:
            # User wants to quit early
            raise
        except Exception as e:
            console.print(f"[red]Error processing card:[/red] {e}")
            console.print("[yellow]Skipping to next card...[/yellow]\n")
            continue

    # Calculate total session time
    total_time_seconds = time.time() - session_start_time

    # Display session summary
    if cards_reviewed > 0:
        summary_panel = display_session_summary(
            total_reviewed=cards_reviewed,
            rating_counts=rating_counts,
            total_time_seconds=total_time_seconds,
            next_review_dates=next_review_dates
        )
        console.print(summary_panel)
        sys.stdout.flush()
    else:
        console.print("\n[yellow]No cards were reviewed.[/yellow]")
        sys.stdout.flush()
