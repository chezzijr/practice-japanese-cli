"""
Tests for interactive prompt utilities.

Tests the ui/prompts.py module which handles user input collection
for vocabulary and kanji data.
"""

import pytest
from unittest.mock import patch, MagicMock
from pydantic import ValidationError

from japanese_cli.models import Vocabulary, Kanji
from japanese_cli.ui.prompts import (
    prompt_vocabulary_data,
    prompt_kanji_data,
    confirm_action,
    prompt_jlpt_level,
    prompt_item_type,
    select_from_vocabulary_matches,
    select_from_kanji_matches,
)


class TestPromptVocabularyData:
    """Tests for prompt_vocabulary_data function."""

    @patch('japanese_cli.ui.prompts.Prompt.ask')
    def test_prompt_basic_vocabulary(self, mock_ask):
        """Test prompting for basic vocabulary data."""
        # Mock user inputs
        mock_ask.side_effect = [
            "単語",  # word
            "たんご",  # reading
            "từ vựng",  # Vietnamese meaning
            "word",  # English meaning
            "đơn ngữ",  # Vietnamese reading
            "n5",  # JLPT level
            "noun",  # Part of speech
            "common",  # Tags
            "Basic word",  # Notes
        ]

        data = prompt_vocabulary_data()

        assert data is not None
        assert data["word"] == "単語"
        assert data["reading"] == "たんご"
        assert data["meanings"]["vi"] == ["từ vựng"]
        assert data["meanings"]["en"] == ["word"]
        assert data["vietnamese_reading"] == "đơn ngữ"
        assert data["jlpt_level"] == "n5"
        assert data["part_of_speech"] == "noun"
        assert "common" in data["tags"]
        assert data["notes"] == "Basic word"

    @patch('japanese_cli.ui.prompts.Prompt.ask')
    def test_prompt_vocabulary_minimal_data(self, mock_ask):
        """Test prompting with minimal required data."""
        mock_ask.side_effect = [
            "テスト",  # word
            "テスト",  # reading
            "kiểm tra",  # Vietnamese meaning
            "",  # English meaning (optional)
            "",  # Vietnamese reading (optional)
            "",  # JLPT level (optional)
            "",  # Part of speech (optional)
            "",  # Tags (optional)
            "",  # Notes (optional)
        ]

        data = prompt_vocabulary_data()

        assert data is not None
        assert data["word"] == "テスト"
        assert data["reading"] == "テスト"
        assert data["meanings"]["vi"] == ["kiểm tra"]
        assert "en" not in data["meanings"] or not data["meanings"]["en"]
        assert data["vietnamese_reading"] is None
        assert data["jlpt_level"] is None

    @patch('japanese_cli.ui.prompts.Prompt.ask')
    def test_prompt_vocabulary_with_existing(self, mock_ask):
        """Test prompting with existing vocabulary data pre-filled."""
        existing = Vocabulary(
            id=1,
            word="勉強",
            reading="べんきょう",
            meanings={"vi": ["học tập"], "en": ["study"]},
            jlpt_level="n5"
        )

        # Mock that user just presses Enter for all fields (keep existing)
        mock_ask.side_effect = [
            "勉強",  # word (default)
            "べんきょう",  # reading (default)
            "học tập",  # Vietnamese meaning (default)
            "study",  # English meaning (default)
            "",  # Vietnamese reading
            "n5",  # JLPT level (default)
            "",  # Part of speech
            "",  # Tags
            "",  # Notes
        ]

        data = prompt_vocabulary_data(existing=existing)

        assert data is not None
        assert data["word"] == "勉強"
        assert data["jlpt_level"] == "n5"

    @patch('japanese_cli.ui.prompts.Prompt.ask')
    def test_prompt_vocabulary_keyboard_interrupt(self, mock_ask):
        """Test handling keyboard interrupt (Ctrl+C)."""
        mock_ask.side_effect = KeyboardInterrupt()

        data = prompt_vocabulary_data()

        assert data is None

    @patch('japanese_cli.ui.prompts.Prompt.ask')
    def test_prompt_vocabulary_multiple_tags(self, mock_ask):
        """Test prompting with multiple tags."""
        mock_ask.side_effect = [
            "単語",
            "たんご",
            "từ vựng",
            "",
            "",
            "",
            "",
            "common, beginner, n5",  # Multiple tags
            "",
        ]

        data = prompt_vocabulary_data()

        assert data is not None
        assert len(data["tags"]) == 3
        assert "common" in data["tags"]
        assert "beginner" in data["tags"]
        assert "n5" in data["tags"]


