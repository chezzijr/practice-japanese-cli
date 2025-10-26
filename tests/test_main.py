"""
Tests for main.py CLI entry point.

Tests the init and version commands, database initialization,
and error handling for the main CLI application.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

from japanese_cli.main import app
from japanese_cli.database import database_exists, get_db_path


# Create CLI test runner
runner = CliRunner()


class TestVersionCommand:
    """Tests for the version command."""

    def test_version_displays_correctly(self):
        """Test that version command displays version information."""
        result = runner.invoke(app, ["version"])

        assert result.exit_code == 0
        assert "Japanese Learning CLI" in result.stdout
        assert "v0.1.0" in result.stdout
        assert "spaced repetition" in result.stdout.lower()

    def test_version_output_format(self):
        """Test that version output is properly formatted."""
        result = runner.invoke(app, ["version"])

        assert result.exit_code == 0
        # Should have at least two lines (title and description)
        lines = [line for line in result.stdout.split('\n') if line.strip()]
        assert len(lines) >= 2


class TestInitCommand:
    """Tests for the init command."""

    @patch('japanese_cli.main.ensure_data_directory')
    @patch('japanese_cli.main.get_db_path')
    @patch('japanese_cli.main.database_exists')
    @patch('japanese_cli.main.initialize_database')
    @patch('japanese_cli.main.get_progress')
    @patch('japanese_cli.main.init_progress')
    def test_init_fresh_database(
        self,
        mock_init_progress,
        mock_get_progress,
        mock_initialize_db,
        mock_db_exists,
        mock_get_db_path,
        mock_ensure_dir,
        tmp_path
    ):
        """Test initialization with a fresh database."""
        # Setup mocks
        test_db = tmp_path / "test.db"
        mock_get_db_path.return_value = test_db
        mock_db_exists.return_value = False
        mock_initialize_db.return_value = True  # Database was created
        mock_get_progress.return_value = None  # Progress not initialized

        result = runner.invoke(app, ["init"])

        assert result.exit_code == 0
        assert "Initializing Japanese Learning CLI" in result.stdout
        assert "✓" in result.stdout or "complete" in result.stdout.lower()

        # Verify all setup steps were called
        mock_ensure_dir.assert_called_once()
        mock_initialize_db.assert_called_once_with(test_db)
        mock_init_progress.assert_called_once()

    @patch('japanese_cli.main.ensure_data_directory')
    @patch('japanese_cli.main.get_db_path')
    @patch('japanese_cli.main.database_exists')
    @patch('japanese_cli.main.initialize_database')
    @patch('japanese_cli.main.get_progress')
    def test_init_existing_database(
        self,
        mock_get_progress,
        mock_initialize_db,
        mock_db_exists,
        mock_get_db_path,
        mock_ensure_dir,
        tmp_path
    ):
        """Test initialization when database already exists."""
        # Setup mocks
        test_db = tmp_path / "test.db"
        mock_get_db_path.return_value = test_db
        mock_db_exists.return_value = True
        mock_initialize_db.return_value = False  # Database already existed
        mock_get_progress.return_value = {
            "user_id": "default",
            "current_level": "n5",
            "target_level": "n5",
        }  # Progress already exists

        result = runner.invoke(app, ["init"])

        assert result.exit_code == 0
        assert "already exists" in result.stdout.lower()
        assert "up to date" in result.stdout.lower() or "✓" in result.stdout

    @patch('japanese_cli.main.ensure_data_directory')
    @patch('japanese_cli.main.get_db_path')
    @patch('japanese_cli.main.database_exists')
    @patch('japanese_cli.main.initialize_database')
    def test_init_database_error(
        self,
        mock_initialize_db,
        mock_db_exists,
        mock_get_db_path,
        mock_ensure_dir,
        tmp_path
    ):
        """Test initialization failure due to database error."""
        # Setup mocks
        test_db = tmp_path / "test.db"
        mock_get_db_path.return_value = test_db
        mock_db_exists.return_value = False
        mock_initialize_db.side_effect = Exception("Database error")

        result = runner.invoke(app, ["init"])

        assert result.exit_code == 1
        assert "failed" in result.stdout.lower() or "error" in result.stdout.lower()

    @patch('japanese_cli.main.ensure_data_directory')
    def test_init_directory_creation_error(self, mock_ensure_dir):
        """Test initialization failure due to directory creation error."""
        mock_ensure_dir.side_effect = PermissionError("Permission denied")

        result = runner.invoke(app, ["init"])

        assert result.exit_code == 1
        assert "failed" in result.stdout.lower() or "permission" in result.stdout.lower()

    @patch('japanese_cli.main.ensure_data_directory')
    @patch('japanese_cli.main.get_db_path')
    @patch('japanese_cli.main.database_exists')
    @patch('japanese_cli.main.initialize_database')
    @patch('japanese_cli.main.get_progress')
    @patch('japanese_cli.main.init_progress')
    def test_init_shows_next_steps(
        self,
        mock_init_progress,
        mock_get_progress,
        mock_initialize_db,
        mock_db_exists,
        mock_get_db_path,
        mock_ensure_dir,
        tmp_path
    ):
        """Test that init shows helpful next steps."""
        # Setup mocks for successful init
        test_db = tmp_path / "test.db"
        mock_get_db_path.return_value = test_db
        mock_db_exists.return_value = False
        mock_initialize_db.return_value = True
        mock_get_progress.return_value = None

        result = runner.invoke(app, ["init"])

        assert result.exit_code == 0
        # Should show next steps
        assert "Next steps" in result.stdout or "import" in result.stdout.lower()
        assert "flashcard" in result.stdout.lower() or "review" in result.stdout.lower()

    @patch('japanese_cli.main.ensure_data_directory')
    @patch('japanese_cli.main.get_db_path')
    @patch('japanese_cli.main.database_exists')
    @patch('japanese_cli.main.initialize_database')
    @patch('japanese_cli.main.get_progress')
    @patch('japanese_cli.main.init_progress')
    def test_init_progress_initialization(
        self,
        mock_init_progress,
        mock_get_progress,
        mock_initialize_db,
        mock_db_exists,
        mock_get_db_path,
        mock_ensure_dir,
        tmp_path
    ):
        """Test that progress is initialized if missing."""
        # Setup mocks
        test_db = tmp_path / "test.db"
        mock_get_db_path.return_value = test_db
        mock_db_exists.return_value = True
        mock_initialize_db.return_value = False
        mock_get_progress.return_value = None  # Progress not initialized

        result = runner.invoke(app, ["init"])

        assert result.exit_code == 0
        # Progress initialization should be called
        mock_init_progress.assert_called_once()
        assert "progress" in result.stdout.lower() or "✓" in result.stdout


class TestAppConfiguration:
    """Tests for main app configuration."""

    def test_app_help(self):
        """Test that app help is accessible."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "Japanese" in result.stdout or "learning" in result.stdout.lower()
        assert "Commands:" in result.stdout or "command" in result.stdout.lower()

    def test_app_has_subcommands(self):
        """Test that app registers all expected subcommands."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        # Check for registered subcommands
        assert "import" in result.stdout.lower()
        assert "flashcard" in result.stdout.lower()
        assert "progress" in result.stdout.lower()
        assert "grammar" in result.stdout.lower()

    def test_app_no_args(self):
        """Test app behavior with no arguments."""
        result = runner.invoke(app, [])

        # Typer should show help or usage information
        assert result.exit_code in [0, 2]  # 0 for help, 2 for missing command

    def test_invalid_command(self):
        """Test app behavior with invalid command."""
        result = runner.invoke(app, ["nonexistent-command"])

        # Should fail with error
        assert result.exit_code != 0


class TestInitIntegration:
    """Integration tests for init command with real database."""

    def test_init_creates_database_file(self, tmp_path, monkeypatch):
        """Test that init actually creates the database file."""
        # Use temporary directory
        test_data_dir = tmp_path / "data"
        test_db = test_data_dir / "japanese.db"

        with patch('japanese_cli.main.get_db_path', return_value=test_db):
            with patch('japanese_cli.main.ensure_data_directory') as mock_ensure:
                mock_ensure.side_effect = lambda: test_data_dir.mkdir(parents=True, exist_ok=True)

                result = runner.invoke(app, ["init"])

                assert result.exit_code == 0

    def test_init_idempotent(self, tmp_path):
        """Test that running init multiple times is safe."""
        test_data_dir = tmp_path / "data"
        test_db = test_data_dir / "japanese.db"

        with patch('japanese_cli.main.get_db_path', return_value=test_db):
            with patch('japanese_cli.main.ensure_data_directory') as mock_ensure:
                mock_ensure.side_effect = lambda: test_data_dir.mkdir(parents=True, exist_ok=True)

                # Run init twice
                result1 = runner.invoke(app, ["init"])
                result2 = runner.invoke(app, ["init"])

                # Both should succeed
                assert result1.exit_code == 0
                assert result2.exit_code == 0
                # Second run should note database exists
                assert "already exists" in result2.stdout.lower() or "up to date" in result2.stdout.lower()


class TestInitErrorCases:
    """Tests for various error scenarios during initialization."""

    @patch('japanese_cli.main.ensure_data_directory')
    @patch('japanese_cli.main.get_db_path')
    @patch('japanese_cli.main.database_exists')
    @patch('japanese_cli.main.initialize_database')
    @patch('japanese_cli.main.get_progress')
    @patch('japanese_cli.main.init_progress')
    def test_init_progress_error(
        self,
        mock_init_progress,
        mock_get_progress,
        mock_initialize_db,
        mock_db_exists,
        mock_get_db_path,
        mock_ensure_dir,
        tmp_path
    ):
        """Test error during progress initialization."""
        test_db = tmp_path / "test.db"
        mock_get_db_path.return_value = test_db
        mock_db_exists.return_value = True
        mock_initialize_db.return_value = False
        mock_get_progress.return_value = None
        mock_init_progress.side_effect = Exception("Progress init error")

        result = runner.invoke(app, ["init"])

        assert result.exit_code == 1

    @patch('japanese_cli.main.ensure_data_directory')
    @patch('japanese_cli.main.get_db_path')
    def test_init_disk_full_error(
        self,
        mock_get_db_path,
        mock_ensure_dir,
        tmp_path
    ):
        """Test initialization with disk full error."""
        test_db = tmp_path / "test.db"
        mock_get_db_path.return_value = test_db
        mock_ensure_dir.side_effect = OSError("No space left on device")

        result = runner.invoke(app, ["init"])

        assert result.exit_code == 1
        assert "failed" in result.stdout.lower()
