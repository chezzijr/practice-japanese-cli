"""
Tests for progress CLI commands.

Tests the cli/progress.py module which implements show, set-level,
and stats commands for progress tracking.
"""

import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from datetime import date, timedelta

from japanese_cli.cli.progress import app


# Create CLI test runner
runner = CliRunner()


class TestProgressShowCommand:
    """Tests for progress show command."""

    @patch('japanese_cli.cli.progress.get_progress')
    @patch('japanese_cli.cli.progress.calculate_vocab_counts_by_level')
    @patch('japanese_cli.cli.progress.calculate_kanji_counts_by_level')
    @patch('japanese_cli.cli.progress.calculate_mastered_items')
    @patch('japanese_cli.cli.progress.get_due_cards')
    @patch('japanese_cli.cli.progress.get_reviews_by_date_range')
    @patch('japanese_cli.cli.progress.calculate_retention_rate')
    @patch('japanese_cli.cli.progress.display_progress_dashboard')
    def test_show_progress_success(
        self, mock_display, mock_retention, mock_reviews, mock_due,
        mock_mastered, mock_kanji, mock_vocab, mock_get_progress
    ):
        """Test successfully displaying progress dashboard."""
        # Mock progress data
        mock_get_progress.return_value = {
            "user_id": "default",
            "current_level": "n5",
            "target_level": "n4",
            "stats": '{"total_vocab": 100, "total_kanji": 50}',
            "milestones": None,
            "streak_days": 5,
            "last_review_date": "2024-01-01",
            "created_at": "2024-01-01 00:00:00",
            "updated_at": "2024-01-01 00:00:00"
        }

        # Mock statistics
        mock_vocab.return_value = {"n5": 100, "n4": 50}
        mock_kanji.return_value = {"n5": 50, "n4": 25}
        mock_mastered.return_value = {"vocab": 20, "kanji": 10}
        mock_due.return_value = []  # No cards due
        mock_reviews.return_value = [{"id": 1}] * 100  # 100 reviews
        mock_retention.return_value = 85.5
        mock_display.return_value = MagicMock()

        result = runner.invoke(app, ["show"])

        assert result.exit_code == 0
        mock_get_progress.assert_called_once()
        mock_display.assert_called_once()

    @patch('japanese_cli.cli.progress.get_progress')
    def test_show_progress_not_initialized(self, mock_get_progress):
        """Test showing progress when not initialized."""
        mock_get_progress.return_value = None

        result = runner.invoke(app, ["show"])

        assert result.exit_code == 1
        assert "not initialized" in result.stdout.lower()

    @patch('japanese_cli.cli.progress.get_progress')
    def test_show_progress_database_error(self, mock_get_progress):
        """Test error during database query."""
        mock_get_progress.side_effect = Exception("Database error")

        result = runner.invoke(app, ["show"])

        assert result.exit_code == 1
        assert "error" in result.stdout.lower()

    @patch('japanese_cli.cli.progress.get_progress')
    @patch('japanese_cli.cli.progress.calculate_vocab_counts_by_level')
    @patch('japanese_cli.cli.progress.calculate_kanji_counts_by_level')
    @patch('japanese_cli.cli.progress.calculate_mastered_items')
    @patch('japanese_cli.cli.progress.get_due_cards')
    @patch('japanese_cli.cli.progress.get_reviews_by_date_range')
    @patch('japanese_cli.cli.progress.calculate_retention_rate')
    @patch('japanese_cli.cli.progress.display_progress_dashboard')
    def test_show_progress_with_due_cards(
        self, mock_display, mock_retention, mock_reviews, mock_due,
        mock_mastered, mock_kanji, mock_vocab, mock_get_progress
    ):
        """Test displaying progress with due cards."""
        mock_get_progress.return_value = {
            "user_id": "default",
            "current_level": "n5",
            "target_level": "n5",
            "stats": '{}',
            "milestones": None,
            "streak_days": 0,
            "last_review_date": None,
            "created_at": "2024-01-01 00:00:00",
            "updated_at": "2024-01-01 00:00:00"
        }

        mock_vocab.return_value = {}
        mock_kanji.return_value = {}
        mock_mastered.return_value = {"vocab": 0, "kanji": 0}
        mock_due.return_value = [{"id": 1}] * 10  # 10 cards due
        mock_reviews.return_value = []
        mock_retention.return_value = 0.0
        mock_display.return_value = MagicMock()

        result = runner.invoke(app, ["show"])

        assert result.exit_code == 0
        assert "10 card" in result.stdout.lower()


