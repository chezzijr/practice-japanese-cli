"""
Rich display utilities for flashcard data.

Provides functions to create Rich tables, panels, and formatted output
for vocabulary, kanji, and other learning materials.
"""

from datetime import datetime, timezone
from typing import Optional

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..models import Vocabulary, Kanji, Review
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
