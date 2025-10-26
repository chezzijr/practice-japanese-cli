"""
CLI commands for progress tracking and statistics.

Provides commands to view progress dashboard, set JLPT levels, and display
detailed statistics with time-based filtering.
"""

from datetime import date, timedelta
from typing import Optional

import typer
from rich.console import Console

from ..database import (
    get_progress,
    get_due_cards,
    update_progress_level,
)
from ..models import Progress
from ..srs import (
    calculate_vocab_counts_by_level,
    calculate_kanji_counts_by_level,
    calculate_mastered_items,
    calculate_retention_rate,
    calculate_average_review_duration,
    aggregate_daily_review_counts,
    get_most_reviewed_items,
    get_reviews_by_date_range,
)
from ..ui import (
    display_progress_dashboard,
    display_statistics,
)

# Create Typer app for progress commands
app = typer.Typer(
    name="progress",
    help="View progress and statistics",
    no_args_is_help=True,
)

console = Console()


@app.command(name="show")
def show_progress():
    """
    Display progress dashboard with current statistics.

    Shows JLPT levels, study streak, flashcard counts, mastery progress,
    and review statistics with real-time data from the database.

    Example:
        japanese-cli progress show
    """
    try:
        # Load progress from database
        progress_dict = get_progress()

        if progress_dict is None:
            console.print("[red]Error: Progress not initialized. Run 'japanese-cli init' first.[/red]")
            raise typer.Exit(code=1)

        # Convert to Progress model
        progress = Progress.from_db_row(progress_dict)

        # Calculate real-time statistics
        console.print("[dim]Calculating statistics...[/dim]")

        # Vocabulary and kanji counts
        vocab_counts = calculate_vocab_counts_by_level()
        kanji_counts = calculate_kanji_counts_by_level()

        # Mastered items (stability >= 21 days)
        mastered_counts = calculate_mastered_items()

        # Cards due today
        due_cards = get_due_cards(limit=None)  # Get all due cards
        due_today = len(due_cards)

        # Total reviews from review history
        all_reviews = get_reviews_by_date_range()
        total_reviews = len(all_reviews)

        # Retention rate (all-time)
        retention_rate = calculate_retention_rate()

        # Display dashboard
        dashboard = display_progress_dashboard(
            progress=progress,
            vocab_counts=vocab_counts,
            kanji_counts=kanji_counts,
            mastered_counts=mastered_counts,
            due_today=due_today,
            total_reviews=total_reviews,
            retention_rate=retention_rate
        )

        console.print("\n")
        console.print(dashboard)
        console.print()

        # Helpful hints
        if due_today > 0:
            console.print(f"[dim]💡 You have {due_today} card(s) due for review.[/dim]")
            console.print("[dim]   Run 'japanese-cli flashcard review' to start reviewing.[/dim]")
        else:
            console.print("[dim]✨ All caught up! Great work![/dim]")

    except Exception as e:
        console.print(f"\n[red]Error displaying progress:[/red] {e}")
        raise typer.Exit(code=1)


@app.command(name="set-level")
def set_level(
    level: str = typer.Argument(..., help="Target JLPT level (n5/n4/n3/n2/n1)"),
    current: bool = typer.Option(
        False,
        "--current",
        "-c",
        help="Set as current level instead of target level"
    )
):
    """
    Update your current or target JLPT level.

    By default, updates your target level (the level you're working towards).
    Use --current to update your current level (the level you're studying from).

    Examples:
        japanese-cli progress set-level n4          # Set target to N4
        japanese-cli progress set-level n4 --current  # Set current to N4
    """
    # Validate JLPT level
    valid_levels = ["n5", "n4", "n3", "n2", "n1"]
    level_lower = level.lower()

    if level_lower not in valid_levels:
        console.print(f"[red]Error: Invalid JLPT level '{level}'.[/red]")
        console.print(f"[dim]Valid levels: {', '.join(valid_levels)}[/dim]")
        raise typer.Exit(code=1)

    try:
        # Check if progress exists
        progress_dict = get_progress()

        if progress_dict is None:
            console.print("[red]Error: Progress not initialized. Run 'japanese-cli init' first.[/red]")
            raise typer.Exit(code=1)

        # Update level
        if current:
            success = update_progress_level(current_level=level_lower)
            level_type = "current"
        else:
            success = update_progress_level(target_level=level_lower)
            level_type = "target"

        if success:
            console.print(f"\n[green]✓ Updated {level_type} level to {level_lower.upper()}[/green]")

            # Show updated progress
            progress_dict = get_progress()
            progress = Progress.from_db_row(progress_dict)

            console.print()
            console.print(f"Current Level: [cyan]{progress.current_level.upper()}[/cyan]")
            console.print(f"Target Level:  [green]{progress.target_level.upper()}[/green]")
            console.print()
        else:
            console.print("[red]Error: Failed to update level.[/red]")
            raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"\n[red]Error updating level:[/red] {e}")
        raise typer.Exit(code=1)