class TestProgressSetLevelCommand:
    """Tests for progress set-level command."""

    @patch('japanese_cli.cli.progress.get_progress')
    @patch('japanese_cli.cli.progress.update_progress_level')
    def test_set_target_level_success(self, mock_update, mock_get):
        """Test successfully setting target level."""
        # Mock existing progress
        mock_get.side_effect = [
            {  # First call - check exists
                "user_id": "default",
                "current_level": "n5",
                "target_level": "n5",
                "stats": '{}',
                "milestones": None,
                "streak_days": 0,
                "last_review_date": None,
                "created_at": "2024-01-01 00:00:00",
                "updated_at": "2024-01-01 00:00:00"
            },
            {  # Second call - show updated
                "user_id": "default",
                "current_level": "n5",
                "target_level": "n4",
                "stats": '{}',
                "milestones": None,
                "streak_days": 0,
                "last_review_date": None,
                "created_at": "2024-01-01 00:00:00",
                "updated_at": "2024-01-01 00:00:00"
            }
        ]
        mock_update.return_value = True

        result = runner.invoke(app, ["set-level", "n4"])

        assert result.exit_code == 0
        assert "updated target level to n4" in result.stdout.lower()
        mock_update.assert_called_once_with(target_level="n4")

    @patch('japanese_cli.cli.progress.get_progress')
    @patch('japanese_cli.cli.progress.update_progress_level')
    def test_set_current_level_success(self, mock_update, mock_get):
        """Test successfully setting current level."""
        mock_get.side_effect = [
            {
                "user_id": "default",
                "current_level": "n5",
                "target_level": "n4",
                "stats": '{}',
                "milestones": None,
                "streak_days": 0,
                "last_review_date": None,
                "created_at": "2024-01-01 00:00:00",
                "updated_at": "2024-01-01 00:00:00"
            },
            {
                "user_id": "default",
                "current_level": "n4",
                "target_level": "n4",
                "stats": '{}',
                "milestones": None,
                "streak_days": 0,
                "last_review_date": None,
                "created_at": "2024-01-01 00:00:00",
                "updated_at": "2024-01-01 00:00:00"
            }
        ]
        mock_update.return_value = True

        result = runner.invoke(app, ["set-level", "n4", "--current"])

        assert result.exit_code == 0
        assert "updated current level to n4" in result.stdout.lower()
        mock_update.assert_called_once_with(current_level="n4")

    def test_set_level_invalid_level(self):
        """Test setting invalid JLPT level."""
        result = runner.invoke(app, ["set-level", "n6"])

        assert result.exit_code == 1
        assert "invalid jlpt level" in result.stdout.lower()

    @patch('japanese_cli.cli.progress.get_progress')
    def test_set_level_not_initialized(self, mock_get):
        """Test setting level when progress not initialized."""
        mock_get.return_value = None

        result = runner.invoke(app, ["set-level", "n4"])

        assert result.exit_code == 1
        assert "not initialized" in result.stdout.lower()

    @patch('japanese_cli.cli.progress.get_progress')
    @patch('japanese_cli.cli.progress.update_progress_level')
    def test_set_level_update_failure(self, mock_update, mock_get):
        """Test failure during level update."""
        mock_get.return_value = {
            "user_id": "default",
            "current_level": "n5",
            "target_level": "n5",
            "stats": '{}',
            "milestones": None,
            "streak_days": 0,
            "last_review_date": None,
            "created_at": "2024-01-01 00:00:00",
            "updated_at": "2024-01-01 00:00:00"
        }
        mock_update.return_value = False

        result = runner.invoke(app, ["set-level", "n4"])

        assert result.exit_code == 1
        assert "failed" in result.stdout.lower()

    def test_set_level_case_insensitive(self):
        """Test that level argument is case-insensitive."""
        with patch('japanese_cli.cli.progress.get_progress') as mock_get:
            with patch('japanese_cli.cli.progress.update_progress_level') as mock_update:
                mock_get.side_effect = [
                    {"user_id": "default", "current_level": "n5", "target_level": "n5",
                     "stats": '{}', "milestones": None, "streak_days": 0,
                     "last_review_date": None, "created_at": "2024-01-01 00:00:00",
                     "updated_at": "2024-01-01 00:00:00"},
                    {"user_id": "default", "current_level": "n5", "target_level": "n4",
                     "stats": '{}', "milestones": None, "streak_days": 0,
                     "last_review_date": None, "created_at": "2024-01-01 00:00:00",
                     "updated_at": "2024-01-01 00:00:00"}
                ]
                mock_update.return_value = True

                result = runner.invoke(app, ["set-level", "N4"])

                assert result.exit_code == 0
                mock_update.assert_called_once_with(target_level="n4")


