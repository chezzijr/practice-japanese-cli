"""
Tests for grammar CLI commands.

Tests the cli/grammar.py module which implements add, list, show,
and edit commands for grammar points.
"""

import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

from japanese_cli.cli.grammar import app
from japanese_cli.models import GrammarPoint, Example


# Create CLI test runner
runner = CliRunner()


class TestGrammarAddCommand:
    """Tests for grammar add command."""

    @patch('japanese_cli.cli.grammar.add_grammar')
    @patch('japanese_cli.cli.grammar.prompt_grammar_data')
    def test_add_grammar_success(self, mock_prompt, mock_add):
        """Test successfully adding a grammar point."""
        # Mock prompt to return grammar data
        mock_prompt.return_value = {
            "title": "は (wa) particle",
            "structure": "Noun + は",
            "explanation": "Topic marker particle",
            "jlpt_level": "n5",
            "examples": [
                {
                    "jp": "私は学生です",
                    "vi": "Tôi là sinh viên",
                    "en": "I am a student"
                }
            ],
            "related_grammar": [],
            "notes": "Basic particle"
        }

        # Mock successful add
        mock_add.return_value = 1

        result = runner.invoke(app, ["add"])

        assert result.exit_code == 0
        assert "added successfully" in result.stdout.lower() or "✓" in result.stdout
        mock_add.assert_called_once()

    @patch('japanese_cli.cli.grammar.prompt_grammar_data')
    def test_add_grammar_cancelled(self, mock_prompt):
        """Test cancelling grammar addition."""
        # Mock prompt to return None (cancelled)
        mock_prompt.return_value = None

        result = runner.invoke(app, ["add"])

        assert result.exit_code == 0
        assert "no grammar point added" in result.stdout.lower()

    @patch('japanese_cli.cli.grammar.add_grammar')
    @patch('japanese_cli.cli.grammar.prompt_grammar_data')
    def test_add_grammar_with_minimal_data(self, mock_prompt, mock_add):
        """Test adding grammar with minimal required fields."""
        mock_prompt.return_value = {
            "title": "を (wo) particle",
            "structure": None,
            "explanation": "Object marker",
            "jlpt_level": None,
            "examples": [
                {
                    "jp": "本を読む",
                    "vi": "Đọc sách",
                    "en": None
                }
            ],
            "related_grammar": "[]",
            "notes": None
        }

        mock_add.return_value = 1

        result = runner.invoke(app, ["add"])

        assert result.exit_code == 0
        assert "added successfully" in result.stdout.lower() or "✓" in result.stdout
        mock_add.assert_called_once()

    @patch('japanese_cli.cli.grammar.prompt_grammar_data')
    @patch('japanese_cli.cli.grammar.add_grammar')
    def test_add_grammar_database_error(self, mock_add, mock_prompt):
        """Test error during database insertion."""
        mock_prompt.return_value = {
            "title": "Test",
            "structure": None,
            "explanation": "Test",
            "jlpt_level": None,
            "examples": [{"jp": "テスト", "vi": "test", "en": None}],
            "related_grammar": "[]",
            "notes": None
        }
        mock_add.side_effect = Exception("Database error")

        result = runner.invoke(app, ["add"])

        assert result.exit_code == 1
        assert "error" in result.stdout.lower()


