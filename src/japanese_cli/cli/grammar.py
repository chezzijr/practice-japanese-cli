"""
CLI commands for grammar point management.

Provides commands to add, list, and view grammar points with examples.
"""

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from ..database import (
    add_grammar,
    get_grammar_by_id,
    list_grammar,
    update_grammar,
)
from ..models import GrammarPoint
from ..ui import (
    prompt_grammar_data,
    format_grammar_table,
    format_grammar_panel,
)

# Create Typer app for grammar commands
app = typer.Typer(
    name="grammar",
    help="Manage grammar points",
    no_args_is_help=True,
)

console = Console()


@app.command(name="add")
def add_grammar_point():
    """
    Add a new grammar point interactively.

    Prompts for title, structure, explanation, JLPT level, examples, and notes.
    Validates input and saves to database.

    Examples:
        japanese-cli grammar add
    """
    try:
        _add_grammar_point()
    except Exception as e:
        console.print(f"\n[red]Error adding grammar point:[/red] {e}")
        raise typer.Exit(code=1)


def _add_grammar_point():
    """Add grammar point interactively."""
    # Collect data
    data = prompt_grammar_data()

    if data is None:
        console.print("[yellow]No grammar point added.[/yellow]")
        return

    # Add to database
    grammar_id = add_grammar(**data)

    console.print(f"\n[green]✓ Grammar point added successfully![/green] (ID: {grammar_id})")

    # Show summary
    grammar_dict = get_grammar_by_id(grammar_id)
    if grammar_dict:
        grammar = GrammarPoint.from_db_row(grammar_dict)
        panel = format_grammar_panel(grammar)
        console.print("\n")
        console.print(panel)


@app.command(name="list")
def list_grammar_points(
    level: Optional[str] = typer.Option(
        None,
        "--level",
        "-l",
        help="Filter by JLPT level (n5/n4/n3/n2/n1)"
    ),
    limit: Optional[int] = typer.Option(
        None,
        "--limit",
        help="Maximum number of results"
    ),
    offset: int = typer.Option(
        0,
        "--offset",
        help="Number of results to skip"
    ),
):
    """
    List grammar points with optional filtering.

    Display a table of grammar points with ID, title, structure, JLPT level,
    and example count. Can filter by JLPT level and paginate results.

    Examples:
        japanese-cli grammar list
        japanese-cli grammar list --level n5
        japanese-cli grammar list --limit 10
        japanese-cli grammar list --level n4 --limit 20
    """
    try:
        # Validate JLPT level
        if level and level not in ["n5", "n4", "n3", "n2", "n1"]:
            console.print(f"[red]Error: Invalid JLPT level '{level}'. Use n5/n4/n3/n2/n1.[/red]")
            raise typer.Exit(code=1)

        # Get grammar points from database
        grammar_dicts = list_grammar(
            jlpt_level=level,
            limit=limit,
            offset=offset
        )

        if not grammar_dicts:
            console.print("\n[yellow]No grammar points found.[/yellow]")
            if level:
                console.print(f"[dim]Try removing the JLPT level filter (--level {level})[/dim]")
            console.print("[dim]Add grammar points with:[/dim] [cyan]japanese-cli grammar add[/cyan]")
            return

        # Convert to GrammarPoint objects
        grammar_list = [GrammarPoint.from_db_row(g) for g in grammar_dicts]

        # Display table
        table = format_grammar_table(grammar_list)
        console.print("\n")
        console.print(table)

        # Show summary info
        console.print(f"\n[dim]Showing {len(grammar_list)} grammar point(s)[/dim]")
        if level:
            console.print(f"[dim]Filtered by JLPT level: {level.upper()}[/dim]")
        if limit:
            console.print(f"[dim]Limited to {limit} results (offset: {offset})[/dim]")

    except Exception as e:
        console.print(f"\n[red]Error listing grammar points:[/red] {e}")
        raise typer.Exit(code=1)


@app.command(name="show")
def show_grammar_point(
    grammar_id: int = typer.Argument(
        ...,
        help="Grammar point ID to display"
    ),
):
    """
    Show detailed information for a grammar point.

    Displays all details including title, structure, explanation, examples
    with translations, related grammar, and notes.

    Examples:
        japanese-cli grammar show 1
        japanese-cli grammar show 42
    """
    try:
        # Get grammar point from database
        grammar_dict = get_grammar_by_id(grammar_id)

        if not grammar_dict:
            console.print(f"\n[red]Error: Grammar point with ID {grammar_id} not found.[/red]")
            console.print("[dim]Use[/dim] [cyan]japanese-cli grammar list[/cyan] [dim]to see available grammar points[/dim]")
            raise typer.Exit(code=1)

        # Convert to GrammarPoint object
        grammar = GrammarPoint.from_db_row(grammar_dict)

        # Display panel
        panel = format_grammar_panel(grammar)
        console.print("\n")
        console.print(panel)

    except Exception as e:
        console.print(f"\n[red]Error showing grammar point:[/red] {e}")
        raise typer.Exit(code=1)


@app.command(name="edit")
def edit_grammar_point(
    grammar_id: int = typer.Argument(
        ...,
        help="Grammar point ID to edit"
    ),
):
    """
    Edit an existing grammar point interactively.

    Prompts for all fields with current values pre-filled. User can update
    any field or keep existing values.

    Examples:
        japanese-cli grammar edit 1
        japanese-cli grammar edit 42
    """
    try:
        _edit_grammar_point(grammar_id)
    except Exception as e:
        console.print(f"\n[red]Error editing grammar point:[/red] {e}")
        raise typer.Exit(code=1)


def _edit_grammar_point(grammar_id: int):
    """Edit grammar point interactively."""
    # Get existing grammar point
    grammar_dict = get_grammar_by_id(grammar_id)

    if not grammar_dict:
        console.print(f"\n[red]Error: Grammar point with ID {grammar_id} not found.[/red]")
        console.print("[dim]Use[/dim] [cyan]japanese-cli grammar list[/cyan] [dim]to see available grammar points[/dim]")
        raise typer.Exit(code=1)

    # Convert to GrammarPoint object
    existing = GrammarPoint.from_db_row(grammar_dict)

    # Show current grammar point
    console.print("\n[bold]Current grammar point:[/bold]")
    panel = format_grammar_panel(existing)
    console.print(panel)
    console.print()

    # Collect updated data
    data = prompt_grammar_data(existing=existing)

    if data is None:
        console.print("[yellow]Edit cancelled. No changes made.[/yellow]")
        return

    # Update in database
    success = update_grammar(grammar_id, **data)

    if success:
        console.print(f"\n[green]✓ Grammar point updated successfully![/green] (ID: {grammar_id})")

        # Show updated grammar point
        updated_dict = get_grammar_by_id(grammar_id)
        if updated_dict:
            updated = GrammarPoint.from_db_row(updated_dict)
            panel = format_grammar_panel(updated)
            console.print("\n")
            console.print(panel)
    else:
        console.print(f"[red]Error: Failed to update grammar point {grammar_id}[/red]")
        raise typer.Exit(code=1)