@app.command(name="stats")
def show_statistics(
    date_range: str = typer.Option(
        "all",
        "--range",
        "-r",
        help="Date range: 7d (last 7 days), 30d (last 30 days), all (all-time)"
    )
):
    """
    Display detailed statistics with time-based filtering.

    Shows total reviews, retention rate, average time per card, daily activity,
    and most reviewed items for the specified time period.

    Examples:
        japanese-cli progress stats                # All-time stats
        japanese-cli progress stats --range 7d     # Last 7 days
        japanese-cli progress stats --range 30d    # Last 30 days
    """
    # Validate and parse date range
    valid_ranges = ["7d", "30d", "all"]
    date_range_lower = date_range.lower()

    if date_range_lower not in valid_ranges:
        console.print(f"[red]Error: Invalid date range '{date_range}'.[/red]")
        console.print(f"[dim]Valid ranges: {', '.join(valid_ranges)}[/dim]")
        raise typer.Exit(code=1)

    try:
        # Calculate date range
        end_date = date.today()
        if date_range_lower == "7d":
            start_date = end_date - timedelta(days=6)  # Last 7 days including today
            range_label = "Last 7 Days"
        elif date_range_lower == "30d":
            start_date = end_date - timedelta(days=29)  # Last 30 days including today
            range_label = "Last 30 Days"
        else:  # all
            start_date = None
            range_label = "All Time"

        # Calculate statistics
        console.print(f"[dim]Calculating statistics for {range_label.lower()}...[/dim]")

        # Get reviews in date range
        if start_date:
            reviews = get_reviews_by_date_range(start_date=start_date, end_date=end_date)
        else:
            reviews = get_reviews_by_date_range()

        total_reviews = len(reviews)

        # Retention rate
        if start_date:
            retention_rate = calculate_retention_rate(start_date=start_date, end_date=end_date)
        else:
            retention_rate = calculate_retention_rate()

        # Average duration
        if start_date:
            avg_duration = calculate_average_review_duration(start_date=start_date, end_date=end_date)
        else:
            avg_duration = calculate_average_review_duration()

        # Daily counts
        if start_date:
            daily_counts = aggregate_daily_review_counts(start_date=start_date, end_date=end_date)
        else:
            # For all-time, show last 30 days of daily counts
            thirty_days_ago = end_date - timedelta(days=29)
            daily_counts = aggregate_daily_review_counts(start_date=thirty_days_ago, end_date=end_date)

        # Most reviewed items
        most_reviewed = get_most_reviewed_items(limit=10)

        # Display statistics
        stats_panel = display_statistics(
            total_reviews=total_reviews,
            retention_rate=retention_rate,
            avg_duration_seconds=avg_duration,
            daily_counts=daily_counts,
            most_reviewed=most_reviewed,
            date_range_label=range_label
        )

        console.print("\n")
        console.print(stats_panel)
        console.print()

        # Helpful hints
        if total_reviews == 0:
            console.print("[dim]💡 No reviews found in this time period.[/dim]")
            console.print("[dim]   Start reviewing to build your statistics![/dim]")
        elif retention_rate < 70.0:
            console.print("[dim]💡 Retention rate is below 70%. Try reviewing more frequently![/dim]")
        elif retention_rate >= 85.0:
            console.print("[dim]✨ Excellent retention rate! Keep up the great work![/dim]")

    except Exception as e:
        console.print(f"\n[red]Error displaying statistics:[/red] {e}")
        raise typer.Exit(code=1)