class TestPromptKanjiData:
    """Tests for prompt_kanji_data function."""

    @patch('japanese_cli.ui.prompts.Prompt.ask')
    def test_prompt_basic_kanji(self, mock_ask):
        """Test prompting for basic kanji data."""
        mock_ask.side_effect = [
            "語",  # character
            "ゴ",  # on-yomi
            "かた.る, かた.らう",  # kun-yomi
            "ngữ",  # Vietnamese meaning
            "word",  # English meaning
            "ngữ",  # Hán Việt
            "n5",  # JLPT level
            "14",  # Stroke count
            "言",  # Radical
            "Used in 日本語",  # Notes
        ]

        data = prompt_kanji_data()

        assert data is not None
        assert data["character"] == "語"
        assert "ゴ" in data["on_readings"]
        assert "かた.る" in data["kun_readings"]
        assert data["meanings"]["vi"] == ["ngữ"]
        assert data["vietnamese_reading"] == "ngữ"
        assert data["jlpt_level"] == "n5"
        assert data["stroke_count"] == 14
        assert data["radical"] == "言"

    @patch('japanese_cli.ui.prompts.Prompt.ask')
    def test_prompt_kanji_minimal_data(self, mock_ask):
        """Test prompting kanji with minimal required data."""
        mock_ask.side_effect = [
            "日",  # character
            "",  # on-yomi (optional)
            "ひ",  # kun-yomi
            "nhật",  # Vietnamese meaning
            "",  # English meaning (optional)
            "",  # Hán Việt (optional)
            "",  # JLPT level (optional)
            "",  # Stroke count (optional)
            "",  # Radical (optional)
            "",  # Notes (optional)
        ]

        data = prompt_kanji_data()

        assert data is not None
        assert data["character"] == "日"
        assert data["on_readings"] == []
        assert "ひ" in data["kun_readings"]

    @patch('japanese_cli.ui.prompts.Prompt.ask')
    def test_prompt_kanji_with_existing(self, mock_ask):
        """Test prompting with existing kanji data."""
        existing = Kanji(
            id=1,
            character="学",
            on_readings=["ガク"],
            kun_readings=["まな.ぶ"],
            meanings={"vi": ["học"]},
            jlpt_level="n5"
        )

        mock_ask.side_effect = [
            "学",  # character (default)
            "ガク",  # on-yomi (default)
            "まな.ぶ",  # kun-yomi (default)
            "học",  # Vietnamese meaning (default)
            "",  # English meaning
            "",  # Hán Việt
            "n5",  # JLPT level (default)
            "",  # Stroke count
            "",  # Radical
            "",  # Notes
        ]

        data = prompt_kanji_data(existing=existing)

        assert data is not None
        assert data["character"] == "学"

    @patch('japanese_cli.ui.prompts.Prompt.ask')
    def test_prompt_kanji_multiple_character_retry(self, mock_ask):
        """Test that multi-character input is rejected."""
        # First attempt: multiple characters, second attempt: single character
        mock_ask.side_effect = [
            "語学",  # Too many characters (will retry)
            "語",  # Correct
            "",  # on-yomi
            "",  # kun-yomi
            "ngữ",  # Vietnamese meaning
            "",  # English meaning
            "",  # Hán Việt
            "",  # JLPT level
            "",  # Stroke count
            "",  # Radical
            "",  # Notes
        ]

        data = prompt_kanji_data()

        assert data is not None
        assert data["character"] == "語"
        assert len(data["character"]) == 1

    @patch('japanese_cli.ui.prompts.Prompt.ask')
    def test_prompt_kanji_keyboard_interrupt(self, mock_ask):
        """Test handling keyboard interrupt."""
        mock_ask.side_effect = KeyboardInterrupt()

        data = prompt_kanji_data()

        assert data is None

    @patch('japanese_cli.ui.prompts.Prompt.ask')
    def test_prompt_kanji_multiple_readings(self, mock_ask):
        """Test kanji with multiple readings."""
        mock_ask.side_effect = [
            "生",
            "セイ, ショウ",  # Multiple on-yomi
            "い.きる, う.まれる",  # Multiple kun-yomi
            "sinh",
            "",
            "",
            "",
            "",
            "",
            "",
        ]

        data = prompt_kanji_data()

        assert data is not None
        assert len(data["on_readings"]) == 2
        assert "セイ" in data["on_readings"]
        assert "ショウ" in data["on_readings"]
        assert len(data["kun_readings"]) == 2


