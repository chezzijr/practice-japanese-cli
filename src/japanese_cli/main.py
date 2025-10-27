"""
Japanese Learning CLI - Main entry point

A CLI application for learning Japanese with FSRS spaced repetition.
"""

import typer
from rich.console import Console
from rich.panel import Panel

from japanese_cli.database import (
    ensure_data_directory,
    get_db_path,
    initialize_database,
    get_progress,
    init_progress,
    database_exists,
)
from japanese_cli.cli import import_data, flashcard, progress, grammar, mcq, chat_command

# Initialize console for rich output
console = Console()

# Create main Typer app
app = typer.Typer(
    name="japanese-cli",
    help="Japanese learning CLI with FSRS spaced repetition",
    add_completion=False,
)

# Register subcommands
app.add_typer(import_data.app, name="import")
app.add_typer(flashcard.app, name="flashcard")
app.add_typer(progress.app, name="progress")
app.add_typer(grammar.app, name="grammar")
app.add_typer(chat_command.app, name="chat")

# Register MCQ command (single command, not a group)
app.command(name="mcq", help="Start an interactive multiple-choice question (MCQ) review session")(mcq.mcq)


@app.command()
def version():
    """Show version information"""
    console.print("[bold cyan]Japanese Learning CLI[/bold cyan] v0.1.0")
    console.print("A CLI tool for learning Japanese with spaced repetition")


@app.command()
def init():
    """Initialize the database and data directories"""
    console.print("\n[bold cyan]Initializing Japanese Learning CLI...[/bold cyan]\n")

    try:
        # Step 1: Ensure data directories exist
        console.print("📁 Creating data directories...", end=" ")
        ensure_data_directory()
        console.print("[green]✓[/green]")

        # Step 2: Check if database already exists
        db_path = get_db_path()
        already_exists = database_exists(db_path)

        if already_exists:
            console.print(f"📊 Database already exists at [dim]{db_path}[/dim]")
        else:
            console.print(f"📊 Creating database at [dim]{db_path}[/dim]...", end=" ")

        # Step 3: Initialize database (creates tables if needed)
        was_created = initialize_database(db_path)

        if was_created:
            console.print("[green]✓[/green]")
            console.print("🗄️  Database schema created successfully")
        else:
            console.print("[green]✓[/green] Database is up to date")

        # Step 4: Initialize progress if needed
        progress = get_progress()
        if progress is None:
            console.print("📈 Initializing progress tracking...", end=" ")
            init_progress()
            console.print("[green]✓[/green]")

        # Success message
        console.print()
        success_panel = Panel(
            "[green]✓ Initialization complete![/green]\n\n"
            "[bold]Database location:[/bold]\n"
            f"  [dim]{db_path}[/dim]\n\n"
            "[bold]Next steps:[/bold]\n"
            "  1. Import N5 data: [cyan]japanese-cli import n5 --vocab --kanji[/cyan]\n"
            "  2. Add flashcards: [cyan]japanese-cli flashcard add[/cyan]\n"
            "  3. Start reviewing: [cyan]japanese-cli flashcard review[/cyan]",
            title="🎌 Japanese Learning CLI",
            border_style="green"
        )
        console.print(success_panel)

    except Exception as e:
        console.print(f"\n[red]✗ Initialization failed:[/red] {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
