"""
UI utilities for Japanese Learning CLI.

Provides Rich-based display, formatting, and interactive prompt utilities
for beautiful terminal user interfaces.
"""

from .display import (
    format_vocabulary_table,
    format_kanji_table,
    format_vocabulary_panel,
    format_kanji_panel,
    format_grammar_table,
    format_grammar_panel,
    display_card_question,
    display_card_answer,
    prompt_rating,
    display_session_summary,
    display_progress_dashboard,
    display_statistics,
    format_relative_date,
    JLPT_COLORS,
    # MCQ display functions
    display_mcq_question,
    display_mcq_result,
    display_mcq_session_summary,
    prompt_mcq_option,
)

from .furigana import (
    render_furigana,
    format_word_with_reading,
    format_kanji_with_readings,
)

from .prompts import (
    prompt_vocabulary_data,
    prompt_kanji_data,
    prompt_grammar_data,
    prompt_example_data,
    confirm_action,
    prompt_jlpt_level,
    prompt_item_type,
    select_from_vocabulary_matches,
    select_from_kanji_matches,
)

from .japanese_utils import (
    is_hiragana,
    is_katakana,
    is_kanji,
    is_japanese_char,
    contains_japanese,
    is_romaji,
    romaji_to_hiragana,
    validate_japanese_text,
    get_character_type,
    contains_only_kana,
)

__all__ = [
    # Display utilities
    "format_vocabulary_table",
    "format_kanji_table",
    "format_vocabulary_panel",
    "format_kanji_panel",
    "format_grammar_table",
    "format_grammar_panel",
    "display_card_question",
    "display_card_answer",
    "prompt_rating",
    "display_session_summary",
    "display_progress_dashboard",
    "display_statistics",
    "format_relative_date",
    "JLPT_COLORS",
    # MCQ display utilities
    "display_mcq_question",
    "display_mcq_result",
    "display_mcq_session_summary",
    "prompt_mcq_option",
    # Furigana utilities
    "render_furigana",
    "format_word_with_reading",
    "format_kanji_with_readings",
    # Prompt utilities
    "prompt_vocabulary_data",
    "prompt_kanji_data",
    "prompt_grammar_data",
    "prompt_example_data",
    "confirm_action",
    "prompt_jlpt_level",
    "prompt_item_type",
    "select_from_vocabulary_matches",
    "select_from_kanji_matches",
    # Japanese utilities
    "is_hiragana",
    "is_katakana",
    "is_kanji",
    "is_japanese_char",
    "contains_japanese",
    "is_romaji",
    "romaji_to_hiragana",
    "validate_japanese_text",
    "get_character_type",
    "contains_only_kana",
]
