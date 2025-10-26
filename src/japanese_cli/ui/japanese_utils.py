"""
Japanese character detection and romaji conversion utilities.

Provides functions to detect character types (hiragana, katakana, kanji, romaji)
and convert between romaji and hiragana for input validation.
"""

import re
import wanakana


def is_hiragana(char: str) -> bool:
    """
    Check if a character is hiragana.

    Args:
        char: Single character to check

    Returns:
        bool: True if character is hiragana (U+3040-U+309F)

    Example:
        >>> is_hiragana('あ')
        True
        >>> is_hiragana('ア')
        False
        >>> is_hiragana('a')
        False
    """
    if not char:
        return False
    return '\u3040' <= char <= '\u309F'


def is_katakana(char: str) -> bool:
    """
    Check if a character is katakana.

    Args:
        char: Single character to check

    Returns:
        bool: True if character is katakana (U+30A0-U+30FF)

    Example:
        >>> is_katakana('ア')
        True
        >>> is_katakana('あ')
        False
        >>> is_katakana('a')
        False
    """
    if not char:
        return False
    return '\u30A0' <= char <= '\u30FF'


def is_kanji(char: str) -> bool:
    """
    Check if a character is kanji (CJK Unified Ideographs).

    Args:
        char: Single character to check

    Returns:
        bool: True if character is kanji (U+4E00-U+9FFF)

    Example:
        >>> is_kanji('語')
        True
        >>> is_kanji('あ')
        False
        >>> is_kanji('a')
        False
    """
    if not char:
        return False
    return '\u4E00' <= char <= '\u9FFF'


def is_japanese_char(char: str) -> bool:
    """
    Check if a character is any type of Japanese character.

    Args:
        char: Single character to check

    Returns:
        bool: True if character is hiragana, katakana, or kanji

    Example:
        >>> is_japanese_char('あ')
        True
        >>> is_japanese_char('ア')
        True
        >>> is_japanese_char('語')
        True
        >>> is_japanese_char('a')
        False
    """
    return is_hiragana(char) or is_katakana(char) or is_kanji(char)


def contains_japanese(text: str) -> bool:
    """
    Check if text contains any Japanese characters.

    Args:
        text: Text to check

    Returns:
        bool: True if text contains at least one Japanese character

    Example:
        >>> contains_japanese('こんにちは')
        True
        >>> contains_japanese('hello 世界')
        True
        >>> contains_japanese('hello')
        False
    """
    if not text:
        return False
    return any(is_japanese_char(char) for char in text)


def is_romaji(text: str) -> bool:
    """
    Check if text is primarily romaji (Latin characters).

    Considers text as romaji if it:
    - Contains only ASCII letters, numbers, spaces, and basic punctuation
    - Does NOT contain Japanese characters

    Args:
        text: Text to check

    Returns:
        bool: True if text appears to be romaji

    Example:
        >>> is_romaji('tanago')
        True
        >>> is_romaji('hello world')
        True
        >>> is_romaji('単語')
        False
        >>> is_romaji('tanago 単語')
        False
    """
    if not text:
        return False

    # If contains Japanese characters, not romaji
    if contains_japanese(text):
        return False

    # Check if contains primarily ASCII letters
    # Allow letters, numbers, spaces, and basic punctuation
    ascii_pattern = re.compile(r'^[a-zA-Z0-9\s\.,\!\?\-\'\"]+$')
    return bool(ascii_pattern.match(text))


def romaji_to_hiragana(text: str) -> str:
    """
    Convert romaji text to hiragana using wanakana library.

    Args:
        text: Romaji text to convert

    Returns:
        str: Hiragana text

    Example:
        >>> romaji_to_hiragana('tanago')
        'たなご'
        >>> romaji_to_hiragana('konnichiwa')
        'こんにちは'
        >>> romaji_to_hiragana('nihongo')
        'にほんご'

    Note:
        Uses Hepburn romanization system (most common)
    """
    if not text:
        return text

    return wanakana.to_hiragana(text)


def validate_japanese_text(text: str, field_name: str = "Field") -> None:
    """
    Validate that text contains Japanese characters (not romaji).

    Raises ValueError if:
    - Text is empty
    - Text contains only romaji
    - Text doesn't contain any Japanese characters

    Args:
        text: Text to validate
        field_name: Name of field being validated (for error messages)

    Raises:
        ValueError: If text is not valid Japanese

    Example:
        >>> validate_japanese_text('単語', 'Word')  # OK
        >>> validate_japanese_text('tanago', 'Word')  # Raises ValueError
        >>> validate_japanese_text('', 'Word')  # Raises ValueError
    """
    if not text or not text.strip():
        raise ValueError(f"{field_name} cannot be empty")

    if is_romaji(text):
        raise ValueError(
            f"{field_name} must be in Japanese characters, not romaji. "
            f"Received: '{text}'"
        )

    if not contains_japanese(text):
        raise ValueError(
            f"{field_name} must contain Japanese characters (hiragana, katakana, or kanji). "
            f"Received: '{text}'"
        )


def get_character_type(char: str) -> str:
    """
    Get the type of a character.

    Args:
        char: Single character to check

    Returns:
        str: One of: 'hiragana', 'katakana', 'kanji', 'romaji', 'other'

    Example:
        >>> get_character_type('あ')
        'hiragana'
        >>> get_character_type('ア')
        'katakana'
        >>> get_character_type('語')
        'kanji'
        >>> get_character_type('a')
        'romaji'
        >>> get_character_type('1')
        'other'
    """
    if not char:
        return 'other'

    if is_hiragana(char):
        return 'hiragana'
    elif is_katakana(char):
        return 'katakana'
    elif is_kanji(char):
        return 'kanji'
    elif char.isascii() and char.isalpha():
        return 'romaji'
    else:
        return 'other'


def contains_only_kana(text: str) -> bool:
    """
    Check if text contains only hiragana and/or katakana (no kanji).

    Args:
        text: Text to check

    Returns:
        bool: True if text contains only kana characters

    Example:
        >>> contains_only_kana('ひらがな')
        True
        >>> contains_only_kana('カタカナ')
        True
        >>> contains_only_kana('ひらカタ')
        True
        >>> contains_only_kana('漢字')
        False
        >>> contains_only_kana('hiragana')
        False
    """
    if not text:
        return False

    # Must contain at least one kana character
    has_kana = any(is_hiragana(char) or is_katakana(char) for char in text)
    if not has_kana:
        return False

    # All characters must be kana (or spaces/punctuation)
    for char in text:
        if char.isspace():  # Allow spaces
            continue
        if not (is_hiragana(char) or is_katakana(char)):
            return False

    return True
