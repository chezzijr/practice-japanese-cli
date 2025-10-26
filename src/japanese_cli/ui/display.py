"""
Rich display utilities for flashcard data.

Provides functions to create Rich tables, panels, and formatted output
for vocabulary, kanji, and other learning materials.
"""

from datetime import datetime, timezone, date, timedelta
from typing import Optional, Any

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..models import Vocabulary, Kanji, Review, GrammarPoint, Example
from .furigana import render_furigana, format_kanji_with_readings


# JLPT level color mapping
JLPT_COLORS = {
    "n5": "green",
    "n4": "cyan",
    "n3": "yellow",
    "n2": "magenta",
    "n1": "red",
}


def format_vocabulary_table(
    vocab_list: list[Vocabulary],
    reviews: Optional[dict[int, Review]] = None,
    show_review_status: bool = True
) -> Table:
    """
    Create a Rich table displaying vocabulary list.

    Args:
        vocab_list: List of Vocabulary objects
        reviews: Optional dict mapping vocab_id to Review object
        show_review_status: Whether to show review status column

    Returns:
        Rich Table object ready for console.print()

    Example:
        >>> vocab_list = list_vocabulary(jlpt_level='n5', limit=10)
        >>> table = format_vocabulary_table(vocab_list)
        >>> console.print(table)
    """
    table = Table(title="📚 Vocabulary", show_header=True, header_style="bold magenta")

    # Columns
    table.add_column("ID", style="dim", width=6)
    table.add_column("Word", style="bold cyan", width=20)
    table.add_column("Meaning (VI)", style="green", width=30)
    table.add_column("JLPT", justify="center", width=6)

    if show_review_status and reviews is not None:
        table.add_column("Review", style="yellow", width=15)

    # Rows
    for vocab in vocab_list:
        # Get Vietnamese meaning (first one if multiple)
        vi_meanings = vocab.meanings.get("vi", [])
        vi_meaning = vi_meanings[0] if vi_meanings else ""

        # Get JLPT level color
        jlpt_color = JLPT_COLORS.get(vocab.jlpt_level or "", "white")
        jlpt_display = vocab.jlpt_level.upper() if vocab.jlpt_level else "-"

        # Format word with furigana
        word_text = render_furigana(vocab.word, vocab.reading)

        row = [
            str(vocab.id),
            word_text,
            vi_meaning,
            f"[{jlpt_color}]{jlpt_display}[/{jlpt_color}]",
        ]

        # Add review status if applicable
        if show_review_status and reviews is not None:
            review = reviews.get(vocab.id)
            if review:
                due_date = review.due_date
                now = datetime.now(timezone.utc)
                if due_date <= now:
                    status = "[red]Due now[/red]"
                else:
                    days = (due_date - now).days
                    status = f"[dim]In {days}d[/dim]"
            else:
                status = "[dim]-[/dim]"
            row.append(status)

        table.add_row(*row)

    return table


def format_kanji_table(
    kanji_list: list[Kanji],
    reviews: Optional[dict[int, Review]] = None,
    show_review_status: bool = True
) -> Table:
    """
    Create a Rich table displaying kanji list.

    Args:
        kanji_list: List of Kanji objects
        reviews: Optional dict mapping kanji_id to Review object
        show_review_status: Whether to show review status column

    Returns:
        Rich Table object ready for console.print()

    Example:
        >>> kanji_list = list_kanji(jlpt_level='n5', limit=10)
        >>> table = format_kanji_table(kanji_list)
        >>> console.print(table)
    """
    table = Table(title="㊙️ Kanji", show_header=True, header_style="bold magenta")

    # Columns
    table.add_column("ID", style="dim", width=6)
    table.add_column("Kanji", style="bold bright_cyan", width=8)
    table.add_column("Readings", width=30)
    table.add_column("Meaning (VI)", style="green", width=25)
    table.add_column("JLPT", justify="center", width=6)

    if show_review_status and reviews is not None:
        table.add_column("Review", style="yellow", width=15)

    # Rows
    for kanji in kanji_list:
        # Get Vietnamese meaning (first one if multiple)
        vi_meanings = kanji.meanings.get("vi", [])
        vi_meaning = vi_meanings[0] if vi_meanings else ""

        # Get JLPT level color
        jlpt_color = JLPT_COLORS.get(kanji.jlpt_level or "", "white")
        jlpt_display = kanji.jlpt_level.upper() if kanji.jlpt_level else "-"

        # Format readings
        readings = format_kanji_with_readings(
            kanji.character,
            kanji.on_readings,
            kanji.kun_readings,
            style="compact"
        )
        # Extract just the readings part (without the character)
        on_str = ", ".join(kanji.on_readings) if kanji.on_readings else "-"
        kun_str = ", ".join(kanji.kun_readings) if kanji.kun_readings else "-"
        readings_text = Text()
        if kanji.on_readings:
            readings_text.append("音: ", style="dim")
            readings_text.append(on_str, style="magenta")
        if kanji.kun_readings:
            if kanji.on_readings:
                readings_text.append(" ", style="")
            readings_text.append("訓: ", style="dim")
            readings_text.append(kun_str, style="yellow")

        row = [
            str(kanji.id),
            kanji.character,
            readings_text,
            vi_meaning,
            f"[{jlpt_color}]{jlpt_display}[/{jlpt_color}]",
        ]

        # Add review status if applicable
        if show_review_status and reviews is not None:
            review = reviews.get(kanji.id)
            if review:
                due_date = review.due_date
                now = datetime.now(timezone.utc)
                if due_date <= now:
                    status = "[red]Due now[/red]"
                else:
                    days = (due_date - now).days
                    status = f"[dim]In {days}d[/dim]"
            else:
                status = "[dim]-[/dim]"
            row.append(status)

        table.add_row(*row)

    return table