class TestConfirmAction:
    """Tests for confirm_action function."""

    @patch('japanese_cli.ui.prompts.Confirm.ask')
    def test_confirm_yes(self, mock_confirm):
        """Test confirmation returning True."""
        mock_confirm.return_value = True

        result = confirm_action("Continue?")

        assert result is True
        mock_confirm.assert_called_once()

    @patch('japanese_cli.ui.prompts.Confirm.ask')
    def test_confirm_no(self, mock_confirm):
        """Test confirmation returning False."""
        mock_confirm.return_value = False

        result = confirm_action("Delete?", default=False)

        assert result is False

    @patch('japanese_cli.ui.prompts.Confirm.ask')
    def test_confirm_with_default_true(self, mock_confirm):
        """Test confirmation with default=True."""
        mock_confirm.return_value = True

        result = confirm_action("Proceed?", default=True)

        assert result is True

    @patch('japanese_cli.ui.prompts.Confirm.ask')
    def test_confirm_keyboard_interrupt(self, mock_confirm):
        """Test handling keyboard interrupt in confirmation."""
        mock_confirm.side_effect = KeyboardInterrupt()

        result = confirm_action("Continue?")

        assert result is False


class TestPromptJLPTLevel:
    """Tests for prompt_jlpt_level function."""

    @patch('japanese_cli.ui.prompts.Prompt.ask')
    def test_prompt_n5_level(self, mock_ask):
        """Test prompting for N5 level."""
        mock_ask.return_value = "n5"

        result = prompt_jlpt_level()

        assert result == "n5"

    @patch('japanese_cli.ui.prompts.Prompt.ask')
    def test_prompt_all_levels(self, mock_ask):
        """Test prompting for 'all' returns None."""
        mock_ask.return_value = "all"

        result = prompt_jlpt_level()

        assert result is None

    @patch('japanese_cli.ui.prompts.Prompt.ask')
    def test_prompt_with_default(self, mock_ask):
        """Test prompting with default level."""
        mock_ask.return_value = "n4"

        result = prompt_jlpt_level(default="n4")

        assert result == "n4"

    @patch('japanese_cli.ui.prompts.Prompt.ask')
    def test_prompt_keyboard_interrupt(self, mock_ask):
        """Test handling keyboard interrupt."""
        mock_ask.side_effect = KeyboardInterrupt()

        result = prompt_jlpt_level()

        assert result is None


class TestPromptItemType:
    """Tests for prompt_item_type function."""

    @patch('japanese_cli.ui.prompts.Prompt.ask')
    def test_prompt_vocab_type(self, mock_ask):
        """Test prompting for vocab type."""
        mock_ask.return_value = "vocab"

        result = prompt_item_type()

        assert result == "vocab"

    @patch('japanese_cli.ui.prompts.Prompt.ask')
    def test_prompt_kanji_type(self, mock_ask):
        """Test prompting for kanji type."""
        mock_ask.return_value = "kanji"

        result = prompt_item_type()

        assert result == "kanji"

    @patch('japanese_cli.ui.prompts.Prompt.ask')
    def test_prompt_keyboard_interrupt(self, mock_ask):
        """Test handling keyboard interrupt."""
        mock_ask.side_effect = KeyboardInterrupt()

        result = prompt_item_type()

        assert result is None


