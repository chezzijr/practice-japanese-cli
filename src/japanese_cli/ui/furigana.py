"""
Furigana rendering utilities for Japanese text.

Provides functions to render Japanese words with furigana (reading annotations)
using Rich Text formatting for beautiful terminal display.
"""

from rich.text import Text


def render_furigana(word: str, reading: str, style: str = "compact") -> Text:
    """
    Render Japanese word with furigana reading.

    Creates a Rich Text object that displays the word with its reading
    in a readable format suitable for terminal display.

    Args:
        word: Japanese word in kanji/kana (e.g., "単語")
        reading: Reading in hiragana/katakana (e.g., "たんご")
        style: Rendering style - "compact" or "detailed" (default: "compact")

    Returns:
        Rich Text object with styled furigana

    Example:
        >>> text = render_furigana("単語", "たんご")
        >>> console.print(text)  # Displays: 単語[たんご]

        >>> text = render_furigana("漢字", "かんじ", style="detailed")
        >>> console.print(text)  # Displays with more styling
    """
    if style == "compact":
        return _render_compact(word, reading)
    elif style == "detailed":
        return _render_detailed(word, reading)
    else:
        raise ValueError(f"Unknown style: {style}. Use 'compact' or 'detailed'")


def _render_compact(word: str, reading: str) -> Text:
    """
    Render furigana in compact format: word[reading]

    Args:
        word: Japanese word
        reading: Reading annotation

    Returns:
        Rich Text with compact furigana
    """
    text = Text()
    text.append(word, style="bold cyan")
    text.append("[", style="dim")
    text.append(reading, style="yellow")
    text.append("]", style="dim")
    return text


def _render_detailed(word: str, reading: str) -> Text:
    """
    Render furigana in detailed format with more visual separation.

    Args:
        word: Japanese word
        reading: Reading annotation

    Returns:
        Rich Text with detailed furigana styling
    """
    text = Text()
    text.append(word, style="bold bright_cyan")
    text.append(" ", style="")
    text.append("(", style="dim white")
    text.append(reading, style="bright_yellow")
    text.append(")", style="dim white")
    return text


def format_word_with_reading(word: str, reading: str) -> str:
    """
    Format word with reading as plain string (no Rich styling).

    Useful for contexts where Rich formatting is not available.

    Args:
        word: Japanese word
        reading: Reading annotation

    Returns:
        Plain string in format: word[reading]

    Example:
        >>> format_word_with_reading("単語", "たんご")
        '単語[たんご]'
    """
    return f"{word}[{reading}]"


def format_kanji_with_readings(
    character: str,
    on_readings: list[str],
    kun_readings: list[str],
    style: str = "compact"
) -> Text:
    """
    Format kanji character with on-yomi and kun-yomi readings.

    Args:
        character: Single kanji character (e.g., "語")
        on_readings: List of on-yomi readings (e.g., ["ゴ"])
        kun_readings: List of kun-yomi readings (e.g., ["かた.る"])
        style: Rendering style - "compact" or "detailed"

    Returns:
        Rich Text with kanji and all readings

    Example:
        >>> text = format_kanji_with_readings("語", ["ゴ"], ["かた.る"])
        >>> console.print(text)
    """
    text = Text()

    # Kanji character
    text.append(character, style="bold bright_cyan")
    text.append(" ", style="")

    # On-yomi readings
    if on_readings:
        text.append("音: ", style="dim")
        text.append(", ".join(on_readings), style="magenta")
        if kun_readings:
            text.append("  ", style="")

    # Kun-yomi readings
    if kun_readings:
        text.append("訓: ", style="dim")
        text.append(", ".join(kun_readings), style="yellow")

    return text