def format_vocabulary_panel(vocab: Vocabulary, review: Optional[Review] = None) -> Panel:
    """
    Create a Rich panel with detailed vocabulary information.

    Args:
        vocab: Vocabulary object
        review: Optional Review object for this vocabulary

    Returns:
        Rich Panel with all vocabulary details

    Example:
        >>> vocab = get_vocabulary_by_id(1)
        >>> panel = format_vocabulary_panel(vocab)
        >>> console.print(panel)
    """
    content_lines = []

    # Word with furigana (convert Text to string markup)
    content_lines.append(f"[bold bright_cyan]{vocab.word}[/bold bright_cyan] [dim white]([/dim white][bright_yellow]{vocab.reading}[/bright_yellow][dim white])[/dim white]")
    content_lines.append("")

    # Vietnamese reading if available
    if vocab.vietnamese_reading:
        content_lines.append(f"[dim]Hán Việt:[/dim] [cyan]{vocab.vietnamese_reading}[/cyan]")
        content_lines.append("")

    # Meanings
    content_lines.append("[bold]Meanings:[/bold]")
    for lang, meanings_list in vocab.meanings.items():
        lang_display = lang.upper()
        for meaning in meanings_list:
            if lang == "vi":
                content_lines.append(f"  [{lang_display}] [green]{meaning}[/green]")
            else:
                content_lines.append(f"  [{lang_display}] [dim]{meaning}[/dim]")
    content_lines.append("")

    # Metadata
    if vocab.part_of_speech:
        content_lines.append(f"[dim]Part of speech:[/dim] {vocab.part_of_speech}")

    if vocab.jlpt_level:
        jlpt_color = JLPT_COLORS.get(vocab.jlpt_level, "white")
        content_lines.append(f"[dim]JLPT level:[/dim] [{jlpt_color}]{vocab.jlpt_level.upper()}[/{jlpt_color}]")

    if vocab.tags:
        content_lines.append(f"[dim]Tags:[/dim] {', '.join(vocab.tags)}")

    # Review status
    if review:
        content_lines.append("")
        content_lines.append("[bold]Review Status:[/bold]")
        due_date = review.due_date
        now = datetime.now(timezone.utc)
        if due_date <= now:
            content_lines.append(f"  [red]Due now![/red]")
        else:
            days = (due_date - now).days
            content_lines.append(f"  Next review in [yellow]{days}[/yellow] days")
        content_lines.append(f"  Total reviews: {review.review_count}")

    # Notes
    if vocab.notes:
        content_lines.append("")
        content_lines.append(f"[dim italic]Notes: {vocab.notes}[/dim italic]")

    # Create panel
    title = f"📚 Vocabulary #{vocab.id}"
    panel = Panel(
        "\n".join(content_lines),
        title=title,
        border_style="cyan",
        expand=False
    )

    return panel