class TestGrammarListCommand:
    """Tests for grammar list command."""

    @patch('japanese_cli.cli.grammar.list_grammar')
    def test_list_grammar_basic(self, mock_list):
        """Test listing all grammar points."""
        mock_list.return_value = [{
            "id": 1,
            "title": "Test Grammar",
            "structure": "Test",
            "explanation": "Test explanation",
            "jlpt_level": "n5",
            "examples": '[{"jp": "テスト", "vi": "test", "en": null}]',
            "related_grammar": "[]",
            "notes": None,
            "created_at": "2024-01-01 00:00:00",
            "updated_at": "2024-01-01 00:00:00"
        }]

        result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        mock_list.assert_called_once()

    @patch('japanese_cli.cli.grammar.list_grammar')
    def test_list_grammar_with_jlpt_filter(self, mock_list):
        """Test listing with JLPT level filter."""
        mock_list.return_value = []

        result = runner.invoke(app, ["list", "--level", "n5"])

        assert result.exit_code == 0
        mock_list.assert_called_once_with(jlpt_level="n5", limit=None, offset=0)

    @patch('japanese_cli.cli.grammar.list_grammar')
    def test_list_grammar_with_limit(self, mock_list):
        """Test listing with limit."""
        mock_list.return_value = []

        result = runner.invoke(app, ["list", "--limit", "5"])

        assert result.exit_code == 0
        mock_list.assert_called_once_with(jlpt_level=None, limit=5, offset=0)

    @patch('japanese_cli.cli.grammar.list_grammar')
    def test_list_grammar_with_offset(self, mock_list):
        """Test listing with offset."""
        mock_list.return_value = []

        result = runner.invoke(app, ["list", "--limit", "5", "--offset", "2"])

        assert result.exit_code == 0
        mock_list.assert_called_once_with(jlpt_level=None, limit=5, offset=2)

    def test_list_grammar_invalid_jlpt_level(self):
        """Test listing with invalid JLPT level."""
        result = runner.invoke(app, ["list", "--level", "n6"])

        assert result.exit_code == 1
        assert "invalid jlpt level" in result.stdout.lower()

    @patch('japanese_cli.cli.grammar.list_grammar')
    def test_list_grammar_empty_database(self, mock_list):
        """Test listing with empty database."""
        mock_list.return_value = []

        result = runner.invoke(app, ["list"])

        # Should show helpful message
        assert result.exit_code == 0
        assert "no grammar points found" in result.stdout.lower()
        assert "add" in result.stdout.lower()

    @patch('japanese_cli.cli.grammar.list_grammar')
    def test_list_grammar_combined_filters(self, mock_list):
        """Test listing with multiple filters."""
        mock_list.return_value = []

        result = runner.invoke(app, ["list", "--level", "n5", "--limit", "10", "--offset", "0"])

        assert result.exit_code == 0
        mock_list.assert_called_once_with(jlpt_level="n5", limit=10, offset=0)

    @patch('japanese_cli.cli.grammar.list_grammar')
    def test_list_grammar_database_error(self, mock_list):
        """Test error during database query."""
        mock_list.side_effect = Exception("Database error")

        result = runner.invoke(app, ["list"])

        assert result.exit_code == 1
        assert "error" in result.stdout.lower()


class TestGrammarShowCommand:
    """Tests for grammar show command."""

    @patch('japanese_cli.cli.grammar.get_grammar_by_id')
    def test_show_grammar_exists(self, mock_get):
        """Test showing existing grammar point."""
        mock_get.return_value = {
            "id": 1,
            "title": "Test Grammar",
            "structure": "Test",
            "explanation": "Test explanation",
            "jlpt_level": "n5",
            "examples": '[{"jp": "テスト", "vi": "test", "en": null}]',
            "related_grammar": "[]",
            "notes": None,
            "created_at": "2024-01-01 00:00:00",
            "updated_at": "2024-01-01 00:00:00"
        }

        result = runner.invoke(app, ["show", "1"])

        assert result.exit_code == 0
        mock_get.assert_called_once_with(1)

    @patch('japanese_cli.cli.grammar.get_grammar_by_id')
    def test_show_grammar_not_found(self, mock_get):
        """Test showing non-existent grammar point."""
        mock_get.return_value = None

        result = runner.invoke(app, ["show", "99999"])

        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()

    @patch('japanese_cli.cli.grammar.get_grammar_by_id')
    def test_show_grammar_zero_id(self, mock_get):
        """Test showing with ID 0."""
        mock_get.return_value = None

        result = runner.invoke(app, ["show", "0"])

        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()

    def test_show_grammar_negative_id(self):
        """Test showing with negative ID."""
        result = runner.invoke(app, ["show", "-1"])

        # Typer may reject negative IDs
        assert result.exit_code != 0

    @patch('japanese_cli.cli.grammar.get_grammar_by_id')
    def test_show_grammar_database_error(self, mock_get):
        """Test error during database query."""
        mock_get.side_effect = Exception("Database error")

        result = runner.invoke(app, ["show", "1"])

        assert result.exit_code == 1
        assert "error" in result.stdout.lower()


