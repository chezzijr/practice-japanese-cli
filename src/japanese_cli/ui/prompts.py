"""
Interactive prompt utilities for collecting user input.

Provides functions to collect vocabulary, kanji, and other data
through interactive prompts with validation.
"""

import json
from typing import Optional

from pydantic import ValidationError
from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table

from ..models import Vocabulary, Kanji
from ..database import search_vocabulary_by_reading, search_kanji_by_reading
from .japanese_utils import is_romaji, romaji_to_hiragana, contains_japanese

console = Console()


def prompt_vocabulary_data(existing: Optional[Vocabulary] = None) -> Optional[dict]:
    """
    Interactively collect vocabulary data from user.

    Prompts for all required and optional fields for a vocabulary entry.
    If existing vocabulary is provided, fields are pre-filled with current values.

    Args:
        existing: Optional existing Vocabulary object for editing

    Returns:
        Dictionary with vocabulary data, or None if user cancels

    Example:
        >>> data = prompt_vocabulary_data()
        >>> if data:
        ...     vocab_id = add_vocabulary(**data)
    """
    console.print("\n[bold cyan]Adding Vocabulary Entry[/bold cyan]")
    console.print("[dim]Press Ctrl+C to cancel at any time[/dim]")
    console.print("[dim]You can enter romaji to search existing vocabulary[/dim]\n")

    try:
        # Word (required) - with romaji lookup
        word = None
        reading = None
        meanings = None
        vietnamese_reading = None
        jlpt_level = None
        part_of_speech = None
        tags = []
        notes = None

        # Track if we auto-filled from database lookup
        auto_filled = False

        while not word:
            word_input = Prompt.ask(
                "[bold]Japanese word[/bold] (kanji/kana or romaji to search)",
                default=existing.word if existing else None
            )

            # Check if romaji input
            if is_romaji(word_input):
                # Convert romaji to hiragana
                hiragana_reading = romaji_to_hiragana(word_input)
                console.print(f"[dim]→ Converting romaji to hiragana: {hiragana_reading}[/dim]")
                console.print(f"[dim]→ Searching database...[/dim]")

                # Search database for matches
                matches = search_vocabulary_by_reading(hiragana_reading, exact_match=True)

                if matches:
                    # Show selection menu
                    selected = select_from_vocabulary_matches(matches, word_input)

                    if selected:
                        # Auto-fill from selected vocabulary
                        console.print("[green]✓ Auto-filled from database[/green]\n")
                        word = selected['word']
                        reading = selected['reading']

                        # Parse meanings from JSON
                        meanings_data = json.loads(selected['meanings']) if isinstance(selected['meanings'], str) else selected['meanings']
                        meanings = meanings_data

                        # Optional fields
                        vietnamese_reading = selected.get('vietnamese_reading')
                        jlpt_level = selected.get('jlpt_level')
                        part_of_speech = selected.get('part_of_speech')

                        # Parse tags from JSON
                        tags_data = selected.get('tags')
                        if tags_data:
                            tags = json.loads(tags_data) if isinstance(tags_data, str) else tags_data
                        else:
                            tags = []

                        notes = selected.get('notes')
                        auto_filled = True
                        break
                    else:
                        # User cancelled selection, re-prompt
                        word = None
                        continue
                else:
                    # No matches found
                    console.print(f"[red]✗ No vocabulary found for '{hiragana_reading}'.[/red]")
                    console.print("[yellow]Please enter Japanese characters (hiragana, katakana, or kanji).[/yellow]\n")
                    word = None
                    continue

            # Check if contains Japanese characters
            elif contains_japanese(word_input):
                # Valid Japanese input
                word = word_input
                break
            else:
                # Invalid input (not Japanese, not romaji)
                console.print("[red]✗ Invalid input. Please enter Japanese characters or romaji.[/red]\n")
                word = None
                continue

        # If not auto-filled, prompt for other fields
        if not auto_filled:
            # Reading (required)
            reading = Prompt.ask(
                "[bold]Reading[/bold] (hiragana/katakana)",
                default=existing.reading if existing else None
            )

            # Vietnamese meaning (required)
            vi_meaning = Prompt.ask(
                "[bold]Vietnamese meaning[/bold]",
                default=existing.meanings.get("vi", [""])[0] if existing else None
            )

            # English meaning (optional)
            en_meaning = Prompt.ask(
                "English meaning [dim](optional)[/dim]",
                default=existing.meanings.get("en", [""])[0] if existing and existing.meanings.get("en") else "",
                show_default=False
            )

            # Build meanings dict
            meanings = {"vi": [vi_meaning]}
            if en_meaning:
                meanings["en"] = [en_meaning]
        else:
            # Show auto-filled values, allow editing
            console.print(f"[dim]Word: {word}[/dim]")
            console.print(f"[dim]Reading: {reading}[/dim]")
            console.print(f"[dim]Meanings: {meanings}[/dim]\n")

        # Determine defaults (from existing, or auto-filled, or none)
        default_vietnamese_reading = vietnamese_reading or (existing.vietnamese_reading if existing else "")
        default_jlpt = jlpt_level or (existing.jlpt_level if existing else "")
        default_pos = part_of_speech or (existing.part_of_speech if existing else "")
        default_tags = tags if tags else (existing.tags if existing else [])
        default_notes = notes or (existing.notes if existing else "")

        # Vietnamese reading (optional)
        vietnamese_reading_input = Prompt.ask(
            "Sino-Vietnamese reading [dim](optional)[/dim]",
            default=default_vietnamese_reading,
            show_default=bool(default_vietnamese_reading)
        )
        vietnamese_reading = vietnamese_reading_input or None

        # JLPT level (optional)
        jlpt_level_input = Prompt.ask(
            "JLPT level [dim](n5/n4/n3/n2/n1, optional)[/dim]",
            choices=["n5", "n4", "n3", "n2", "n1", ""],
            default=default_jlpt,
            show_default=bool(default_jlpt),
            show_choices=True
        )
        jlpt_level = jlpt_level_input or None

        # Part of speech (optional)
        part_of_speech_input = Prompt.ask(
            "Part of speech [dim](noun/verb/adjective/etc., optional)[/dim]",
            default=default_pos,
            show_default=bool(default_pos)
        )
        part_of_speech = part_of_speech_input or None

        # Tags (optional)
        tags_str = Prompt.ask(
            "Tags [dim](comma-separated, optional)[/dim]",
            default=", ".join(default_tags) if default_tags else "",
            show_default=bool(default_tags)
        )
        tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]

        # Notes (optional)
        notes_input = Prompt.ask(
            "Notes [dim](optional)[/dim]",
            default=default_notes,
            show_default=bool(default_notes)
        )
        notes = notes_input or None

        # Validate data using Pydantic model
        try:
            vocab_data = {
                "word": word,
                "reading": reading,
                "meanings": meanings,
                "vietnamese_reading": vietnamese_reading,
                "jlpt_level": jlpt_level,
                "part_of_speech": part_of_speech,
                "tags": tags,
                "notes": notes,
            }

            # Validate with Pydantic (create temporary model to check)
            Vocabulary(**vocab_data)

            # Return data for database insertion
            return vocab_data

        except ValidationError as e:
            console.print(f"\n[red]Validation error:[/red] {e}")
            return None

    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/yellow]")
        return None