def format_kanji_panel(kanji: Kanji, review: Optional[Review] = None) -> Panel:
    """
    Create a Rich panel with detailed kanji information.

    Args:
        kanji: Kanji object
        review: Optional Review object for this kanji

    Returns:
        Rich Panel with all kanji details

    Example:
        >>> kanji = get_kanji_by_id(1)
        >>> panel = format_kanji_panel(kanji)
        >>> console.print(panel)
    """
    content_lines = []

    # Kanji character (large)
    content_lines.append(f"[bold bright_cyan]{kanji.character}[/bold bright_cyan]")
    content_lines.append("")

    # Readings
    content_lines.append("[bold]Readings:[/bold]")
    if kanji.on_readings:
        on_text = ", ".join(kanji.on_readings)
        content_lines.append(f"  [dim]音読み (On-yomi):[/dim] [magenta]{on_text}[/magenta]")
    if kanji.kun_readings:
        kun_text = ", ".join(kanji.kun_readings)
        content_lines.append(f"  [dim]訓読み (Kun-yomi):[/dim] [yellow]{kun_text}[/yellow]")
    if kanji.vietnamese_reading:
        content_lines.append(f"  [dim]Hán Việt:[/dim] [cyan]{kanji.vietnamese_reading}[/cyan]")
    content_lines.append("")

    # Meanings
    content_lines.append("[bold]Meanings:[/bold]")
    for lang, meanings_list in kanji.meanings.items():
        lang_display = lang.upper()
        for meaning in meanings_list:
            if lang == "vi":
                content_lines.append(f"  [{lang_display}] [green]{meaning}[/green]")
            else:
                content_lines.append(f"  [{lang_display}] [dim]{meaning}[/dim]")
    content_lines.append("")

    # Metadata
    if kanji.stroke_count:
        content_lines.append(f"[dim]Strokes:[/dim] {kanji.stroke_count}")

    if kanji.radical:
        content_lines.append(f"[dim]Radical:[/dim] {kanji.radical}")

    if kanji.jlpt_level:
        jlpt_color = JLPT_COLORS.get(kanji.jlpt_level, "white")
        content_lines.append(f"[dim]JLPT level:[/dim] [{jlpt_color}]{kanji.jlpt_level.upper()}[/{jlpt_color}]")

    # Review status
    if review:
        content_lines.append("")
        content_lines.append("[bold]Review Status:[/bold]")
        due_date = review.due_date
        now = datetime.now(timezone.utc)
        if due_date <= now:
            content_lines.append(f"  [red]Due now![/red]")
        else:
            days = (due_date - now).days
            content_lines.append(f"  Next review in [yellow]{days}[/yellow] days")
        content_lines.append(f"  Total reviews: {review.review_count}")

    # Notes
    if kanji.notes:
        content_lines.append("")
        content_lines.append(f"[dim italic]Notes: {kanji.notes}[/dim italic]")

    # Create panel
    title = f"㊙️ Kanji #{kanji.id}"
    panel = Panel(
        "\n".join(content_lines),
        title=title,
        border_style="bright_cyan",
        expand=False
    )

    return panel


def display_card_question(
    item: Vocabulary | Kanji,
    item_type: str,
    current: int,
    total: int
) -> Panel:
    """
    Display the question side of a flashcard during review.

    Shows the meaning(s) and asks the user to recall the Japanese word/kanji.

    Args:
        item: Vocabulary or Kanji object
        item_type: "vocab" or "kanji"
        current: Current card number (1-indexed)
        total: Total cards in session

    Returns:
        Rich Panel with question display

    Example:
        >>> vocab = get_vocabulary_by_id(1)
        >>> panel = display_card_question(vocab, "vocab", 1, 20)
        >>> console.print(panel)
    """
    content_lines = []

    # Progress indicator
    content_lines.append(f"[dim]Card {current} of {total}[/dim]")
    content_lines.append("")

    # Vietnamese meaning (primary)
    vi_meanings = item.meanings.get("vi", [])
    if vi_meanings:
        content_lines.append("[bold green]Vietnamese:[/bold green]")
        for meaning in vi_meanings:
            content_lines.append(f"  [green]{meaning}[/green]")
        content_lines.append("")

    # English meaning (secondary)
    en_meanings = item.meanings.get("en", [])
    if en_meanings:
        content_lines.append("[dim]English:[/dim]")
        for meaning in en_meanings:
            content_lines.append(f"  [dim]{meaning}[/dim]")
        content_lines.append("")

    # Metadata hints
    hints = []
    if item.jlpt_level:
        jlpt_color = JLPT_COLORS.get(item.jlpt_level, "white")
        hints.append(f"[{jlpt_color}]{item.jlpt_level.upper()}[/{jlpt_color}]")

    if item_type == "vocab" and hasattr(item, 'part_of_speech') and item.part_of_speech:
        hints.append(f"[dim]{item.part_of_speech}[/dim]")

    if item_type == "kanji" and hasattr(item, 'stroke_count') and item.stroke_count:
        hints.append(f"[dim]{item.stroke_count} strokes[/dim]")

    if hints:
        content_lines.append(" · ".join(hints))

    # Instruction
    content_lines.append("")
    content_lines.append("[dim italic]Press Enter to reveal answer...[/dim italic]")

    # Create panel
    icon = "📚" if item_type == "vocab" else "㊙️"
    title = f"{icon} What is this in Japanese?"
    panel = Panel(
        "\n".join(content_lines),
        title=title,
        border_style="yellow",
        expand=False
    )

    return panel


