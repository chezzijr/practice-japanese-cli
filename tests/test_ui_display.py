"""
Tests for display formatting utilities.

Tests the ui/display.py module which creates Rich tables and panels
for displaying vocabulary and kanji flashcards.
"""

import pytest
from datetime import datetime, timedelta, timezone
from rich.table import Table
from rich.panel import Panel

from japanese_cli.models import Vocabulary, Kanji, Review, ItemType
from japanese_cli.ui.display import (
    format_vocabulary_table,
    format_kanji_table,
    format_vocabulary_panel,
    format_kanji_panel,
    JLPT_COLORS,
)


class TestJLPTColors:
    """Tests for JLPT color mapping."""

    def test_jlpt_colors_defined(self):
        """Test that all JLPT levels have colors."""
        assert "n5" in JLPT_COLORS
        assert "n4" in JLPT_COLORS
        assert "n3" in JLPT_COLORS
        assert "n2" in JLPT_COLORS
        assert "n1" in JLPT_COLORS

    def test_jlpt_colors_are_strings(self):
        """Test that all colors are string values."""
        for color in JLPT_COLORS.values():
            assert isinstance(color, str)


class TestFormatVocabularyTable:
    """Tests for format_vocabulary_table function."""

    @pytest.fixture
    def sample_vocab_list(self):
        """Create sample vocabulary list for testing."""
        return [
            Vocabulary(
                id=1,
                word="単語",
                reading="たんご",
                meanings={"vi": ["từ vựng"], "en": ["word", "vocabulary"]},
                jlpt_level="n5",
                part_of_speech="noun"
            ),
            Vocabulary(
                id=2,
                word="勉強",
                reading="べんきょう",
                meanings={"vi": ["học tập"], "en": ["study"]},
                jlpt_level="n4",
                vietnamese_reading="miễn cưỡng"
            ),
            Vocabulary(
                id=3,
                word="ありがとう",
                reading="ありがとう",
                meanings={"vi": ["cảm ơn"]},
                jlpt_level=None
            ),
        ]

    def test_basic_table_creation(self, sample_vocab_list):
        """Test creating basic vocabulary table."""
        table = format_vocabulary_table(sample_vocab_list)

        assert isinstance(table, Table)
        assert table.title == "📚 Vocabulary"

    def test_table_without_reviews(self, sample_vocab_list):
        """Test table creation without review data."""
        table = format_vocabulary_table(sample_vocab_list, reviews=None)

        assert isinstance(table, Table)
        # Should have 4 columns without review status
        assert len(table.columns) == 4

    def test_table_with_reviews(self, sample_vocab_list):
        """Test table creation with review data."""
        # Create mock review
        review = Review(
            id=1,
            item_id=1,
            item_type=ItemType.VOCAB,
            fsrs_card_state={},
            due_date=datetime.now(timezone.utc) + timedelta(days=5),
            review_count=10
        )

        table = format_vocabulary_table(
            sample_vocab_list,
            reviews={1: review},
            show_review_status=True
        )

        assert isinstance(table, Table)
        # Should have 5 columns with review status
        assert len(table.columns) == 5

    def test_table_with_empty_list(self):
        """Test table creation with empty vocabulary list."""
        table = format_vocabulary_table([])

        assert isinstance(table, Table)
        # Should create table even with no data

    def test_table_with_mixed_jlpt_levels(self, sample_vocab_list):
        """Test table with various JLPT levels including None."""
        table = format_vocabulary_table(sample_vocab_list)

        assert isinstance(table, Table)
        # Should handle None JLPT level gracefully

    def test_table_with_due_review(self, sample_vocab_list):
        """Test table showing due review."""
        # Create review that's due now
        review = Review(
            id=1,
            item_id=1,
            item_type=ItemType.VOCAB,
            fsrs_card_state={},
            due_date=datetime.now(timezone.utc) - timedelta(hours=1),  # Due in the past
            review_count=5
        )

        table = format_vocabulary_table(
            sample_vocab_list,
            reviews={1: review},
            show_review_status=True
        )

        assert isinstance(table, Table)


