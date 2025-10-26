"""
Rich display utilities for flashcard data.

Provides functions to create Rich tables, panels, and formatted output
for vocabulary, kanji, and other learning materials.
"""

from datetime import datetime, timezone
from typing import Optional

from rich.console import Group
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
        if due_date <= datetime.now():
            content_lines.append(f"  [red]Due now![/red]")
        else:
            days = (due_date - datetime.now()).days
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
        if due_date <= datetime.now():
            content_lines.append(f"  [red]Due now![/red]")
        else:
            days = (due_date - datetime.now()).days
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