def display_card_answer(
    item: Vocabulary | Kanji,
    item_type: str,
) -> Panel:
    """
    Display the answer side of a flashcard during review.

    Shows the full details including Japanese word/kanji, readings, and all meanings.

    Args:
        item: Vocabulary or Kanji object
        item_type: "vocab" or "kanji"

    Returns:
        Rich Panel with answer display

    Example:
        >>> vocab = get_vocabulary_by_id(1)
        >>> panel = display_card_answer(vocab, "vocab")
        >>> console.print(panel)
    """
    content_lines = []

    if item_type == "vocab":
        # Vocabulary answer
        content_lines.append(
            f"[bold bright_cyan]{item.word}[/bold bright_cyan] "
            f"[dim white]([/dim white][bright_yellow]{item.reading}[/bright_yellow][dim white])[/dim white]"
        )
        content_lines.append("")

        # Vietnamese reading if available
        if item.vietnamese_reading:
            content_lines.append(f"[dim]Hán Việt:[/dim] [cyan]{item.vietnamese_reading}[/cyan]")
            content_lines.append("")

    else:  # kanji
        # Kanji answer
        content_lines.append(f"[bold bright_cyan]{item.character}[/bold bright_cyan]")
        content_lines.append("")

        # Readings
        content_lines.append("[bold]Readings:[/bold]")
        if item.on_readings:
            on_text = ", ".join(item.on_readings)
            content_lines.append(f"  [dim]音読み:[/dim] [magenta]{on_text}[/magenta]")
        if item.kun_readings:
            kun_text = ", ".join(item.kun_readings)
            content_lines.append(f"  [dim]訓読み:[/dim] [yellow]{kun_text}[/yellow]")
        if item.vietnamese_reading:
            content_lines.append(f"  [dim]Hán Việt:[/dim] [cyan]{item.vietnamese_reading}[/cyan]")
        content_lines.append("")

    # Meanings
    content_lines.append("[bold]Meanings:[/bold]")
    for lang, meanings_list in item.meanings.items():
        lang_display = lang.upper()
        for meaning in meanings_list:
            if lang == "vi":
                content_lines.append(f"  [{lang_display}] [green]{meaning}[/green]")
            else:
                content_lines.append(f"  [{lang_display}] [dim]{meaning}[/dim]")

    # Create panel
    icon = "📚" if item_type == "vocab" else "㊙️"
    title = f"{icon} Answer"
    panel = Panel(
        "\n".join(content_lines),
        title=title,
        border_style="cyan",
        expand=False
    )

    return panel


def prompt_rating() -> int:
    """
    Prompt user to rate how well they recalled the flashcard.

    Displays rating guide and validates input (1-4 only).

    Returns:
        int: Rating from 1-4
            1 = Again (forgot completely)
            2 = Hard (difficult to recall)
            3 = Good (recalled correctly)
            4 = Easy (very easy to recall)

    Example:
        >>> rating = prompt_rating()
        >>> # User enters 3
        >>> print(rating)  # 3
    """
    from rich.prompt import IntPrompt

    # Display rating guide
    guide = Table.grid(padding=(0, 2))
    guide.add_column(style="bold", justify="right")
    guide.add_column()

    guide.add_row("[red]1[/red]", "[dim]Again[/dim] - Forgot completely")
    guide.add_row("[yellow]2[/yellow]", "[dim]Hard[/dim] - Difficult to recall")
    guide.add_row("[green]3[/green]", "[dim]Good[/dim] - Recalled correctly")
    guide.add_row("[cyan]4[/cyan]", "[dim]Easy[/dim] - Very easy to recall")

    console = Console()
    console.print("")
    console.print(guide)
    console.print("")

    # Prompt for rating with validation
    while True:
        try:
            rating = IntPrompt.ask(
                "[bold]Rate your recall[/bold]",
                default=3
            )
            if rating in [1, 2, 3, 4]:
                return rating
            else:
                console.print("[red]Please enter a number between 1 and 4[/red]")
        except KeyboardInterrupt:
            console.print("\n[yellow]Session cancelled[/yellow]")
            raise
        except Exception:
            console.print("[red]Please enter a valid number (1-4)[/red]")