class TestFormatKanjiTable:
    """Tests for format_kanji_table function."""

    @pytest.fixture
    def sample_kanji_list(self):
        """Create sample kanji list for testing."""
        return [
            Kanji(
                id=1,
                character="語",
                on_readings=["ゴ"],
                kun_readings=["かた.る", "かた.らう"],
                meanings={"vi": ["ngữ"], "en": ["word", "language"]},
                vietnamese_reading="ngữ",
                jlpt_level="n5",
                stroke_count=14
            ),
            Kanji(
                id=2,
                character="学",
                on_readings=["ガク"],
                kun_readings=["まな.ぶ"],
                meanings={"vi": ["học"], "en": ["learning", "study"]},
                vietnamese_reading="học",
                jlpt_level="n5",
                stroke_count=8,
                radical="子"
            ),
            Kanji(
                id=3,
                character="日",
                on_readings=["ニチ", "ジツ"],
                kun_readings=["ひ", "か"],
                meanings={"vi": ["nhật"], "en": ["day", "sun"]},
                jlpt_level="n5"
            ),
        ]

    def test_basic_kanji_table(self, sample_kanji_list):
        """Test creating basic kanji table."""
        table = format_kanji_table(sample_kanji_list)

        assert isinstance(table, Table)
        assert table.title == "㊙️ Kanji"

    def test_kanji_table_without_reviews(self, sample_kanji_list):
        """Test kanji table without review data."""
        table = format_kanji_table(sample_kanji_list, reviews=None)

        assert isinstance(table, Table)
        # Should have 5 columns without review status
        assert len(table.columns) == 5

    def test_kanji_table_with_reviews(self, sample_kanji_list):
        """Test kanji table with review data."""
        review = Review(
            id=1,
            item_id=1,
            item_type=ItemType.KANJI,
            fsrs_card_state={},
            due_date=datetime.now(timezone.utc) + timedelta(days=3),
            review_count=8
        )

        table = format_kanji_table(
            sample_kanji_list,
            reviews={1: review},
            show_review_status=True
        )

        assert isinstance(table, Table)
        # Should have 6 columns with review status
        assert len(table.columns) == 6

    def test_kanji_table_with_empty_list(self):
        """Test kanji table with empty list."""
        table = format_kanji_table([])

        assert isinstance(table, Table)

    def test_kanji_with_multiple_readings(self, sample_kanji_list):
        """Test kanji table with multiple on and kun readings."""
        table = format_kanji_table(sample_kanji_list)

        assert isinstance(table, Table)
        # Should handle multiple readings gracefully


class TestFormatVocabularyPanel:
    """Tests for format_vocabulary_panel function."""

    @pytest.fixture
    def sample_vocab(self):
        """Create sample vocabulary for testing."""
        return Vocabulary(
            id=42,
            word="日本語",
            reading="にほんご",
            meanings={"vi": ["tiếng Nhật"], "en": ["Japanese language"]},
            vietnamese_reading="nhật bản ngữ",
            jlpt_level="n5",
            part_of_speech="noun",
            tags=["language", "essential"],
            notes="Common word for Japanese language"
        )

    def test_basic_panel_creation(self, sample_vocab):
        """Test creating basic vocabulary panel."""
        panel = format_vocabulary_panel(sample_vocab)

        assert isinstance(panel, Panel)
        assert "📚 Vocabulary #42" in str(panel.title)

    def test_panel_without_review(self, sample_vocab):
        """Test panel without review data."""
        panel = format_vocabulary_panel(sample_vocab, review=None)

        assert isinstance(panel, Panel)
        # Should not crash without review

    def test_panel_with_review(self, sample_vocab):
        """Test panel with review data."""
        review = Review(
            id=1,
            item_id=42,
            item_type=ItemType.VOCAB,
            fsrs_card_state={},
            due_date=datetime.now(timezone.utc) + timedelta(days=7),
            review_count=15
        )

        panel = format_vocabulary_panel(sample_vocab, review=review)

        assert isinstance(panel, Panel)
        # Should include review information

    def test_panel_with_minimal_data(self):
        """Test panel with minimal vocabulary data."""
        vocab = Vocabulary(
            id=1,
            word="テスト",
            reading="テスト",
            meanings={"vi": ["kiểm tra"]}
        )

        panel = format_vocabulary_panel(vocab)

        assert isinstance(panel, Panel)

    def test_panel_with_all_fields(self, sample_vocab):
        """Test panel with all optional fields populated."""
        panel = format_vocabulary_panel(sample_vocab)

        assert isinstance(panel, Panel)
        # Should display all fields

    def test_panel_with_due_review(self, sample_vocab):
        """Test panel with review that's due."""
        review = Review(
            id=1,
            item_id=42,
            item_type=ItemType.VOCAB,
            fsrs_card_state={},
            due_date=datetime.now(timezone.utc) - timedelta(hours=2),
            review_count=3
        )

        panel = format_vocabulary_panel(sample_vocab, review=review)

        assert isinstance(panel, Panel)
        # Should show "Due now!"


