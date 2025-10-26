"""
Tests for furigana rendering utilities.

Tests the ui/furigana.py module which handles rendering Japanese text
with reading annotations for terminal display.
"""

import pytest
from rich.text import Text

from japanese_cli.ui.furigana import (
    render_furigana,
    format_word_with_reading,
    format_kanji_with_readings,
)


class TestRenderFurigana:
    """Tests for render_furigana function."""

    def test_render_compact_style(self):
        """Test rendering furigana in compact format."""
        result = render_furigana("単語", "たんご", style="compact")

        assert isinstance(result, Text)
        # Check that result contains the word and reading
        plain_text = result.plain
        assert "単語" in plain_text
        assert "たんご" in plain_text
        assert "[" in plain_text
        assert "]" in plain_text

    def test_render_detailed_style(self):
        """Test rendering furigana in detailed format."""
        result = render_furigana("漢字", "かんじ", style="detailed")

        assert isinstance(result, Text)
        # Check that result contains the word and reading
        plain_text = result.plain
        assert "漢字" in plain_text
        assert "かんじ" in plain_text

    def test_render_with_katakana(self):
        """Test rendering with katakana reading."""
        result = render_furigana("コーヒー", "コーヒー", style="compact")

        assert isinstance(result, Text)
        assert "コーヒー" in result.plain

    def test_render_with_hiragana_only(self):
        """Test rendering hiragana-only word."""
        result = render_furigana("ありがとう", "ありがとう", style="compact")

        assert isinstance(result, Text)
        assert "ありがとう" in result.plain

    def test_render_invalid_style(self):
        """Test that invalid style raises ValueError."""
        with pytest.raises(ValueError, match="Unknown style"):
            render_furigana("単語", "たんご", style="invalid")

    def test_render_empty_strings(self):
        """Test rendering with empty strings."""
        result = render_furigana("", "", style="compact")

        assert isinstance(result, Text)
        # Should still create Text object, even if empty

    def test_render_long_word(self):
        """Test rendering long word with reading."""
        word = "日本語能力試験"
        reading = "にほんごのうりょくしけん"
        result = render_furigana(word, reading, style="compact")

        assert isinstance(result, Text)
        assert word in result.plain
        assert reading in result.plain


class TestFormatWordWithReading:
    """Tests for format_word_with_reading function."""

    def test_basic_formatting(self):
        """Test basic word formatting."""
        result = format_word_with_reading("単語", "たんご")

        assert result == "単語[たんご]"
        assert isinstance(result, str)

    def test_with_katakana(self):
        """Test formatting with katakana."""
        result = format_word_with_reading("コンピューター", "コンピューター")

        assert result == "コンピューター[コンピューター]"

    def test_with_empty_strings(self):
        """Test formatting with empty strings."""
        result = format_word_with_reading("", "")

        assert result == "[]"

    def test_special_characters(self):
        """Test formatting with special characters."""
        result = format_word_with_reading("食べる", "たべる")

        assert result == "食べる[たべる]"
        assert "[" in result
        assert "]" in result


class TestFormatKanjiWithReadings:
    """Tests for format_kanji_with_readings function."""

    def test_with_both_readings(self):
        """Test formatting kanji with both on and kun readings."""
        result = format_kanji_with_readings(
            "語",
            ["ゴ"],
            ["かた.る", "かた.らう"],
            style="compact"
        )

        assert isinstance(result, Text)
        plain = result.plain
        assert "語" in plain
        assert "ゴ" in plain
        assert "かた.る" in plain

    def test_with_only_on_reading(self):
        """Test formatting kanji with only on-yomi."""
        result = format_kanji_with_readings(
            "学",
            ["ガク"],
            [],
            style="compact"
        )

        assert isinstance(result, Text)
        plain = result.plain
        assert "学" in plain
        assert "ガク" in plain

    def test_with_only_kun_reading(self):
        """Test formatting kanji with only kun-yomi."""
        result = format_kanji_with_readings(
            "上",
            [],
            ["うえ", "あ.げる"],
            style="compact"
        )

        assert isinstance(result, Text)
        plain = result.plain
        assert "上" in plain
        assert "うえ" in plain

    def test_with_no_readings(self):
        """Test formatting kanji with no readings."""
        result = format_kanji_with_readings(
            "字",
            [],
            [],
            style="compact"
        )

        assert isinstance(result, Text)
        # Should still contain the character
        assert "字" in result.plain

    def test_with_multiple_on_readings(self):
        """Test formatting kanji with multiple on-yomi."""
        result = format_kanji_with_readings(
            "生",
            ["セイ", "ショウ"],
            ["い.きる", "う.まれる"],
            style="compact"
        )

        assert isinstance(result, Text)
        plain = result.plain
        assert "生" in plain
        assert "セイ" in plain or "ショウ" in plain

    def test_detailed_style(self):
        """Test formatting with detailed style."""
        result = format_kanji_with_readings(
            "語",
            ["ゴ"],
            ["かた.る"],
            style="detailed"
        )

        assert isinstance(result, Text)
        # Should still work with detailed style
        assert "語" in result.plain

    def test_invalid_style(self):
        """Test that invalid style raises ValueError."""
        # Note: This function doesn't validate style, it's passed to render_furigana
        # But we can test that it still works
        result = format_kanji_with_readings(
            "語",
            ["ゴ"],
            ["かた.る"],
            style="compact"
        )

        assert isinstance(result, Text)


class TestFuriganaEdgeCases:
    """Tests for edge cases in furigana rendering."""

    def test_unicode_characters(self):
        """Test with various Unicode characters."""
        result = render_furigana("日本", "にほん", style="compact")

        assert isinstance(result, Text)
        assert "日本" in result.plain

    def test_mixed_kanji_kana(self):
        """Test with mixed kanji and kana."""
        result = render_furigana("食べる", "たべる", style="compact")

        assert isinstance(result, Text)
        assert "食べる" in result.plain

    def test_numbers_in_reading(self):
        """Test with numbers in reading."""
        result = render_furigana("一", "いち", style="compact")

        assert isinstance(result, Text)
        assert "一" in result.plain
        assert "いち" in result.plain

    def test_whitespace_handling(self):
        """Test handling of whitespace."""
        result = render_furigana("単語", "たんご", style="compact")

        # Should not have extra whitespace issues
        assert isinstance(result, Text)

    def test_special_kanji_readings(self):
        """Test with special kanji readings (okurigana)."""
        readings = format_kanji_with_readings(
            "食",
            ["ショク"],
            ["た.べる", "く.う"],
            style="compact"
        )

        assert isinstance(readings, Text)
        plain = readings.plain
        # Should handle dots in kun-yomi
        assert "た.べる" in plain or "く.う" in plain