class TestPromptEdgeCases:
    """Tests for edge cases in prompts."""

    @patch('japanese_cli.ui.prompts.Prompt.ask')
    def test_vocabulary_with_special_characters(self, mock_ask):
        """Test vocabulary prompt with special characters."""
        mock_ask.side_effect = [
            "〜です",
            "です",
            "là [lịch sự]",
            "",
            "",
            "",
            "",
            "",
            "",
        ]

        data = prompt_vocabulary_data()

        assert data is not None
        assert data["word"] == "〜です"

    @patch('japanese_cli.ui.prompts.Prompt.ask')
    def test_kanji_with_whitespace_in_readings(self, mock_ask):
        """Test kanji with whitespace in readings list."""
        mock_ask.side_effect = [
            "語",
            " ゴ ",  # Whitespace around reading
            " かた.る , かた.らう ",  # Whitespace in list
            "ngữ",
            "",
            "",
            "",
            "",
            "",
            "",
        ]

        data = prompt_kanji_data()

        assert data is not None
        # Should strip whitespace
        assert "ゴ" in data["on_readings"]
        assert "かた.る" in data["kun_readings"]

    @patch('japanese_cli.ui.prompts.Prompt.ask')
    def test_vocabulary_with_commas_in_tags(self, mock_ask):
        """Test vocabulary with various tag formats."""
        mock_ask.side_effect = [
            "テスト",  # Use katakana instead of romaji
            "テスト",
            "テスト",
            "",
            "",
            "",
            "",
            "tag1,tag2, tag3 , tag4",  # Various spacing
            "",
        ]

        data = prompt_vocabulary_data()

        assert data is not None
        assert len(data["tags"]) == 4
        assert "tag1" in data["tags"]
        assert "tag4" in data["tags"]


class TestSelectFromVocabularyMatches:
    """Tests for select_from_vocabulary_matches function."""

    @patch('japanese_cli.ui.prompts.IntPrompt.ask')
    @patch('japanese_cli.ui.prompts.console.print')
    def test_select_single_match(self, mock_print, mock_ask):
        """Test selecting from a single vocabulary match."""
        matches = [
            {
                'id': 1,
                'word': '単語',
                'reading': 'たんご',
                'meanings': '{"vi": ["từ vựng"], "en": ["word"]}',
            }
        ]
        mock_ask.return_value = 1

        result = select_from_vocabulary_matches(matches, 'tanago')

        assert result is not None
        assert result['word'] == '単語'
        assert mock_ask.called

    @patch('japanese_cli.ui.prompts.IntPrompt.ask')
    @patch('japanese_cli.ui.prompts.console.print')
    def test_select_multiple_matches(self, mock_print, mock_ask):
        """Test selecting from multiple vocabulary matches."""
        matches = [
            {
                'id': 1,
                'word': '橋',
                'reading': 'はし',
                'meanings': '{"vi": ["cầu"], "en": ["bridge"]}',
            },
            {
                'id': 2,
                'word': '箸',
                'reading': 'はし',
                'meanings': '{"vi": ["đũa"], "en": ["chopsticks"]}',
            },
        ]
        mock_ask.return_value = 2  # Select second match

        result = select_from_vocabulary_matches(matches, 'hashi')

        assert result is not None
        assert result['word'] == '箸'
        assert result['id'] == 2

    @patch('japanese_cli.ui.prompts.IntPrompt.ask')
    @patch('japanese_cli.ui.prompts.console.print')
    def test_select_with_missing_meanings(self, mock_print, mock_ask):
        """Test selection with missing optional fields."""
        matches = [
            {
                'id': 1,
                'word': 'テスト',
                'reading': 'テスト',
                'meanings': '{"vi": ["kiểm tra"]}',  # No English
            }
        ]
        mock_ask.return_value = 1

        result = select_from_vocabulary_matches(matches, 'tesuto')

        assert result is not None
        assert result['word'] == 'テスト'