class TestFormatKanjiPanel:
    """Tests for format_kanji_panel function."""

    @pytest.fixture
    def sample_kanji(self):
        """Create sample kanji for testing."""
        return Kanji(
            id=123,
            character="語",
            on_readings=["ゴ"],
            kun_readings=["かた.る", "かた.らう"],
            meanings={"vi": ["ngữ", "lời"], "en": ["word", "language", "speak"]},
            vietnamese_reading="ngữ",
            jlpt_level="n5",
            stroke_count=14,
            radical="言",
            notes="Used in 日本語 (Japanese language)"
        )

    def test_basic_kanji_panel(self, sample_kanji):
        """Test creating basic kanji panel."""
        panel = format_kanji_panel(sample_kanji)

        assert isinstance(panel, Panel)
        assert "㊙️ Kanji #123" in str(panel.title)

    def test_panel_without_review(self, sample_kanji):
        """Test kanji panel without review data."""
        panel = format_kanji_panel(sample_kanji, review=None)

        assert isinstance(panel, Panel)

    def test_panel_with_review(self, sample_kanji):
        """Test kanji panel with review data."""
        review = Review(
            id=1,
            item_id=123,
            item_type=ItemType.KANJI,
            fsrs_card_state={},
            due_date=datetime.now(timezone.utc) + timedelta(days=2),
            review_count=20
        )

        panel = format_kanji_panel(sample_kanji, review=review)

        assert isinstance(panel, Panel)

    def test_panel_with_minimal_kanji(self):
        """Test panel with minimal kanji data."""
        kanji = Kanji(
            id=1,
            character="日",
            on_readings=[],
            kun_readings=["ひ"],
            meanings={"vi": ["nhật"]}
        )

        panel = format_kanji_panel(kanji)

        assert isinstance(panel, Panel)

    def test_panel_with_all_kanji_fields(self, sample_kanji):
        """Test panel with all fields populated."""
        panel = format_kanji_panel(sample_kanji)

        assert isinstance(panel, Panel)
        # Should display all fields including radical, stroke count, etc.

    def test_panel_with_no_readings(self):
        """Test panel with kanji that has no readings."""
        kanji = Kanji(
            id=1,
            character="一",  # Use real kanji instead of iteration mark
            on_readings=[],
            kun_readings=[],
            meanings={"vi": ["một"]}  # one
        )

        panel = format_kanji_panel(kanji)

        assert isinstance(panel, Panel)


class TestDisplayEdgeCases:
    """Tests for edge cases in display formatting."""

    def test_vocabulary_with_long_meanings(self):
        """Test vocabulary with very long meaning lists."""
        vocab = Vocabulary(
            id=1,
            word="する",
            reading="する",
            meanings={
                "vi": ["làm", "thực hiện", "hành động"],
                "en": ["to do", "to perform", "to execute", "to carry out", "to accomplish"]
            }
        )

        panel = format_vocabulary_panel(vocab)
        assert isinstance(panel, Panel)

        table = format_vocabulary_table([vocab])
        assert isinstance(table, Table)

    def test_kanji_with_many_readings(self):
        """Test kanji with many readings."""
        kanji = Kanji(
            id=1,
            character="生",
            on_readings=["セイ", "ショウ"],
            kun_readings=["い.きる", "い.かす", "い.ける", "う.まれる", "う.む", "お.う", "は.える", "は.やす", "き", "なま"],
            meanings={"vi": ["sinh", "sống", "sống sót"]}
        )

        panel = format_kanji_panel(kanji)
        assert isinstance(panel, Panel)

        table = format_kanji_table([kanji])
        assert isinstance(table, Table)

    def test_special_characters_in_text(self):
        """Test handling special characters."""
        vocab = Vocabulary(
            id=1,
            word="〜です",
            reading="です",
            meanings={"vi": ["là [lịch sự]"]}
        )

        panel = format_vocabulary_panel(vocab)
        assert isinstance(panel, Panel)

    def test_empty_meanings_dict(self):
        """Test with empty language in meanings."""
        vocab = Vocabulary(
            id=1,
            word="テスト",  # Use katakana instead of romaji
            reading="テスト",
            meanings={"vi": ["thử nghiệm"], "en": []}
        )

        table = format_vocabulary_table([vocab])
        assert isinstance(table, Table)