class TestProgressStatsCommand:
    """Tests for progress stats command."""

    @patch('japanese_cli.cli.progress.get_reviews_by_date_range')
    @patch('japanese_cli.cli.progress.calculate_retention_rate')
    @patch('japanese_cli.cli.progress.calculate_average_review_duration')
    @patch('japanese_cli.cli.progress.aggregate_daily_review_counts')
    @patch('japanese_cli.cli.progress.get_most_reviewed_items')
    @patch('japanese_cli.cli.progress.display_statistics')
    def test_stats_all_time(
        self, mock_display, mock_most_reviewed, mock_daily, mock_avg_duration,
        mock_retention, mock_reviews
    ):
        """Test displaying all-time statistics."""
        mock_reviews.return_value = [{"id": i} for i in range(100)]
        mock_retention.return_value = 85.5
        mock_avg_duration.return_value = 5.5
        mock_daily.return_value = [{"date": "2024-01-01", "count": 10}]
        mock_most_reviewed.return_value = []
        mock_display.return_value = MagicMock()

        result = runner.invoke(app, ["stats"])

        assert result.exit_code == 0
        mock_reviews.assert_called_once_with()
        mock_retention.assert_called_once_with()
        mock_display.assert_called_once()

    @patch('japanese_cli.cli.progress.get_reviews_by_date_range')
    @patch('japanese_cli.cli.progress.calculate_retention_rate')
    @patch('japanese_cli.cli.progress.calculate_average_review_duration')
    @patch('japanese_cli.cli.progress.aggregate_daily_review_counts')
    @patch('japanese_cli.cli.progress.get_most_reviewed_items')
    @patch('japanese_cli.cli.progress.display_statistics')
    def test_stats_last_7_days(
        self, mock_display, mock_most_reviewed, mock_daily, mock_avg_duration,
        mock_retention, mock_reviews
    ):
        """Test displaying 7-day statistics."""
        mock_reviews.return_value = [{"id": i} for i in range(50)]
        mock_retention.return_value = 80.0
        mock_avg_duration.return_value = 4.2
        mock_daily.return_value = []
        mock_most_reviewed.return_value = []
        mock_display.return_value = MagicMock()

        result = runner.invoke(app, ["stats", "--range", "7d"])

        assert result.exit_code == 0
        # Check that date-filtered functions were called
        assert mock_reviews.call_count == 1
        assert mock_retention.call_count == 1

    @patch('japanese_cli.cli.progress.get_reviews_by_date_range')
    @patch('japanese_cli.cli.progress.calculate_retention_rate')
    @patch('japanese_cli.cli.progress.calculate_average_review_duration')
    @patch('japanese_cli.cli.progress.aggregate_daily_review_counts')
    @patch('japanese_cli.cli.progress.get_most_reviewed_items')
    @patch('japanese_cli.cli.progress.display_statistics')
    def test_stats_last_30_days(
        self, mock_display, mock_most_reviewed, mock_daily, mock_avg_duration,
        mock_retention, mock_reviews
    ):
        """Test displaying 30-day statistics."""
        mock_reviews.return_value = []
        mock_retention.return_value = 0.0
        mock_avg_duration.return_value = 0.0
        mock_daily.return_value = []
        mock_most_reviewed.return_value = []
        mock_display.return_value = MagicMock()

        result = runner.invoke(app, ["stats", "--range", "30d"])

        assert result.exit_code == 0

    def test_stats_invalid_range(self):
        """Test stats with invalid date range."""
        result = runner.invoke(app, ["stats", "--range", "invalid"])

        assert result.exit_code == 1
        assert "invalid date range" in result.stdout.lower()

    @patch('japanese_cli.cli.progress.get_reviews_by_date_range')
    @patch('japanese_cli.cli.progress.calculate_retention_rate')
    @patch('japanese_cli.cli.progress.calculate_average_review_duration')
    @patch('japanese_cli.cli.progress.aggregate_daily_review_counts')
    @patch('japanese_cli.cli.progress.get_most_reviewed_items')
    @patch('japanese_cli.cli.progress.display_statistics')
    def test_stats_no_reviews(
        self, mock_display, mock_most_reviewed, mock_daily, mock_avg_duration,
        mock_retention, mock_reviews
    ):
        """Test stats display with no reviews."""
        mock_reviews.return_value = []
        mock_retention.return_value = 0.0
        mock_avg_duration.return_value = 0.0
        mock_daily.return_value = []
        mock_most_reviewed.return_value = []
        mock_display.return_value = MagicMock()

        result = runner.invoke(app, ["stats"])

        assert result.exit_code == 0
        assert "no reviews found" in result.stdout.lower()

    @patch('japanese_cli.cli.progress.get_reviews_by_date_range')
    def test_stats_database_error(self, mock_reviews):
        """Test error during statistics calculation."""
        mock_reviews.side_effect = Exception("Database error")

        result = runner.invoke(app, ["stats"])

        assert result.exit_code == 1
        assert "error" in result.stdout.lower()