class TestSelectFromKanjiMatches:
    """Tests for select_from_kanji_matches function."""

    @patch('japanese_cli.ui.prompts.IntPrompt.ask')
    @patch('japanese_cli.ui.prompts.console.print')
    def test_select_single_kanji_match(self, mock_print, mock_ask):
        """Test selecting from a single kanji match."""
        matches = [
            {
                'id': 1,
                'character': '語',
                'on_readings': '["ゴ"]',
                'kun_readings': '["かた.る"]',
                'meanings': '{"vi": ["ngữ"], "en": ["word"]}',
            }
        ]
        mock_ask.return_value = 1

        result = select_from_kanji_matches(matches, 'go')

        assert result is not None
        assert result['character'] == '語'

    @patch('japanese_cli.ui.prompts.IntPrompt.ask')
    @patch('japanese_cli.ui.prompts.console.print')
    def test_select_multiple_kanji_matches(self, mock_print, mock_ask):
        """Test selecting from multiple kanji matches."""
        matches = [
            {
                'id': 1,
                'character': '日',
                'on_readings': '["ニチ", "ジツ"]',
                'kun_readings': '["ひ"]',
                'meanings': '{"vi": ["nhật"], "en": ["day", "sun"]}',
            },
            {
                'id': 2,
                'character': '火',
                'on_readings': '["カ"]',
                'kun_readings': '["ひ"]',
                'meanings': '{"vi": ["hỏa"], "en": ["fire"]}',
            },
        ]
        mock_ask.return_value = 2  # Select second match

        result = select_from_kanji_matches(matches, 'hi')

        assert result is not None
        assert result['character'] == '火'