class TestGrammarEditCommand:
    """Tests for grammar edit command."""

    @patch('japanese_cli.cli.grammar.get_grammar_by_id')
    @patch('japanese_cli.cli.grammar.prompt_grammar_data')
    @patch('japanese_cli.cli.grammar.update_grammar')
    def test_edit_grammar_success(self, mock_update, mock_prompt, mock_get):
        """Test successfully editing a grammar point."""
        # Mock existing grammar
        mock_get.return_value = {
            "id": 1,
            "title": "Old Title",
            "structure": "Old",
            "explanation": "Old explanation",
            "jlpt_level": "n5",
            "examples": '[{"jp": "古い", "vi": "cũ", "en": null}]',
            "related_grammar": "[]",
            "notes": None,
            "created_at": "2024-01-01 00:00:00",
            "updated_at": "2024-01-01 00:00:00"
        }

        # Mock prompt to return updated data
        mock_prompt.return_value = {
            "title": "Updated Title",
            "structure": "Updated structure",
            "explanation": "Updated explanation",
            "jlpt_level": "n4",
            "examples": [{"jp": "更新", "vi": "cập nhật", "en": "update"}],
            "related_grammar": [],
            "notes": "Updated notes"
        }

        # Mock successful update
        mock_update.return_value = True

        result = runner.invoke(app, ["edit", "1"])

        assert result.exit_code == 0
        assert "updated successfully" in result.stdout.lower() or "✓" in result.stdout

    @patch('japanese_cli.cli.grammar.get_grammar_by_id')
    @patch('japanese_cli.cli.grammar.prompt_grammar_data')
    def test_edit_grammar_cancelled(self, mock_prompt, mock_get):
        """Test cancelling edit."""
        # Mock existing grammar
        mock_get.return_value = {
            "id": 1,
            "title": "Test",
            "structure": None,
            "explanation": "Test",
            "jlpt_level": None,
            "examples": '[{"jp": "テスト", "vi": "test", "en": null}]',
            "related_grammar": "[]",
            "notes": None,
            "created_at": "2024-01-01 00:00:00",
            "updated_at": "2024-01-01 00:00:00"
        }

        # Mock prompt to return None (cancelled)
        mock_prompt.return_value = None

        result = runner.invoke(app, ["edit", "1"])

        assert result.exit_code == 0
        assert "cancelled" in result.stdout.lower() or "no changes" in result.stdout.lower()

    @patch('japanese_cli.cli.grammar.get_grammar_by_id')
    def test_edit_grammar_not_found(self, mock_get):
        """Test editing non-existent grammar point."""
        mock_get.return_value = None

        result = runner.invoke(app, ["edit", "99999"])

        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()

    @patch('japanese_cli.cli.grammar.get_grammar_by_id')
    @patch('japanese_cli.cli.grammar.prompt_grammar_data')
    @patch('japanese_cli.cli.grammar.update_grammar')
    def test_edit_grammar_update_failure(self, mock_update, mock_prompt, mock_get):
        """Test failure during update."""
        # Mock existing grammar
        mock_get.return_value = {
            "id": 1,
            "title": "Old",
            "structure": None,
            "explanation": "Old",
            "jlpt_level": None,
            "examples": '[{"jp": "古い", "vi": "cũ", "en": null}]',
            "related_grammar": "[]",
            "notes": None,
            "created_at": "2024-01-01 00:00:00",
            "updated_at": "2024-01-01 00:00:00"
        }

        # Mock prompt
        mock_prompt.return_value = {
            "title": "Test",
            "structure": None,
            "explanation": "Test",
            "jlpt_level": None,
            "examples": [{"jp": "テスト", "vi": "test", "en": None}],
            "related_grammar": "[]",
            "notes": None
        }

        # Mock failed update
        mock_update.return_value = False

        result = runner.invoke(app, ["edit", "1"])

        assert result.exit_code == 1
        assert "failed" in result.stdout.lower() or "error" in result.stdout.lower()