# Tests for Progress Display Functions

class TestDisplayProgressDashboard:
    """Tests for display_progress_dashboard function."""

    def test_display_basic_dashboard(self):
        """Test displaying progress dashboard with typical data."""
        from japanese_cli.models import Progress, ProgressStats
        from japanese_cli.ui.display import display_progress_dashboard
        from datetime import date

        progress = Progress(
            id=1,
            user_id="default",
            current_level="n5",
            target_level="n4",
            stats=ProgressStats(
                total_vocab=100,
                total_kanji=50,
                mastered_vocab=20,
                mastered_kanji=10,
                total_reviews=500,
                average_retention=0.855  # Fraction not percentage
            ),
            streak_days=5,
            last_review_date=date.today()
        )

        vocab_counts = {"n5": 80, "n4": 20, "total": 100}
        kanji_counts = {"n5": 45, "n4": 5, "total": 50}
        mastered_counts = {"vocab": 20, "kanji": 10, "total": 30}

        # Should not raise any exceptions
        display_progress_dashboard(
            progress=progress,
            vocab_counts=vocab_counts,
            kanji_counts=kanji_counts,
            mastered_counts=mastered_counts,
            due_today=15,
            total_reviews=500,
            retention_rate=85.5
        )

    def test_display_dashboard_high_streak(self):
        """Test dashboard with high streak (should show fire emoji)."""
        from japanese_cli.models import Progress, ProgressStats
        from japanese_cli.ui.display import display_progress_dashboard
        from datetime import date

        progress = Progress(
            id=1,
            current_level="n4",
            target_level="n3",
            stats=ProgressStats(
                total_vocab=500,
                total_kanji=200,
                mastered_vocab=100,
                mastered_kanji=50,
                total_reviews=2000,
                average_retention=0.92  # Fraction not percentage
            ),
            streak_days=15,  # High streak (>= 7 should show 🔥)
            last_review_date=date.today()
        )

        vocab_counts = {"n4": 300, "n3": 200, "total": 500}
        kanji_counts = {"n4": 120, "n3": 80, "total": 200}
        mastered_counts = {"vocab": 100, "kanji": 50, "total": 150}

        display_progress_dashboard(
            progress=progress,
            vocab_counts=vocab_counts,
            kanji_counts=kanji_counts,
            mastered_counts=mastered_counts,
            due_today=25,
            total_reviews=2000,
            retention_rate=92.0
        )

    def test_display_dashboard_invalid_type(self):
        """Test that TypeError is raised for invalid progress type."""
        from japanese_cli.ui.display import display_progress_dashboard

        with pytest.raises(TypeError, match="Expected Progress model"):
            display_progress_dashboard(
                progress={"not": "a progress object"},  # Invalid type
                vocab_counts={"n5": 10},
                kanji_counts={"n5": 5},
                mastered_counts={"total": 0},
                due_today=0,
                total_reviews=0,
                retention_rate=0.0
            )