def prompt_kanji_data(existing: Optional[Kanji] = None) -> Optional[dict]:
    """
    Interactively collect kanji data from user.

    Prompts for all required and optional fields for a kanji entry.
    If existing kanji is provided, fields are pre-filled with current values.

    Args:
        existing: Optional existing Kanji object for editing

    Returns:
        Dictionary with kanji data, or None if user cancels

    Example:
        >>> data = prompt_kanji_data()
        >>> if data:
        ...     kanji_id = add_kanji(**data)
    """
    console.print("\n[bold cyan]Adding Kanji Entry[/bold cyan]")
    console.print("[dim]Press Ctrl+C to cancel at any time[/dim]")
    console.print("[dim]You can enter romaji to search existing kanji[/dim]\n")

    try:
        # Character (required) - with romaji lookup
        character = None
        on_readings = []
        kun_readings = []
        meanings = None
        vietnamese_reading = None
        jlpt_level = None
        stroke_count = None
        radical = None
        notes = None

        # Track if we auto-filled from database lookup
        auto_filled = False

        while not character:
            character_input = Prompt.ask(
                "[bold]Kanji character[/bold] (single character or romaji to search)",
                default=existing.character if existing else None
            )

            # Check if romaji input
            if is_romaji(character_input):
                # Convert romaji to hiragana
                hiragana_reading = romaji_to_hiragana(character_input)
                console.print(f"[dim]→ Converting romaji to hiragana: {hiragana_reading}[/dim]")
                console.print(f"[dim]→ Searching kanji database...[/dim]")

                # Search database for matches (search both on and kun readings)
                matches = search_kanji_by_reading(hiragana_reading, reading_type="both")

                if matches:
                    # Show selection menu
                    selected = select_from_kanji_matches(matches, character_input)

                    if selected:
                        # Auto-fill from selected kanji
                        console.print("[green]✓ Auto-filled from database[/green]\n")
                        character = selected['character']

                        # Parse readings from JSON
                        on_data = selected.get('on_readings')
                        on_readings = json.loads(on_data) if isinstance(on_data, str) else (on_data or [])

                        kun_data = selected.get('kun_readings')
                        kun_readings = json.loads(kun_data) if isinstance(kun_data, str) else (kun_data or [])

                        # Parse meanings from JSON
                        meanings_data = json.loads(selected['meanings']) if isinstance(selected['meanings'], str) else selected['meanings']
                        meanings = meanings_data

                        # Optional fields
                        vietnamese_reading = selected.get('vietnamese_reading')
                        jlpt_level = selected.get('jlpt_level')
                        stroke_count = selected.get('stroke_count')
                        radical = selected.get('radical')
                        notes = selected.get('notes')

                        auto_filled = True
                        break
                    else:
                        # User cancelled selection, re-prompt
                        character = None
                        continue
                else:
                    # No matches found
                    console.print(f"[red]✗ No kanji found for reading '{hiragana_reading}'.[/red]")
                    console.print("[yellow]Please enter a single kanji character.[/yellow]\n")
                    character = None
                    continue

            # Check if single Japanese character
            elif len(character_input) == 1:
                from .japanese_utils import is_kanji
                if is_kanji(character_input):
                    # Valid kanji input
                    character = character_input
                    break
                else:
                    console.print("[red]✗ Please enter a kanji character (not hiragana or katakana).[/red]\n")
                    character = None
                    continue
            else:
                # Invalid input (not single character, not romaji)
                console.print("[red]✗ Please enter exactly one kanji character or romaji to search.[/red]\n")
                character = None
                continue

        # If not auto-filled, prompt for other fields
        if not auto_filled:
            # On-yomi readings (optional, comma-separated)
            on_readings_str = Prompt.ask(
                "On-yomi readings [dim](comma-separated, optional)[/dim]",
                default=", ".join(existing.on_readings) if existing and existing.on_readings else "",
                show_default=False
            )
            on_readings = [r.strip() for r in on_readings_str.split(",") if r.strip()]

            # Kun-yomi readings (optional, comma-separated)
            kun_readings_str = Prompt.ask(
                "Kun-yomi readings [dim](comma-separated, optional)[/dim]",
                default=", ".join(existing.kun_readings) if existing and existing.kun_readings else "",
                show_default=False
            )
            kun_readings = [r.strip() for r in kun_readings_str.split(",") if r.strip()]

            # Vietnamese meaning (required)
            vi_meaning = Prompt.ask(
                "[bold]Vietnamese meaning[/bold]",
                default=existing.meanings.get("vi", [""])[0] if existing else None
            )

            # English meaning (optional)
            en_meaning = Prompt.ask(
                "English meaning [dim](optional)[/dim]",
                default=existing.meanings.get("en", [""])[0] if existing and existing.meanings.get("en") else "",
                show_default=False
            )

            # Build meanings dict
            meanings = {"vi": [vi_meaning]}
            if en_meaning:
                meanings["en"] = [en_meaning]
        else:
            # Show auto-filled values
            console.print(f"[dim]Character: {character}[/dim]")
            console.print(f"[dim]On-readings: {', '.join(on_readings)}[/dim]")
            console.print(f"[dim]Kun-readings: {', '.join(kun_readings)}[/dim]")
            console.print(f"[dim]Meanings: {meanings}[/dim]\n")

        # Determine defaults (from existing, or auto-filled, or none)
        default_vietnamese_reading = vietnamese_reading or (existing.vietnamese_reading if existing else "")
        default_jlpt = jlpt_level or (existing.jlpt_level if existing else "")
        default_stroke_count = stroke_count or (existing.stroke_count if existing and existing.stroke_count else "")
        default_radical = radical or (existing.radical if existing else "")
        default_notes = notes or (existing.notes if existing else "")

        # Vietnamese reading (Hán Việt) (optional)
        vietnamese_reading_input = Prompt.ask(
            "Hán Việt reading [dim](optional)[/dim]",
            default=default_vietnamese_reading,
            show_default=bool(default_vietnamese_reading)
        )
        vietnamese_reading = vietnamese_reading_input or None

        # JLPT level (optional)
        jlpt_level_input = Prompt.ask(
            "JLPT level [dim](n5/n4/n3/n2/n1, optional)[/dim]",
            choices=["n5", "n4", "n3", "n2", "n1", ""],
            default=default_jlpt,
            show_default=bool(default_jlpt),
            show_choices=True
        )
        jlpt_level = jlpt_level_input or None

        # Stroke count (optional)
        stroke_count_str = Prompt.ask(
            "Stroke count [dim](optional)[/dim]",
            default=str(default_stroke_count) if default_stroke_count else "",
            show_default=bool(default_stroke_count)
        )
        stroke_count = int(stroke_count_str) if stroke_count_str else None

        # Radical (optional)
        radical_input = Prompt.ask(
            "Radical [dim](optional)[/dim]",
            default=default_radical,
            show_default=bool(default_radical)
        )
        radical = radical_input or None

        # Notes (optional)
        notes_input = Prompt.ask(
            "Notes [dim](optional)[/dim]",
            default=default_notes,
            show_default=bool(default_notes)
        )
        notes = notes_input or None

        # Validate data using Pydantic model
        try:
            kanji_data = {
                "character": character,
                "on_readings": on_readings,
                "kun_readings": kun_readings,
                "meanings": meanings,
                "vietnamese_reading": vietnamese_reading,
                "jlpt_level": jlpt_level,
                "stroke_count": stroke_count,
                "radical": radical,
                "notes": notes,
            }

            # Validate with Pydantic (create temporary model to check)
            Kanji(**kanji_data)

            # Return data for database insertion
            return kanji_data

        except ValidationError as e:
            console.print(f"\n[red]Validation error:[/red] {e}")
            return None

    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/yellow]")
        return None