class TestProgressCLIHelp:
    """Tests for progress command help."""

    def test_progress_help(self):
        """Test progress main help."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "progress" in result.stdout.lower()
        assert "show" in result.stdout.lower()
        assert "set-level" in result.stdout.lower()
        assert "stats" in result.stdout.lower()

    def test_progress_show_help(self):
        """Test progress show help."""
        result = runner.invoke(app, ["show", "--help"])

        assert result.exit_code == 0
        assert "show" in result.stdout.lower() or "display" in result.stdout.lower()

    def test_progress_set_level_help(self):
        """Test progress set-level help."""
        result = runner.invoke(app, ["set-level", "--help"])

        assert result.exit_code == 0
        assert "level" in result.stdout.lower()
        assert "current" in result.stdout.lower()

    def test_progress_stats_help(self):
        """Test progress stats help."""
        result = runner.invoke(app, ["stats", "--help"])

        assert result.exit_code == 0
        assert "stats" in result.stdout.lower() or "statistics" in result.stdout.lower()
        assert "range" in result.stdout.lower()


class TestProgressCLIEdgeCases:
    """Edge case tests for progress CLI."""

    def test_no_args_shows_help(self):
        """Test that no arguments shows help."""
        result = runner.invoke(app, [])

        # no_args_is_help=True means it should show usage
        assert result.exit_code in [0, 2]

    def test_invalid_command(self):
        """Test invalid progress subcommand."""
        result = runner.invoke(app, ["invalid-command"])

        assert result.exit_code != 0

    def test_set_level_missing_argument(self):
        """Test set-level without level argument."""
        result = runner.invoke(app, ["set-level"])

        assert result.exit_code != 0