def display_session_summary(
    total_reviewed: int,
    rating_counts: dict[int, int],
    total_time_seconds: float,
    next_review_dates: list[tuple[str, datetime]],
) -> Panel:
    """
    Display summary statistics after a review session.

    Args:
        total_reviewed: Total number of cards reviewed
        rating_counts: Dictionary mapping rating (1-4) to count
        total_time_seconds: Total session duration in seconds
        next_review_dates: List of (word/kanji, due_date) tuples

    Returns:
        Rich Panel with session summary

    Example:
        >>> rating_counts = {1: 2, 2: 3, 3: 10, 4: 5}
        >>> next_dates = [("単語", datetime.now()), ...]
        >>> panel = display_session_summary(20, rating_counts, 300.5, next_dates)
        >>> console.print(panel)
    """
    content_lines = []

    # Header
    content_lines.append(f"[bold green]✓ Review session complete![/bold green]")
    content_lines.append("")

    # Cards reviewed
    content_lines.append(f"[bold]Cards reviewed:[/bold] {total_reviewed}")
    content_lines.append("")

    # Ratings distribution
    content_lines.append("[bold]Ratings:[/bold]")
    again_count = rating_counts.get(1, 0)
    hard_count = rating_counts.get(2, 0)
    good_count = rating_counts.get(3, 0)
    easy_count = rating_counts.get(4, 0)

    content_lines.append(f"  [red]Again (1):[/red] {again_count}")
    content_lines.append(f"  [yellow]Hard (2):[/yellow] {hard_count}")
    content_lines.append(f"  [green]Good (3):[/green] {good_count}")
    content_lines.append(f"  [cyan]Easy (4):[/cyan] {easy_count}")
    content_lines.append("")

    # Accuracy rate
    if total_reviewed > 0:
        accuracy = ((good_count + easy_count) / total_reviewed) * 100
        content_lines.append(f"[bold]Accuracy:[/bold] {accuracy:.1f}% (Good + Easy)")
        content_lines.append("")

    # Time statistics
    avg_time = total_time_seconds / total_reviewed if total_reviewed > 0 else 0
    minutes = int(total_time_seconds // 60)
    seconds = int(total_time_seconds % 60)
    content_lines.append(f"[bold]Time:[/bold] {minutes}m {seconds}s total")
    content_lines.append(f"[dim]Average per card: {avg_time:.1f}s[/dim]")
    content_lines.append("")

    # Next review preview (first 5)
    if next_review_dates:
        content_lines.append("[bold]Next reviews:[/bold]")
        now = datetime.now(timezone.utc)
        for word, due_date in next_review_dates[:5]:
            days = (due_date - now).days
            if days == 0:
                time_str = "[red]Due now[/red]"
            elif days == 1:
                time_str = "[yellow]Tomorrow[/yellow]"
            else:
                time_str = f"[dim]In {days} days[/dim]"
            content_lines.append(f"  {word}: {time_str}")

        if len(next_review_dates) > 5:
            content_lines.append(f"  [dim]... and {len(next_review_dates) - 5} more[/dim]")

    # Create panel
    panel = Panel(
        "\n".join(content_lines),
        title="📊 Session Summary",
        border_style="green",
        expand=False
    )

    return panel


# ============================================================================
# Progress Dashboard Display
# ============================================================================

def display_progress_dashboard(
    progress: Any,  # Progress model
    vocab_counts: dict[str, int],
    kanji_counts: dict[str, int],
    mastered_counts: dict[str, int],
    due_today: int,
    total_reviews: int,
    retention_rate: float
) -> Panel:
    """
    Display progress dashboard with Rich panel.

    Shows current/target level, study streak, item counts, and key statistics.

    Args:
        progress: Progress model instance
        vocab_counts: Vocab counts by level (from calculate_vocab_counts_by_level)
        kanji_counts: Kanji counts by level (from calculate_kanji_counts_by_level)
        mastered_counts: Mastered item counts by type
        due_today: Number of cards due for review today
        total_reviews: Total reviews completed
        retention_rate: Retention rate percentage (0-100)

    Returns:
        Panel: Rich panel with dashboard content

    Example:
        panel = display_progress_dashboard(
            progress=progress,
            vocab_counts={"n5": 81, "total": 81},
            kanji_counts={"n5": 103, "total": 103},
            mastered_counts={"vocab": 50, "kanji": 20, "total": 70},
            due_today=15,
            total_reviews=500,
            retention_rate=85.5
        )
    """
    from ..models import Progress

    # Ensure progress is a Progress model
    if not isinstance(progress, Progress):
        raise TypeError(f"Expected Progress model, got {type(progress)}")

    # Build content lines
    content_lines = []

    # Level information
    current_level_color = JLPT_COLORS.get(progress.current_level, "white")
    target_level_color = JLPT_COLORS.get(progress.target_level, "white")

    content_lines.append("[bold]📚 Study Progress[/bold]")
    content_lines.append("")
    content_lines.append(
        f"Current Level: [{current_level_color}]{progress.current_level.upper()}[/{current_level_color}]"
    )
    content_lines.append(
        f"Target Level:  [{target_level_color}]{progress.target_level.upper()}[/{target_level_color}]"
    )
    content_lines.append("")

    # Study streak
    if progress.streak_days > 0:
        streak_emoji = "🔥" if progress.streak_days >= 7 else "⭐"
        content_lines.append(
            f"{streak_emoji} Study Streak: [bold yellow]{progress.streak_days}[/bold yellow] "
            f"day{'s' if progress.streak_days != 1 else ''}"
        )
    else:
        content_lines.append("⭐ Study Streak: [dim]0 days (start reviewing!)[/dim]")

    # Last review date
    if progress.last_review_date:
        days_ago = (date.today() - progress.last_review_date).days
        if days_ago == 0:
            time_str = "[green]Today[/green]"
        elif days_ago == 1:
            time_str = "[yellow]Yesterday[/yellow]"
        else:
            time_str = f"[dim]{days_ago} days ago[/dim]"
        content_lines.append(f"Last Review: {time_str}")
    else:
        content_lines.append("Last Review: [dim]Never[/dim]")

    content_lines.append("")

    # Item counts
    content_lines.append("[bold]📊 Flashcard Inventory[/bold]")
    content_lines.append("")

    total_vocab = vocab_counts.get("total", 0)
    total_kanji = kanji_counts.get("total", 0)
    total_items = total_vocab + total_kanji

    content_lines.append(f"Total Vocabulary: [cyan]{total_vocab}[/cyan]")
    content_lines.append(f"Total Kanji:      [yellow]{total_kanji}[/yellow]")
    content_lines.append(f"Total Items:      [bold]{total_items}[/bold]")
    content_lines.append("")

    # Mastered counts
    mastered_vocab = mastered_counts.get("vocab", 0)
    mastered_kanji = mastered_counts.get("kanji", 0)
    mastered_total = mastered_counts.get("total", 0)

    content_lines.append("[bold]✨ Mastered (21+ day intervals)[/bold]")
    content_lines.append("")
    content_lines.append(f"Vocabulary: [green]{mastered_vocab}[/green]")
    content_lines.append(f"Kanji:      [green]{mastered_kanji}[/green]")
    content_lines.append(f"Total:      [bold green]{mastered_total}[/bold green]")
    content_lines.append("")

    # Review statistics
    content_lines.append("[bold]📈 Review Statistics[/bold]")
    content_lines.append("")

    if due_today > 0:
        content_lines.append(f"Due Today:      [red bold]{due_today}[/red bold] 🔔")
    else:
        content_lines.append("Due Today:      [green]0[/green] ✓")

    content_lines.append(f"Total Reviews:  [cyan]{total_reviews}[/cyan]")

    if total_reviews > 0:
        # Color-code retention rate
        if retention_rate >= 85.0:
            rate_color = "green"
        elif retention_rate >= 70.0:
            rate_color = "yellow"
        else:
            rate_color = "red"
        content_lines.append(f"Retention Rate: [{rate_color}]{retention_rate:.1f}%[/{rate_color}]")
    else:
        content_lines.append("Retention Rate: [dim]N/A[/dim]")

    # Create panel
    panel = Panel(
        "\n".join(content_lines),
        title="📊 Progress Dashboard",
        border_style="cyan",
        expand=False
    )

    return panel


def display_statistics(
    total_reviews: int,
    retention_rate: float,
    avg_duration_seconds: float,
    daily_counts: dict[str, int],
    most_reviewed: list[dict[str, Any]],
    date_range_label: str = "All Time"
) -> Panel:
    """
    Display detailed statistics with Rich table.

    Shows review counts, retention rate, average time, daily breakdown,
    and most reviewed items.

    Args:
        total_reviews: Total number of reviews in period
        retention_rate: Retention rate percentage (0-100)
        avg_duration_seconds: Average time per review in seconds
        daily_counts: Daily review counts (ISO date -> count)
        most_reviewed: List of most reviewed items
        date_range_label: Label for the date range (e.g., "Last 7 Days")

    Returns:
        Panel: Rich panel with statistics

    Example:
        panel = display_statistics(
            total_reviews=500,
            retention_rate=85.5,
            avg_duration_seconds=4.5,
            daily_counts={"2025-10-20": 15, "2025-10-21": 20},
            most_reviewed=[{"word": "単語", "review_count": 50}, ...],
            date_range_label="Last 7 Days"
        )
    """
    from rich.table import Table

    content_lines = []

    # Header
    content_lines.append(f"[bold]Statistics: {date_range_label}[/bold]")
    content_lines.append("")

    # Summary metrics
    content_lines.append("[bold]📈 Summary[/bold]")
    content_lines.append("")
    content_lines.append(f"Total Reviews: [cyan]{total_reviews}[/cyan]")

    if total_reviews > 0:
        # Retention rate
        if retention_rate >= 85.0:
            rate_color = "green"
        elif retention_rate >= 70.0:
            rate_color = "yellow"
        else:
            rate_color = "red"
        content_lines.append(f"Retention Rate: [{rate_color}]{retention_rate:.1f}%[/{rate_color}]")

        # Average time
        content_lines.append(f"Avg Time per Card: [cyan]{avg_duration_seconds:.1f}s[/cyan]")
    else:
        content_lines.append("Retention Rate: [dim]N/A[/dim]")
        content_lines.append("Avg Time per Card: [dim]N/A[/dim]")

    content_lines.append("")

    # Daily review counts (if available)
    if daily_counts and len(daily_counts) > 0:
        content_lines.append("[bold]📅 Daily Review Activity[/bold]")
        content_lines.append("")

        # Sort by date
        sorted_dates = sorted(daily_counts.keys())

        # Show last 7 days max (or fewer if less data available)
        display_dates = sorted_dates[-7:] if len(sorted_dates) > 7 else sorted_dates

        max_count = max(daily_counts.values()) if daily_counts.values() else 1

        for date_str in display_dates:
            count = daily_counts[date_str]

            # Format date nicely
            date_obj = date.fromisoformat(date_str)
            if date_obj == date.today():
                label = "Today    "
            elif date_obj == date.today() - timedelta(days=1):
                label = "Yesterday"
            else:
                label = date_obj.strftime("%b %d   ")

            # Create simple bar chart
            bar_length = int((count / max_count) * 20) if max_count > 0 else 0
            bar = "█" * bar_length
            content_lines.append(f"{label}: [cyan]{bar}[/cyan] {count}")

        content_lines.append("")

    # Most reviewed items
    if most_reviewed and len(most_reviewed) > 0:
        content_lines.append("[bold]🔥 Most Reviewed Items[/bold]")
        content_lines.append("")

        for item in most_reviewed[:5]:  # Show top 5
            if "word" in item:
                text = item["word"]
            elif "character" in item:
                text = item["character"]
            else:
                text = "Unknown"

            count = item.get("review_count", 0)
            content_lines.append(f"  {text}: [yellow]{count}[/yellow] reviews")

        content_lines.append("")

    # Create panel
    panel = Panel(
        "\n".join(content_lines),
        title="📊 Detailed Statistics",
        border_style="magenta",
        expand=False
    )

    return panel


def format_relative_date(target_date: date) -> str:
    """
    Format a date relative to today.

    Args:
        target_date: The date to format

    Returns:
        str: Formatted string (e.g., "Today", "Yesterday", "3 days ago", "In 5 days")

    Example:
        format_relative_date(date.today())  # "Today"
        format_relative_date(date.today() - timedelta(days=1))  # "Yesterday"
        format_relative_date(date.today() - timedelta(days=5))  # "5 days ago"
    """
    today = date.today()
    delta_days = (target_date - today).days

    if delta_days == 0:
        return "Today"
    elif delta_days == 1:
        return "Tomorrow"
    elif delta_days == -1:
        return "Yesterday"
    elif delta_days > 0:
        return f"In {delta_days} days"
    else:
        return f"{abs(delta_days)} days ago"


def format_grammar_table(grammar_list: list[GrammarPoint]) -> Table:
    """
    Create a Rich table displaying grammar points list.

    Args:
        grammar_list: List of GrammarPoint objects

    Returns:
        Rich Table object ready for console.print()

    Example:
        >>> grammar_list = list_grammar(jlpt_level='n5', limit=10)
        >>> table = format_grammar_table(grammar_list)
        >>> console.print(table)
    """
    table = Table(title="📖 Grammar Points", show_header=True, header_style="bold magenta")

    # Columns
    table.add_column("ID", style="dim", width=6)
    table.add_column("Title", style="bold cyan", width=30)
    table.add_column("Structure", style="yellow", width=25)
    table.add_column("JLPT", justify="center", width=6)
    table.add_column("Examples", justify="center", width=10)

    # Rows
    for grammar in grammar_list:
        # Get JLPT level color
        jlpt_color = JLPT_COLORS.get(grammar.jlpt_level or "", "white")
        jlpt_display = grammar.jlpt_level.upper() if grammar.jlpt_level else "-"

        # Structure (truncate if too long)
        structure_display = grammar.structure if grammar.structure else "-"
        if len(structure_display) > 25:
            structure_display = structure_display[:22] + "..."

        # Example count
        example_count = len(grammar.examples) if grammar.examples else 0

        row = [
            str(grammar.id),
            grammar.title,
            structure_display,
            f"[{jlpt_color}]{jlpt_display}[/{jlpt_color}]",
            str(example_count),
        ]

        table.add_row(*row)

    return table


def format_grammar_panel(grammar: GrammarPoint) -> Panel:
    """
    Create a Rich panel with detailed grammar point information.

    Args:
        grammar: GrammarPoint object

    Returns:
        Rich Panel with all grammar details

    Example:
        >>> grammar = get_grammar_by_id(1)
        >>> panel = format_grammar_panel(grammar)
        >>> console.print(panel)
    """
    content_lines = []

    # Title (bold and prominent)
    content_lines.append(f"[bold bright_cyan]{grammar.title}[/bold bright_cyan]")
    content_lines.append("")

    # Structure
    if grammar.structure:
        content_lines.append(f"[bold]Structure:[/bold] [yellow]{grammar.structure}[/yellow]")
        content_lines.append("")

    # Explanation
    content_lines.append("[bold]Explanation:[/bold]")
    content_lines.append(f"[green]{grammar.explanation}[/green]")
    content_lines.append("")

    # JLPT level
    if grammar.jlpt_level:
        jlpt_color = JLPT_COLORS.get(grammar.jlpt_level, "white")
        content_lines.append(f"[dim]JLPT level:[/dim] [{jlpt_color}]{grammar.jlpt_level.upper()}[/{jlpt_color}]")
        content_lines.append("")

    # Examples
    if grammar.examples:
        content_lines.append(f"[bold]Examples ({len(grammar.examples)}):[/bold]")
        for idx, example in enumerate(grammar.examples, 1):
            content_lines.append(f"\n[dim]{idx}.[/dim]")
            # Japanese sentence (with furigana if possible)
            content_lines.append(f"  [bright_yellow]{example.jp}[/bright_yellow]")
            # Vietnamese translation
            content_lines.append(f"  [green]{example.vi}[/green]")
            # English translation (if available)
            if example.en:
                content_lines.append(f"  [dim]{example.en}[/dim]")
        content_lines.append("")

    # Related grammar
    if grammar.related_grammar:
        related_ids = ", ".join(str(gid) for gid in grammar.related_grammar)
        content_lines.append(f"[dim]Related grammar:[/dim] {related_ids}")
        content_lines.append("")

    # Notes
    if grammar.notes:
        content_lines.append(f"[dim]Notes:[/dim]")
        content_lines.append(f"{grammar.notes}")
        content_lines.append("")

    # Timestamps
    content_lines.append(f"[dim]Created:[/dim] {grammar.created_at.strftime('%Y-%m-%d %H:%M')}")
    content_lines.append(f"[dim]Updated:[/dim] {grammar.updated_at.strftime('%Y-%m-%d %H:%M')}")

    # Join all lines and create panel
    content = "\n".join(content_lines)
    return Panel(
        content,
        title=f"📖 Grammar Point #{grammar.id}",
        border_style="cyan",
        padding=(1, 2)
    )