class TestRomajiLookupVocabulary:
    """Tests for romaji lookup in prompt_vocabulary_data."""

    @patch('japanese_cli.ui.prompts.search_vocabulary_by_reading')
    @patch('japanese_cli.ui.prompts.IntPrompt.ask')
    @patch('japanese_cli.ui.prompts.Prompt.ask')
    def test_romaji_lookup_with_single_match(self, mock_prompt, mock_int_prompt, mock_search):
        """Test romaji input with single database match auto-fills data."""
        # Mock database search result
        mock_search.return_value = [
            {
                'id': 1,
                'word': '単語',
                'reading': 'たんご',
                'meanings': '{"vi": ["từ vựng"], "en": ["word"]}',
                'vietnamese_reading': 'đơn ngữ',
                'jlpt_level': 'n5',
                'part_of_speech': 'noun',
                'tags': '["common"]',
                'notes': None,
            }
        ]
        mock_int_prompt.return_value = 1  # Select first match
        # User enters romaji, then accepts defaults for optional fields
        mock_prompt.side_effect = [
            'tanago',  # word (romaji input)
            # After auto-fill, still prompts for optional fields:
            'đơn ngữ',  # Vietnamese reading (accept auto-filled default)
            'n5',  # JLPT level (accept auto-filled default)
            'noun',  # Part of speech (accept auto-filled default)
            'common',  # Tags (accept auto-filled default)
            '',  # Notes (no default, leave empty)
        ]

        data = prompt_vocabulary_data()

        assert data is not None
        assert data['word'] == '単語'
        assert data['reading'] == 'たんご'
        assert data['vietnamese_reading'] == 'đơn ngữ'
        assert data['jlpt_level'] == 'n5'
        assert mock_search.called
        # Verify search was called with converted hiragana
        search_call_args = mock_search.call_args[0]
        assert search_call_args[0] == 'たなご'

    @patch('japanese_cli.ui.prompts.search_vocabulary_by_reading')
    @patch('japanese_cli.ui.prompts.IntPrompt.ask')
    @patch('japanese_cli.ui.prompts.Prompt.ask')
    def test_romaji_lookup_with_multiple_matches(self, mock_prompt, mock_int_prompt, mock_search):
        """Test romaji input with multiple matches shows selection menu."""
        # Mock database with homonyms
        mock_search.return_value = [
            {
                'id': 1,
                'word': '橋',
                'reading': 'はし',
                'meanings': '{"vi": ["cầu"], "en": ["bridge"]}',
                'vietnamese_reading': None,
                'jlpt_level': 'n5',
                'part_of_speech': 'noun',
                'tags': '[]',
                'notes': None,
            },
            {
                'id': 2,
                'word': '箸',
                'reading': 'はし',
                'meanings': '{"vi": ["đũa"], "en": ["chopsticks"]}',
                'vietnamese_reading': None,
                'jlpt_level': 'n5',
                'part_of_speech': 'noun',
                'tags': '[]',
                'notes': None,
            },
        ]
        mock_int_prompt.return_value = 2  # Select second match (chopsticks)
        mock_prompt.side_effect = [
            'hashi',  # word (romaji input)
            # After auto-fill, prompts for optional fields (no defaults for None values):
            '',  # Vietnamese reading (was None, stays empty)
            'n5',  # JLPT level (accept auto-filled default)
            'noun',  # Part of speech (accept auto-filled default)
            '',  # Tags (was empty, stays empty)
            '',  # Notes
        ]

        data = prompt_vocabulary_data()

        assert data is not None
        assert data['word'] == '箸'
        assert data['reading'] == 'はし'
        assert data['jlpt_level'] == 'n5'
        assert data['part_of_speech'] == 'noun'
        assert mock_int_prompt.called

    @patch('japanese_cli.ui.prompts.search_vocabulary_by_reading')
    @patch('japanese_cli.ui.prompts.Prompt.ask')
    @patch('japanese_cli.ui.prompts.console.print')
    def test_romaji_lookup_no_match_then_japanese(self, mock_console, mock_prompt, mock_search):
        """Test romaji with no match shows error, then accepts Japanese input."""
        mock_search.return_value = []  # No matches
        mock_prompt.side_effect = [
            'tanago',  # Romaji (no match)
            '単語',  # Japanese input (retry)
            'たんご',  # reading
            'từ vựng',  # Vietnamese meaning
            '',  # Rest optional
            '', '', '', '', '',
        ]

        data = prompt_vocabulary_data()

        assert data is not None
        assert data['word'] == '単語'
        assert mock_search.called

    @patch('japanese_cli.ui.prompts.Prompt.ask')
    def test_direct_japanese_input_no_lookup(self, mock_prompt):
        """Test direct Japanese input bypasses romaji lookup."""
        mock_prompt.side_effect = [
            '単語',  # Japanese input directly
            'たんご',
            'từ vựng',
            '', '', '', '', '', '',
        ]

        data = prompt_vocabulary_data()

        assert data is not None
        assert data['word'] == '単語'

    @patch('japanese_cli.ui.prompts.Prompt.ask')
    @patch('japanese_cli.ui.prompts.console.print')
    def test_invalid_input_retry(self, mock_console, mock_prompt):
        """Test invalid input (neither romaji nor Japanese) prompts retry."""
        mock_prompt.side_effect = [
            '123',  # Invalid (numbers)
            '単語',  # Valid Japanese
            'たんご',
            'từ vựng',
            '', '', '', '', '', '',
        ]

        data = prompt_vocabulary_data()

        assert data is not None
        assert data['word'] == '単語'