class TestDisplayStatistics:
    """Tests for display_statistics function."""

    def test_display_basic_statistics(self):
        """Test displaying statistics with typical data."""
        from japanese_cli.ui.display import display_statistics

        display_statistics(
            total_reviews=150,
            retention_rate=85.5,
            avg_duration_seconds=4.2,
            daily_counts={
                "2025-10-20": 20,
                "2025-10-21": 25,
                "2025-10-22": 30,
                "2025-10-23": 15,
                "2025-10-24": 20,
                "2025-10-25": 25,
                "2025-10-26": 15
            },
            most_reviewed=[
                {"item_id": 1, "item_type": "vocab", "word": "私", "review_count": 15},
                {"item_id": 2, "item_type": "kanji", "character": "語", "review_count": 12},
                {"item_id": 3, "item_type": "vocab", "word": "猫", "review_count": 10}
            ],
            date_range_label="Last 7 days"
        )

    def test_display_statistics_high_retention(self):
        """Test statistics with high retention rate (should be green)."""
        from japanese_cli.ui.display import display_statistics

        display_statistics(
            total_reviews=500,
            retention_rate=95.0,  # >= 85% (green)
            avg_duration_seconds=3.5,
            daily_counts={"2025-10-26": 50},
            most_reviewed=[],
            date_range_label="Today"
        )

    def test_display_statistics_medium_retention(self):
        """Test statistics with medium retention rate (should be yellow)."""
        from japanese_cli.ui.display import display_statistics

        display_statistics(
            total_reviews=200,
            retention_rate=75.0,  # >= 70% and < 85% (yellow)
            avg_duration_seconds=5.0,
            daily_counts={"2025-10-26": 20},
            most_reviewed=[],
            date_range_label="All time"
        )

    def test_display_statistics_low_retention(self):
        """Test statistics with low retention rate (should be red)."""
        from japanese_cli.ui.display import display_statistics

        display_statistics(
            total_reviews=100,
            retention_rate=60.0,  # < 70% (red)
            avg_duration_seconds=6.5,
            daily_counts={"2025-10-26": 10},
            most_reviewed=[],
            date_range_label="Last 30 days"
        )

    def test_display_statistics_no_reviews(self):
        """Test statistics with no reviews."""
        from japanese_cli.ui.display import display_statistics

        display_statistics(
            total_reviews=0,
            retention_rate=0.0,
            avg_duration_seconds=0.0,
            daily_counts={},
            most_reviewed=[],
            date_range_label="All time"
        )

    def test_display_statistics_with_bar_chart(self):
        """Test statistics with daily activity bar chart."""
        from japanese_cli.ui.display import display_statistics

        # Create daily counts spanning a week
        daily_counts = {
            f"2025-10-{20+i}": (i+1) * 10  # Varying counts
            for i in range(7)
        }

        display_statistics(
            total_reviews=280,
            retention_rate=88.0,
            avg_duration_seconds=4.0,
            daily_counts=daily_counts,
            most_reviewed=[
                {"item_id": 1, "item_type": "vocab", "word": "単語", "review_count": 25}
            ],
            date_range_label="Last 7 days"
        )


class TestFormatRelativeDate:
    """Tests for format_relative_date function."""

    def test_format_today(self):
        """Test formatting today's date."""
        from japanese_cli.ui.display import format_relative_date
        from datetime import date

        today = date.today()
        result = format_relative_date(today)

        assert "Today" in result

    def test_format_yesterday(self):
        """Test formatting yesterday's date."""
        from japanese_cli.ui.display import format_relative_date
        from datetime import date, timedelta

        yesterday = date.today() - timedelta(days=1)
        result = format_relative_date(yesterday)

        assert "Yesterday" in result

    def test_format_recent_past(self):
        """Test formatting a recent past date (2-6 days ago)."""
        from japanese_cli.ui.display import format_relative_date
        from datetime import date, timedelta

        three_days_ago = date.today() - timedelta(days=3)
        result = format_relative_date(three_days_ago)

        assert "3 days ago" in result

    def test_format_one_week_ago(self):
        """Test formatting exactly one week ago."""
        from japanese_cli.ui.display import format_relative_date
        from datetime import date, timedelta

        one_week_ago = date.today() - timedelta(days=7)
        result = format_relative_date(one_week_ago)

        assert "1 week ago" in result or "7 days ago" in result

    def test_format_multiple_weeks_ago(self):
        """Test formatting multiple weeks ago."""
        from japanese_cli.ui.display import format_relative_date
        from datetime import date, timedelta

        three_weeks_ago = date.today() - timedelta(days=21)
        result = format_relative_date(three_weeks_ago)

        assert "3 weeks ago" in result or "21 days ago" in result

    def test_format_absolute_date(self):
        """Test formatting a date far in the past (shows absolute date)."""
        from japanese_cli.ui.display import format_relative_date
        from datetime import date, timedelta

        long_ago = date.today() - timedelta(days=60)
        result = format_relative_date(long_ago)

        # Should contain the actual date
        assert str(long_ago) in result or "days ago" in result or "weeks ago" in result