def confirm_action(message: str, default: bool = False) -> bool:
    """
    Ask user for confirmation (yes/no).

    Args:
        message: Confirmation message to display
        default: Default value if user presses Enter

    Returns:
        True if user confirms, False otherwise

    Example:
        >>> if confirm_action("Delete this item?"):
        ...     delete_item()
    """
    try:
        return Confirm.ask(message, default=default)
    except KeyboardInterrupt:
        return False


def prompt_jlpt_level(default: Optional[str] = None) -> Optional[str]:
    """
    Prompt user to select JLPT level.

    Args:
        default: Default JLPT level

    Returns:
        Selected JLPT level or None

    Example:
        >>> level = prompt_jlpt_level()
    """
    try:
        level = Prompt.ask(
            "JLPT level",
            choices=["n5", "n4", "n3", "n2", "n1", "all"],
            default=default or "all",
            show_choices=True
        )
        return level if level != "all" else None
    except KeyboardInterrupt:
        return None


def prompt_item_type() -> Optional[str]:
    """
    Prompt user to select item type (vocabulary or kanji).

    Returns:
        "vocab" or "kanji", or None if cancelled

    Example:
        >>> item_type = prompt_item_type()
    """
    try:
        return Prompt.ask(
            "Item type",
            choices=["vocab", "kanji"],
            default="vocab",
            show_choices=True
        )
    except KeyboardInterrupt:
        return None


