"""
Tests for Japanese character detection and conversion utilities.

Tests the ui/japanese_utils.py module which handles character type detection
and romaji-to-hiragana conversion.
"""

import pytest

from japanese_cli.ui.japanese_utils import (
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


class TestIsHiragana:
    """Tests for is_hiragana function."""

    def test_hiragana_characters(self):
        """Test that hiragana characters are detected."""
        assert is_hiragana('あ') is True
        assert is_hiragana('ん') is True
        assert is_hiragana('が') is True

    def test_katakana_not_hiragana(self):
        """Test that katakana is not hiragana."""
        assert is_hiragana('ア') is False
        assert is_hiragana('ン') is False

    def test_kanji_not_hiragana(self):
        """Test that kanji is not hiragana."""
        assert is_hiragana('語') is False
        assert is_hiragana('日') is False

    def test_romaji_not_hiragana(self):
        """Test that romaji is not hiragana."""
        assert is_hiragana('a') is False
        assert is_hiragana('n') is False

    def test_empty_string(self):
        """Test empty string returns False."""
        assert is_hiragana('') is False


class TestIsKatakana:
    """Tests for is_katakana function."""

    def test_katakana_characters(self):
        """Test that katakana characters are detected."""
        assert is_katakana('ア') is True
        assert is_katakana('ン') is True
        assert is_katakana('ガ') is True

    def test_hiragana_not_katakana(self):
        """Test that hiragana is not katakana."""
        assert is_katakana('あ') is False
        assert is_katakana('ん') is False

    def test_kanji_not_katakana(self):
        """Test that kanji is not katakana."""
        assert is_katakana('語') is False

    def test_romaji_not_katakana(self):
        """Test that romaji is not katakana."""
        assert is_katakana('a') is False

    def test_empty_string(self):
        """Test empty string returns False."""
        assert is_katakana('') is False


class TestIsKanji:
    """Tests for is_kanji function."""

    def test_kanji_characters(self):
        """Test that kanji characters are detected."""
        assert is_kanji('語') is True
        assert is_kanji('日') is True
        assert is_kanji('本') is True
        assert is_kanji('学') is True

    def test_hiragana_not_kanji(self):
        """Test that hiragana is not kanji."""
        assert is_kanji('あ') is False
        assert is_kanji('ん') is False

    def test_katakana_not_kanji(self):
        """Test that katakana is not kanji."""
        assert is_kanji('ア') is False
        assert is_kanji('ン') is False

    def test_romaji_not_kanji(self):
        """Test that romaji is not kanji."""
        assert is_kanji('a') is False

    def test_empty_string(self):
        """Test empty string returns False."""
        assert is_kanji('') is False


class TestIsJapaneseChar:
    """Tests for is_japanese_char function."""

    def test_hiragana_is_japanese(self):
        """Test hiragana is recognized as Japanese."""
        assert is_japanese_char('あ') is True
        assert is_japanese_char('ん') is True

    def test_katakana_is_japanese(self):
        """Test katakana is recognized as Japanese."""
        assert is_japanese_char('ア') is True
        assert is_japanese_char('ン') is True

    def test_kanji_is_japanese(self):
        """Test kanji is recognized as Japanese."""
        assert is_japanese_char('語') is True
        assert is_japanese_char('日') is True

    def test_romaji_not_japanese(self):
        """Test romaji is not Japanese."""
        assert is_japanese_char('a') is False
        assert is_japanese_char('z') is False

    def test_numbers_not_japanese(self):
        """Test numbers are not Japanese characters."""
        assert is_japanese_char('1') is False
        assert is_japanese_char('5') is False


class TestContainsJapanese:
    """Tests for contains_japanese function."""

    def test_hiragana_only(self):
        """Test text with only hiragana."""
        assert contains_japanese('あいうえお') is True
        assert contains_japanese('こんにちは') is True

    def test_katakana_only(self):
        """Test text with only katakana."""
        assert contains_japanese('アイウエオ') is True
        assert contains_japanese('コーヒー') is True

    def test_kanji_only(self):
        """Test text with only kanji."""
        assert contains_japanese('日本語') is True
        assert contains_japanese('単語') is True

    def test_mixed_japanese(self):
        """Test text with mixed Japanese characters."""
        assert contains_japanese('日本ご') is True
        assert contains_japanese('コンピューター') is True

    def test_japanese_with_romaji(self):
        """Test text with both Japanese and romaji."""
        assert contains_japanese('hello 世界') is True
        assert contains_japanese('tanago 単語') is True

    def test_romaji_only(self):
        """Test text with only romaji."""
        assert contains_japanese('hello') is False
        assert contains_japanese('tanago') is False

    def test_empty_string(self):
        """Test empty string."""
        assert contains_japanese('') is False


class TestIsRomaji:
    """Tests for is_romaji function."""

    def test_pure_romaji(self):
        """Test pure romaji strings."""
        assert is_romaji('tanago') is True
        assert is_romaji('nihongo') is True
        assert is_romaji('hello world') is True

    def test_romaji_with_numbers(self):
        """Test romaji with numbers."""
        assert is_romaji('test123') is True

    def test_romaji_with_punctuation(self):
        """Test romaji with punctuation."""
        assert is_romaji('hello, world!') is True
        assert is_romaji("it's ok") is True

    def test_japanese_not_romaji(self):
        """Test Japanese characters are not romaji."""
        assert is_romaji('単語') is False
        assert is_romaji('こんにちは') is False
        assert is_romaji('カタカナ') is False

    def test_mixed_not_romaji(self):
        """Test mixed text is not romaji."""
        assert is_romaji('hello 単語') is False
        assert is_romaji('tanago たなご') is False

    def test_empty_string(self):
        """Test empty string."""
        assert is_romaji('') is False


class TestRomajiToHiragana:
    """Tests for romaji_to_hiragana function."""

    def test_basic_conversion(self):
        """Test basic romaji to hiragana conversion."""
        assert romaji_to_hiragana('tanago') == 'たなご'
        assert romaji_to_hiragana('nihongo') == 'にほんご'
        # Note: wanakana converts 'wa' sound to 'わ' (not 'は' particle)
        assert romaji_to_hiragana('konnichiwa') == 'こんにちわ'

    def test_long_vowels(self):
        """Test long vowel conversion."""
        assert romaji_to_hiragana('toukyou') == 'とうきょう'
        # Note: wanakana converts double vowels literally (not as long vowel marks)
        assert romaji_to_hiragana('koohii') == 'こおひい'

    def test_double_consonants(self):
        """Test double consonant (sokuon) conversion."""
        assert romaji_to_hiragana('gakkou') == 'がっこう'
        assert romaji_to_hiragana('kitte') == 'きって'

    def test_particles(self):
        """Test particle conversion."""
        assert romaji_to_hiragana('wa') == 'わ'
        assert romaji_to_hiragana('wo') == 'を'
        assert romaji_to_hiragana('he') == 'へ'

    def test_empty_string(self):
        """Test empty string."""
        assert romaji_to_hiragana('') == ''

    def test_already_hiragana(self):
        """Test that hiragana passthrough depends on wanakana behavior."""
        # This test documents actual wanakana behavior
        result = romaji_to_hiragana('こんにちは')
        # Wanakana should keep hiragana as-is
        assert result == 'こんにちは'


class TestValidateJapaneseText:
    """Tests for validate_japanese_text function."""

    def test_valid_hiragana(self):
        """Test valid hiragana passes validation."""
        validate_japanese_text('こんにちは', 'Word')
        # No exception raised

    def test_valid_katakana(self):
        """Test valid katakana passes validation."""
        validate_japanese_text('カタカナ', 'Word')
        # No exception raised

    def test_valid_kanji(self):
        """Test valid kanji passes validation."""
        validate_japanese_text('単語', 'Word')
        # No exception raised

    def test_valid_mixed(self):
        """Test valid mixed Japanese passes validation."""
        validate_japanese_text('日本語', 'Word')
        # No exception raised

    def test_romaji_raises_error(self):
        """Test romaji raises ValueError."""
        with pytest.raises(ValueError, match="must be in Japanese characters, not romaji"):
            validate_japanese_text('tanago', 'Word')

    def test_empty_string_raises_error(self):
        """Test empty string raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_japanese_text('', 'Word')

    def test_whitespace_only_raises_error(self):
        """Test whitespace only raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_japanese_text('   ', 'Word')

    def test_numbers_only_raises_error(self):
        """Test numbers only raises ValueError."""
        # Numbers are considered romaji by is_romaji(), so error message differs
        with pytest.raises(ValueError, match="not romaji"):
            validate_japanese_text('12345', 'Word')


class TestGetCharacterType:
    """Tests for get_character_type function."""

    def test_hiragana_type(self):
        """Test hiragana character type."""
        assert get_character_type('あ') == 'hiragana'
        assert get_character_type('ん') == 'hiragana'

    def test_katakana_type(self):
        """Test katakana character type."""
        assert get_character_type('ア') == 'katakana'
        assert get_character_type('ン') == 'katakana'

    def test_kanji_type(self):
        """Test kanji character type."""
        assert get_character_type('語') == 'kanji'
        assert get_character_type('日') == 'kanji'

    def test_romaji_type(self):
        """Test romaji character type."""
        assert get_character_type('a') == 'romaji'
        assert get_character_type('z') == 'romaji'

    def test_other_type(self):
        """Test other character types."""
        assert get_character_type('1') == 'other'
        assert get_character_type('!') == 'other'
        assert get_character_type(' ') == 'other'

    def test_empty_string(self):
        """Test empty string."""
        assert get_character_type('') == 'other'


class TestContainsOnlyKana:
    """Tests for contains_only_kana function."""

    def test_hiragana_only(self):
        """Test text with only hiragana."""
        assert contains_only_kana('ひらがな') is True
        assert contains_only_kana('こんにちは') is True

    def test_katakana_only(self):
        """Test text with only katakana."""
        assert contains_only_kana('カタカナ') is True
        assert contains_only_kana('コーヒー') is True

    def test_mixed_kana(self):
        """Test text with mixed hiragana and katakana."""
        assert contains_only_kana('ひらカタ') is True
        assert contains_only_kana('これはカタカナ') is True

    def test_kana_with_spaces(self):
        """Test kana with spaces."""
        assert contains_only_kana('こんにちは せかい') is True

    def test_kanji_not_only_kana(self):
        """Test that kanji fails the check."""
        assert contains_only_kana('漢字') is False
        assert contains_only_kana('ひら漢字') is False

    def test_romaji_not_only_kana(self):
        """Test that romaji fails the check."""
        assert contains_only_kana('hiragana') is False
        assert contains_only_kana('こんにちは world') is False

    def test_empty_string(self):
        """Test empty string."""
        assert contains_only_kana('') is False

    def test_spaces_only(self):
        """Test spaces only."""
        assert contains_only_kana('   ') is False