class TestRomajiLookupKanji:
    """Tests for romaji lookup in prompt_kanji_data."""

    @patch('japanese_cli.ui.prompts.search_kanji_by_reading')
    @patch('japanese_cli.ui.prompts.IntPrompt.ask')
    @patch('japanese_cli.ui.prompts.Prompt.ask')
    def test_romaji_lookup_kanji_single_match(self, mock_prompt, mock_int_prompt, mock_search):
        """Test romaji input for kanji with single match auto-fills."""
        mock_search.return_value = [
            {
                'id': 1,
                'character': '語',
                'on_readings': '["ゴ"]',
                'kun_readings': '["かた.る"]',
                'meanings': '{"vi": ["ngữ"], "en": ["word"]}',
                'vietnamese_reading': 'ngữ',
                'jlpt_level': 'n5',
                'stroke_count': 14,
                'radical': '言',
                'notes': None,
            }
        ]
        mock_int_prompt.return_value = 1
        mock_prompt.side_effect = [
            'go',  # character (romaji input)
            # After auto-fill, prompts for optional fields (accepting defaults):
            'ngữ',  # Vietnamese reading (accept auto-filled default)
            'n5',  # JLPT level (accept auto-filled default)
            '14',  # Stroke count (accept auto-filled default)
            '言',  # Radical (accept auto-filled default)
            '',  # Notes (no default)
        ]

        data = prompt_kanji_data()

        assert data is not None
        assert data['character'] == '語'
        assert 'ゴ' in data['on_readings']
        assert data['vietnamese_reading'] == 'ngữ'
        assert data['jlpt_level'] == 'n5'
        assert data['stroke_count'] == 14
        assert mock_search.called

    @patch('japanese_cli.ui.prompts.search_kanji_by_reading')
    @patch('japanese_cli.ui.prompts.IntPrompt.ask')
    @patch('japanese_cli.ui.prompts.Prompt.ask')
    def test_romaji_lookup_kanji_multiple_matches(self, mock_prompt, mock_int_prompt, mock_search):
        """Test romaji lookup with multiple kanji matches."""
        mock_search.return_value = [
            {
                'id': 1,
                'character': '日',
                'on_readings': '["ニチ", "ジツ"]',
                'kun_readings': '["ひ"]',
                'meanings': '{"vi": ["nhật"], "en": ["day"]}',
                'vietnamese_reading': 'nhật',
                'jlpt_level': 'n5',
                'stroke_count': 4,
                'radical': '日',
                'notes': None,
            },
            {
                'id': 2,
                'character': '火',
                'on_readings': '["カ"]',
                'kun_readings': '["ひ"]',
                'meanings': '{"vi": ["hỏa"], "en": ["fire"]}',
                'vietnamese_reading': 'hỏa',
                'jlpt_level': 'n5',
                'stroke_count': 4,
                'radical': '火',
                'notes': None,
            },
        ]
        mock_int_prompt.return_value = 2  # Select fire
        mock_prompt.side_effect = [
            'hi',  # character (romaji input)
            # After auto-fill, prompts for optional fields (accepting defaults):
            'hỏa',  # Vietnamese reading (accept auto-filled default)
            'n5',  # JLPT level (accept auto-filled default)
            '4',  # Stroke count (accept auto-filled default)
            '火',  # Radical (accept auto-filled default)
            '',  # Notes (no default)
        ]

        data = prompt_kanji_data()

        assert data is not None
        assert data['character'] == '火'
        assert 'カ' in data['on_readings']
        assert data['vietnamese_reading'] == 'hỏa'
        assert data['jlpt_level'] == 'n5'
        assert data['stroke_count'] == 4

    @patch('japanese_cli.ui.prompts.search_kanji_by_reading')
    @patch('japanese_cli.ui.prompts.Prompt.ask')
    @patch('japanese_cli.ui.prompts.console.print')
    def test_romaji_lookup_kanji_no_match(self, mock_console, mock_prompt, mock_search):
        """Test romaji with no kanji match shows error."""
        mock_search.return_value = []
        mock_prompt.side_effect = [
            'xyz',  # Romaji with no match
            '語',  # Valid kanji
            '', '',  # readings
            'ngữ',  # meaning
            '', '', '', '', '', '',
        ]

        data = prompt_kanji_data()

        assert data is not None
        assert data['character'] == '語'

    @patch('japanese_cli.ui.prompts.Prompt.ask')
    def test_direct_kanji_input_no_lookup(self, mock_prompt):
        """Test direct kanji input bypasses lookup."""
        mock_prompt.side_effect = [
            '語',  # Direct kanji input
            '', '',  # readings
            'ngữ',  # meaning
            '', '', '', '', '', '',
        ]

        data = prompt_kanji_data()

        assert data is not None
        assert data['character'] == '語'