def select_from_vocabulary_matches(matches: list[dict], search_term: str) -> Optional[dict]:
    """
    Show selection menu for multiple vocabulary matches.

    Displays a Rich table with all matching vocabulary entries and prompts
    user to select one.

    Args:
        matches: List of vocabulary dictionaries from database
        search_term: Original search term (for display)

    Returns:
        Selected vocabulary dict, or None if cancelled

    Example:
        >>> matches = search_vocabulary_by_reading("たんご")
        >>> selected = select_from_vocabulary_matches(matches, "tanago")
        >>> if selected:
        ...     vocab = Vocabulary.from_db_row(selected)
    """
    if not matches:
        return None

    console.print(f"\n[cyan]Found {len(matches)} match(es) for '[bold]{search_term}[/bold]':[/cyan]\n")

    # Create selection table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=4)
    table.add_column("Word", style="bold cyan")
    table.add_column("Reading", style="cyan")
    table.add_column("Meanings", style="green")

    for idx, vocab in enumerate(matches, 1):
        # Parse meanings from JSON string
        meanings_data = json.loads(vocab['meanings']) if isinstance(vocab['meanings'], str) else vocab['meanings']

        # Format meanings (Vietnamese primary, English secondary)
        meanings_parts = []
        if 'vi' in meanings_data and meanings_data['vi']:
            meanings_parts.append(", ".join(meanings_data['vi'][:2]))  # Max 2 meanings
        if 'en' in meanings_data and meanings_data['en']:
            meanings_parts.append(f"[dim]({', '.join(meanings_data['en'][:2])})[/dim]")
        meanings_display = " ".join(meanings_parts)

        table.add_row(
            str(idx),
            vocab['word'],
            vocab['reading'],
            meanings_display
        )

    console.print(table)

    try:
        console.print("\n[dim]Enter selection number, or press Ctrl+C to cancel[/dim]")
        choice = IntPrompt.ask(
            "Select word",
            choices=[str(i) for i in range(1, len(matches) + 1)]
        )
        return matches[int(choice) - 1]
    except KeyboardInterrupt:
        console.print("\n[yellow]Selection cancelled[/yellow]")
        return None


