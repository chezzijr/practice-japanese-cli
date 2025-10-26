"""
CLI commands for flashcard management.

Provides commands to add, list, edit, and review flashcards (vocabulary and kanji).
"""

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

    # Add to database
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

    # Add to database
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