class TestGrammarCLIIntegration:
    """Integration tests for grammar CLI."""

    @patch('japanese_cli.cli.grammar.add_grammar')
    @patch('japanese_cli.cli.grammar.list_grammar')
    @patch('japanese_cli.cli.grammar.prompt_grammar_data')
    def test_add_then_list(self, mock_prompt, mock_list, mock_add):
        """Test adding grammar then listing it."""
        # Add grammar
        mock_prompt.return_value = {
            "title": "Integration Test",
            "structure": "Test + です",
            "explanation": "Integration test grammar",
            "jlpt_level": "n5",
            "examples": [
                {
                    "jp": "テストです",
                    "vi": "Là test",
                    "en": "It is a test"
                }
            ],
            "related_grammar": [],
            "notes": None
        }

        mock_add.return_value = 1

        add_result = runner.invoke(app, ["add"])
        assert add_result.exit_code == 0

        # List grammar
        mock_list.return_value = []

        list_result = runner.invoke(app, ["list"])
        assert list_result.exit_code == 0

    @patch('japanese_cli.cli.grammar.add_grammar')
    @patch('japanese_cli.cli.grammar.get_grammar_by_id')
    @patch('japanese_cli.cli.grammar.prompt_grammar_data')
    def test_add_then_show(self, mock_prompt, mock_get, mock_add):
        """Test adding grammar then showing it."""
        # Set up mock data for get_grammar_by_id (used by both add and show commands)
        mock_get.return_value = {
            "id": 1,
            "title": "Show Test",
            "structure": None,
            "explanation": "Test for show command",
            "jlpt_level": None,
            "examples": '[{"jp": "表示テスト", "vi": "Test hiển thị", "en": null}]',
            "related_grammar": "[]",
            "notes": None,
            "created_at": "2024-01-01 00:00:00",
            "updated_at": "2024-01-01 00:00:00"
        }

        # Add grammar
        mock_prompt.return_value = {
            "title": "Show Test",
            "structure": None,
            "explanation": "Test for show command",
            "jlpt_level": None,
            "examples": [
                {
                    "jp": "表示テスト",
                    "vi": "Test hiển thị",
                    "en": None
                }
            ],
            "related_grammar": [],
            "notes": None
        }

        mock_add.return_value = 1

        # Add command will call get_grammar_by_id after adding
        add_result = runner.invoke(app, ["add"])
        assert add_result.exit_code == 0

        # Show grammar (reuses the same mock_get)
        show_result = runner.invoke(app, ["show", "1"])
        assert show_result.exit_code == 0


class TestGrammarCLIEdgeCases:
    """Edge case tests for grammar CLI."""

    @patch('japanese_cli.cli.grammar.list_grammar')
    def test_list_with_very_large_limit(self, mock_list):
        """Test listing with very large limit."""
        mock_list.return_value = []

        result = runner.invoke(app, ["list", "--limit", "10000"])

        assert result.exit_code == 0

    @patch('japanese_cli.cli.grammar.list_grammar')
    def test_list_with_large_offset(self, mock_list):
        """Test listing with offset larger than dataset."""
        mock_list.return_value = []

        result = runner.invoke(app, ["list", "--offset", "1000"])

        assert result.exit_code == 0
        assert "no grammar points found" in result.stdout.lower()

    def test_show_missing_argument(self):
        """Test show command without ID argument."""
        result = runner.invoke(app, ["show"])

        # Should fail with missing argument error
        assert result.exit_code != 0

    def test_edit_missing_argument(self):
        """Test edit command without ID argument."""
        result = runner.invoke(app, ["edit"])

        # Should fail with missing argument error
        assert result.exit_code != 0

    def test_invalid_command(self):
        """Test invalid grammar subcommand."""
        result = runner.invoke(app, ["invalid-command"])

        # Should fail with error
        assert result.exit_code != 0


class TestGrammarHelp:
    """Tests for grammar command help."""

    def test_grammar_help(self):
        """Test grammar main help."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "grammar" in result.stdout.lower()
        assert "add" in result.stdout.lower()
        assert "list" in result.stdout.lower()
        assert "show" in result.stdout.lower()
        assert "edit" in result.stdout.lower()

    def test_grammar_add_help(self):
        """Test grammar add help."""
        result = runner.invoke(app, ["add", "--help"])

        assert result.exit_code == 0
        assert "add" in result.stdout.lower()
        assert "grammar" in result.stdout.lower()

    def test_grammar_list_help(self):
        """Test grammar list help."""
        result = runner.invoke(app, ["list", "--help"])

        assert result.exit_code == 0
        assert "list" in result.stdout.lower()
        assert "level" in result.stdout.lower()
        assert "limit" in result.stdout.lower()

    def test_grammar_show_help(self):
        """Test grammar show help."""
        result = runner.invoke(app, ["show", "--help"])

        assert result.exit_code == 0
        assert "show" in result.stdout.lower()
        assert "id" in result.stdout.lower()

    def test_grammar_edit_help(self):
        """Test grammar edit help."""
        result = runner.invoke(app, ["edit", "--help"])

        assert result.exit_code == 0
        assert "edit" in result.stdout.lower()
        assert "id" in result.stdout.lower()