def select_from_kanji_matches(matches: list[dict], search_term: str) -> Optional[dict]:
    """
    Show selection menu for multiple kanji matches.

    Displays a Rich table with all matching kanji entries and prompts
    user to select one.

    Args:
        matches: List of kanji dictionaries from database
        search_term: Original search term (for display)

    Returns:
        Selected kanji dict, or None if cancelled

    Example:
        >>> matches = search_kanji_by_reading("ゴ", reading_type="on")
        >>> selected = select_from_kanji_matches(matches, "go")
        >>> if selected:
        ...     kanji = Kanji.from_db_row(selected)
    """
    if not matches:
        return None

    console.print(f"\n[cyan]Found {len(matches)} match(es) for '[bold]{search_term}[/bold]':[/cyan]\n")

    # Create selection table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=4)
    table.add_column("Kanji", style="bold yellow", width=8)
    table.add_column("Readings", style="cyan")
    table.add_column("Meanings", style="green")

    for idx, kanji in enumerate(matches, 1):
        # Parse readings from JSON strings
        on_readings = json.loads(kanji['on_readings']) if isinstance(kanji['on_readings'], str) else kanji['on_readings']
        kun_readings = json.loads(kanji['kun_readings']) if isinstance(kanji['kun_readings'], str) else kanji['kun_readings']

        # Format readings (on-yomi in katakana style, kun-yomi in hiragana style)
        readings_parts = []
        if on_readings:
            readings_parts.append(", ".join(on_readings[:2]))  # Max 2 readings
        if kun_readings:
            readings_parts.append(f"[dim]{', '.join(kun_readings[:2])}[/dim]")
        readings_display = " / ".join(readings_parts)

        # Parse meanings
        meanings_data = json.loads(kanji['meanings']) if isinstance(kanji['meanings'], str) else kanji['meanings']

        # Format meanings (Vietnamese primary)
        meanings_parts = []
        if 'vi' in meanings_data and meanings_data['vi']:
            meanings_parts.append(", ".join(meanings_data['vi'][:2]))
        if 'en' in meanings_data and meanings_data['en']:
            meanings_parts.append(f"[dim]({', '.join(meanings_data['en'][:2])})[/dim]")
        meanings_display = " ".join(meanings_parts)

        table.add_row(
            str(idx),
            kanji['character'],
            readings_display,
            meanings_display
        )

    console.print(table)

    try:
        console.print("\n[dim]Enter selection number, or press Ctrl+C to cancel[/dim]")
        choice = IntPrompt.ask(
            "Select kanji",
            choices=[str(i) for i in range(1, len(matches) + 1)]
        )
        return matches[int(choice) - 1]
    except KeyboardInterrupt:
        console.print("\n[yellow]Selection cancelled[/yellow]")
        return None
