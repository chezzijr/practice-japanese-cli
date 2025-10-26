"""
Comprehensive tests for the statistics module (srs/statistics.py).

Tests all statistical calculation functions including counts, retention rates,
mastery tracking, and time-based analytics.
"""

import pytest
from datetime import date, datetime, timedelta, timezone
from fsrs import Card, Scheduler, Rating

from src.japanese_cli.database import (
    add_vocabulary,
    add_kanji,
)
from src.japanese_cli.srs import ReviewScheduler, MCQReviewScheduler
from src.japanese_cli.srs.statistics import (
    MASTERY_STABILITY_THRESHOLD,
    calculate_vocab_counts_by_level,
    calculate_kanji_counts_by_level,
    calculate_mastered_items,
    calculate_retention_rate,
    get_most_reviewed_items,
    get_reviews_by_date_range,
    aggregate_daily_review_counts,
    calculate_average_review_duration,
    get_mcq_accuracy_rate,
    get_mcq_stats_by_type,
    get_mcq_option_distribution,
)


# Fixtures

@pytest.fixture
def db_with_mixed_vocab(clean_db):
    """Database with vocabulary across multiple JLPT levels."""
    vocab_data = [
        {"word": "私", "reading": "わたし", "meanings": {"vi": ["tôi"], "en": ["I"]}, "jlpt_level": "n5"},
        {"word": "猫", "reading": "ねこ", "meanings": {"vi": ["mèo"], "en": ["cat"]}, "jlpt_level": "n5"},
        {"word": "食べる", "reading": "たべる", "meanings": {"vi": ["ăn"], "en": ["eat"]}, "jlpt_level": "n5"},
        {"word": "便利", "reading": "べんり", "meanings": {"vi": ["tiện lợi"], "en": ["convenient"]}, "jlpt_level": "n4"},
        {"word": "会議", "reading": "かいぎ", "meanings": {"vi": ["hội nghị"], "en": ["meeting"]}, "jlpt_level": "n4"},
        {"word": "経済", "reading": "けいざい", "meanings": {"vi": ["kinh tế"], "en": ["economy"]}, "jlpt_level": "n3"},
        {"word": "未定", "reading": "みてい", "meanings": {"vi": ["chưa quyết"], "en": ["undecided"]}, "jlpt_level": None},
    ]

    vocab_ids = []
    for vocab in vocab_data:
        vocab_id = add_vocabulary(**vocab, db_path=clean_db)
        vocab_ids.append(vocab_id)

    return clean_db, vocab_ids


@pytest.fixture
def db_with_mixed_kanji(clean_db):
    """Database with kanji across multiple JLPT levels."""
    kanji_data = [
        {"character": "私", "on_readings": ["シ"], "kun_readings": ["わたし"],
         "meanings": {"vi": ["tư"], "en": ["I", "private"]}, "jlpt_level": "n5", "stroke_count": 7},
        {"character": "猫", "on_readings": ["ビョウ"], "kun_readings": ["ねこ"],
         "meanings": {"vi": ["miêu"], "en": ["cat"]}, "jlpt_level": "n5", "stroke_count": 11},
        {"character": "食", "on_readings": ["ショク"], "kun_readings": ["た.べる"],
         "meanings": {"vi": ["thực"], "en": ["eat", "food"]}, "jlpt_level": "n5", "stroke_count": 9},
        {"character": "便", "on_readings": ["ベン"], "kun_readings": ["たよ.り"],
         "meanings": {"vi": ["tiện"], "en": ["convenient"]}, "jlpt_level": "n4", "stroke_count": 9},
        {"character": "経", "on_readings": ["ケイ"], "kun_readings": ["へ.る"],
         "meanings": {"vi": ["kinh"], "en": ["pass", "sutra"]}, "jlpt_level": "n3", "stroke_count": 11},
    ]

    kanji_ids = []
    for kanji in kanji_data:
        kanji_id = add_kanji(**kanji, db_path=clean_db)
        kanji_ids.append(kanji_id)

    return clean_db, kanji_ids


@pytest.fixture
def db_with_reviews_and_history(clean_db):
    """Database with reviews and review history spanning multiple days."""
    # Add mixed vocabulary
    vocab_data = [
        {"word": "私", "reading": "わたし", "meanings": {"vi": ["tôi"], "en": ["I"]}, "jlpt_level": "n5"},
        {"word": "猫", "reading": "ねこ", "meanings": {"vi": ["mèo"], "en": ["cat"]}, "jlpt_level": "n5"},
        {"word": "食べる", "reading": "たべる", "meanings": {"vi": ["ăn"], "en": ["eat"]}, "jlpt_level": "n5"},
        {"word": "便利", "reading": "べんり", "meanings": {"vi": ["tiện lợi"], "en": ["convenient"]}, "jlpt_level": "n4"},
        {"word": "会議", "reading": "かいぎ", "meanings": {"vi": ["hội nghị"], "en": ["meeting"]}, "jlpt_level": "n4"},
    ]

    vocab_ids = []
    for vocab in vocab_data:
        vocab_id = add_vocabulary(**vocab, db_path=clean_db)
        vocab_ids.append(vocab_id)

    # Add mixed kanji
    kanji_data = [
        {"character": "私", "on_readings": ["シ"], "kun_readings": ["わたし"],
         "meanings": {"vi": ["tư"], "en": ["I", "private"]}, "jlpt_level": "n5", "stroke_count": 7},
        {"character": "猫", "on_readings": ["ビョウ"], "kun_readings": ["ねこ"],
         "meanings": {"vi": ["miêu"], "en": ["cat"]}, "jlpt_level": "n5", "stroke_count": 11},
        {"character": "食", "on_readings": ["ショク"], "kun_readings": ["た.べる"],
         "meanings": {"vi": ["thực"], "en": ["eat", "food"]}, "jlpt_level": "n5", "stroke_count": 9},
    ]

    kanji_ids = []
    for kanji in kanji_data:
        kanji_id = add_kanji(**kanji, db_path=clean_db)
        kanji_ids.append(kanji_id)

    # Create reviews with varying stability levels and review history
    scheduler = ReviewScheduler(db_path=clean_db)

    # Vocab reviews
    # vocab_ids[0] - high stability (mastered)
    review_id_0 = scheduler.create_new_review(vocab_ids[0], 'vocab')
    # Simulate multiple successful reviews to boost stability
    for _ in range(5):
        scheduler.process_review(review_id_0, rating=3, duration_ms=3000)

    # vocab_ids[1] - medium stability
    review_id_1 = scheduler.create_new_review(vocab_ids[1], 'vocab')
    for _ in range(2):
        scheduler.process_review(review_id_1, rating=3, duration_ms=4000)

    # vocab_ids[2] - low stability (just started)
    review_id_2 = scheduler.create_new_review(vocab_ids[2], 'vocab')
    scheduler.process_review(review_id_2, rating=2, duration_ms=5000)

    # Kanji reviews
    # kanji_ids[0] - high stability (mastered)
    review_id_k0 = scheduler.create_new_review(kanji_ids[0], 'kanji')
    for _ in range(6):
        scheduler.process_review(review_id_k0, rating=4, duration_ms=2000)

    # kanji_ids[1] - medium stability
    review_id_k1 = scheduler.create_new_review(kanji_ids[1], 'kanji')
    for _ in range(3):
        scheduler.process_review(review_id_k1, rating=3, duration_ms=3500)

    return clean_db, vocab_ids, kanji_ids, [review_id_0, review_id_1, review_id_2, review_id_k0, review_id_k1]


# Tests for calculate_vocab_counts_by_level

class TestCalculateVocabCountsByLevel:
    """Tests for calculate_vocab_counts_by_level function."""

    def test_empty_database(self, clean_db):
        """Test with empty database returns all zeros."""
        counts = calculate_vocab_counts_by_level(db_path=clean_db)

        assert counts == {"n5": 0, "n4": 0, "n3": 0, "n2": 0, "n1": 0, "total": 0}

    def test_all_levels(self, db_with_mixed_vocab):
        """Test counting vocabulary across all JLPT levels."""
        db_path, vocab_ids = db_with_mixed_vocab
        counts = calculate_vocab_counts_by_level(db_path=db_path)

        assert counts["n5"] == 3  # 私, 猫, 食べる
        assert counts["n4"] == 2  # 便利, 会議
        assert counts["n3"] == 1  # 経済
        assert counts["n2"] == 0
        assert counts["n1"] == 0
        assert counts["total"] == 7  # Including NULL level item

    def test_specific_level_n5(self, db_with_mixed_vocab):
        """Test counting only N5 vocabulary."""
        db_path, vocab_ids = db_with_mixed_vocab
        counts = calculate_vocab_counts_by_level(jlpt_level="n5", db_path=db_path)

        assert counts == {"n5": 3}

    def test_specific_level_n4(self, db_with_mixed_vocab):
        """Test counting only N4 vocabulary."""
        db_path, vocab_ids = db_with_mixed_vocab
        counts = calculate_vocab_counts_by_level(jlpt_level="n4", db_path=db_path)

        assert counts == {"n4": 2}

    def test_specific_level_empty(self, db_with_mixed_vocab):
        """Test counting level with no items."""
        db_path, vocab_ids = db_with_mixed_vocab
        counts = calculate_vocab_counts_by_level(jlpt_level="n2", db_path=db_path)

        assert counts == {"n2": 0}


# Tests for calculate_kanji_counts_by_level

class TestCalculateKanjiCountsByLevel:
    """Tests for calculate_kanji_counts_by_level function."""

    def test_empty_database(self, clean_db):
        """Test with empty database returns all zeros."""
        counts = calculate_kanji_counts_by_level(db_path=clean_db)

        assert counts == {"n5": 0, "n4": 0, "n3": 0, "n2": 0, "n1": 0, "total": 0}

    def test_all_levels(self, db_with_mixed_kanji):
        """Test counting kanji across all JLPT levels."""
        db_path, kanji_ids = db_with_mixed_kanji
        counts = calculate_kanji_counts_by_level(db_path=db_path)

        assert counts["n5"] == 3  # 私, 猫, 食
        assert counts["n4"] == 1  # 便
        assert counts["n3"] == 1  # 経
        assert counts["n2"] == 0
        assert counts["n1"] == 0
        assert counts["total"] == 5

    def test_specific_level_n5(self, db_with_mixed_kanji):
        """Test counting only N5 kanji."""
        db_path, kanji_ids = db_with_mixed_kanji
        counts = calculate_kanji_counts_by_level(jlpt_level="n5", db_path=db_path)

        assert counts == {"n5": 3}

    def test_specific_level_empty(self, db_with_mixed_kanji):
        """Test counting level with no items."""
        db_path, kanji_ids = db_with_mixed_kanji
        counts = calculate_kanji_counts_by_level(jlpt_level="n1", db_path=db_path)

        assert counts == {"n1": 0}


# Tests for calculate_mastered_items

class TestCalculateMasteredItems:
    """Tests for calculate_mastered_items function."""

    def test_empty_database(self, clean_db):
        """Test with no reviews returns all zeros."""
        mastered = calculate_mastered_items(db_path=clean_db)

        assert mastered == {"vocab": 0, "kanji": 0, "total": 0}

    def test_mastered_items_both_types(self, db_with_reviews_and_history):
        """Test counting mastered items for both vocab and kanji."""
        db_path, vocab_ids, kanji_ids, review_ids = db_with_reviews_and_history
        mastered = calculate_mastered_items(db_path=db_path)

        # After multiple Good/Easy reviews, some items should reach stability >= 21
        # This depends on FSRS algorithm, but we're testing the query works
        assert isinstance(mastered["vocab"], int)
        assert isinstance(mastered["kanji"], int)
        assert isinstance(mastered["total"], int)
        assert mastered["total"] == mastered["vocab"] + mastered["kanji"]

    def test_filter_by_vocab_only(self, db_with_reviews_and_history):
        """Test filtering to only vocabulary items."""
        db_path, vocab_ids, kanji_ids, review_ids = db_with_reviews_and_history
        mastered = calculate_mastered_items(item_type="vocab", db_path=db_path)

        assert "vocab" in mastered
        assert "kanji" in mastered
        assert mastered["kanji"] == 0  # Should be 0 when filtering vocab only
        assert mastered["total"] == mastered["vocab"]

    def test_filter_by_kanji_only(self, db_with_reviews_and_history):
        """Test filtering to only kanji items."""
        db_path, vocab_ids, kanji_ids, review_ids = db_with_reviews_and_history
        mastered = calculate_mastered_items(item_type="kanji", db_path=db_path)

        assert "vocab" in mastered
        assert "kanji" in mastered
        assert mastered["vocab"] == 0  # Should be 0 when filtering kanji only
        assert mastered["total"] == mastered["kanji"]

    def test_mastery_threshold_constant(self):
        """Test that the mastery threshold is set correctly."""
        assert MASTERY_STABILITY_THRESHOLD == 21.0

    def test_filter_by_vocab_and_jlpt_level(self, db_with_reviews_and_history):
        """Test filtering by both vocab type and JLPT level."""
        db_path, vocab_ids, kanji_ids, review_ids = db_with_reviews_and_history

        # Filter for N5 vocabulary only
        mastered = calculate_mastered_items(jlpt_level="n5", item_type="vocab", db_path=db_path)

        assert "vocab" in mastered
        assert "kanji" in mastered
        assert mastered["kanji"] == 0  # No kanji when filtering vocab
        assert mastered["total"] == mastered["vocab"]

    def test_filter_by_kanji_and_jlpt_level(self, db_with_reviews_and_history):
        """Test filtering by both kanji type and JLPT level."""
        db_path, vocab_ids, kanji_ids, review_ids = db_with_reviews_and_history

        # Filter for N5 kanji only
        mastered = calculate_mastered_items(jlpt_level="n5", item_type="kanji", db_path=db_path)

        assert "vocab" in mastered
        assert "kanji" in mastered
        assert mastered["vocab"] == 0  # No vocab when filtering kanji
        assert mastered["total"] == mastered["kanji"]


# Tests for calculate_retention_rate

class TestCalculateRetentionRate:
    """Tests for calculate_retention_rate function."""

    def test_empty_database(self, clean_db):
        """Test with no review history returns 0.0."""
        rate = calculate_retention_rate(db_path=clean_db)

        assert rate == 0.0

    def test_perfect_retention(self, db_with_reviews_and_history):
        """Test retention rate calculation with all Good/Easy ratings."""
        db_path, vocab_ids, kanji_ids, review_ids = db_with_reviews_and_history

        # We created reviews with ratings 2, 3, and 4
        # So retention should be > 0 but < 100
        rate = calculate_retention_rate(db_path=db_path)

        assert 0.0 <= rate <= 100.0
        assert isinstance(rate, float)

    def test_retention_with_date_range(self, db_with_reviews_and_history):
        """Test retention rate with date filtering."""
        db_path, vocab_ids, kanji_ids, review_ids = db_with_reviews_and_history

        # Test with today's date range
        today = date.today()
        rate = calculate_retention_rate(
            start_date=today,
            end_date=today,
            db_path=db_path
        )

        assert 0.0 <= rate <= 100.0

    def test_retention_with_start_date_only(self, db_with_reviews_and_history):
        """Test retention rate with only start date."""
        db_path, vocab_ids, kanji_ids, review_ids = db_with_reviews_and_history

        yesterday = date.today() - timedelta(days=1)
        rate = calculate_retention_rate(start_date=yesterday, db_path=db_path)

        assert 0.0 <= rate <= 100.0


# Tests for get_most_reviewed_items

class TestGetMostReviewedItems:
    """Tests for get_most_reviewed_items function."""

    def test_empty_database(self, clean_db):
        """Test with no reviews returns empty list."""
        items = get_most_reviewed_items(db_path=clean_db)

        assert items == []

    def test_get_top_items_both_types(self, db_with_reviews_and_history):
        """Test getting most reviewed items from both vocab and kanji."""
        db_path, vocab_ids, kanji_ids, review_ids = db_with_reviews_and_history

        items = get_most_reviewed_items(limit=10, db_path=db_path)

        assert isinstance(items, list)
        assert len(items) > 0

        # Check structure of returned items
        for item in items:
            assert "item_id" in item
            assert "item_type" in item
            assert "review_count" in item
            assert item["item_type"] in ["vocab", "kanji"]

            # Check for word or character field
            if item["item_type"] == "vocab":
                assert "word" in item
            else:
                assert "character" in item

    def test_filter_vocab_only(self, db_with_reviews_and_history):
        """Test filtering to only vocabulary items."""
        db_path, vocab_ids, kanji_ids, review_ids = db_with_reviews_and_history

        items = get_most_reviewed_items(limit=5, item_type="vocab", db_path=db_path)

        assert isinstance(items, list)
        for item in items:
            assert item["item_type"] == "vocab"
            assert "word" in item

    def test_filter_kanji_only(self, db_with_reviews_and_history):
        """Test filtering to only kanji items."""
        db_path, vocab_ids, kanji_ids, review_ids = db_with_reviews_and_history

        items = get_most_reviewed_items(limit=5, item_type="kanji", db_path=db_path)

        assert isinstance(items, list)
        for item in items:
            assert item["item_type"] == "kanji"
            assert "character" in item

    def test_limit_respected(self, db_with_reviews_and_history):
        """Test that limit parameter is respected."""
        db_path, vocab_ids, kanji_ids, review_ids = db_with_reviews_and_history

        items = get_most_reviewed_items(limit=2, db_path=db_path)

        assert len(items) <= 2

    def test_sorted_by_review_count(self, db_with_reviews_and_history):
        """Test that results are sorted by review_count descending."""
        db_path, vocab_ids, kanji_ids, review_ids = db_with_reviews_and_history

        items = get_most_reviewed_items(limit=5, db_path=db_path)

        if len(items) > 1:
            # Check that items are sorted in descending order
            for i in range(len(items) - 1):
                assert items[i]["review_count"] >= items[i + 1]["review_count"]


# Tests for get_reviews_by_date_range

class TestGetReviewsByDateRange:
    """Tests for get_reviews_by_date_range function."""

    def test_empty_database(self, clean_db):
        """Test with no review history returns empty list."""
        reviews = get_reviews_by_date_range(db_path=clean_db)

        assert reviews == []

    def test_get_all_reviews(self, db_with_reviews_and_history):
        """Test getting all reviews without date filtering."""
        db_path, vocab_ids, kanji_ids, review_ids = db_with_reviews_and_history

        reviews = get_reviews_by_date_range(db_path=db_path)

        assert isinstance(reviews, list)
        assert len(reviews) > 0

        # Check structure
        for review in reviews:
            assert "id" in review
            assert "review_id" in review
            assert "rating" in review
            assert "reviewed_at" in review

    def test_filter_by_date_range(self, db_with_reviews_and_history):
        """Test filtering by specific date range."""
        db_path, vocab_ids, kanji_ids, review_ids = db_with_reviews_and_history

        today = date.today()
        reviews = get_reviews_by_date_range(
            start_date=today,
            end_date=today,
            db_path=db_path
        )

        assert isinstance(reviews, list)
        # All reviews should be from today
        for review in reviews:
            review_date = datetime.fromisoformat(review["reviewed_at"].replace('Z', '+00:00')).date()
            assert review_date == today

    def test_filter_by_start_date_only(self, db_with_reviews_and_history):
        """Test filtering with only start date."""
        db_path, vocab_ids, kanji_ids, review_ids = db_with_reviews_and_history

        yesterday = date.today() - timedelta(days=1)
        reviews = get_reviews_by_date_range(start_date=yesterday, db_path=db_path)

        assert isinstance(reviews, list)

    def test_sorted_by_date_descending(self, db_with_reviews_and_history):
        """Test that reviews are sorted by date descending (newest first)."""
        db_path, vocab_ids, kanji_ids, review_ids = db_with_reviews_and_history

        reviews = get_reviews_by_date_range(db_path=db_path)

        if len(reviews) > 1:
            # Check descending order
            for i in range(len(reviews) - 1):
                time1 = datetime.fromisoformat(reviews[i]["reviewed_at"].replace('Z', '+00:00'))
                time2 = datetime.fromisoformat(reviews[i + 1]["reviewed_at"].replace('Z', '+00:00'))
                assert time1 >= time2


# Tests for aggregate_daily_review_counts

class TestAggregateDailyReviewCounts:
    """Tests for aggregate_daily_review_counts function."""

    def test_empty_database(self, clean_db):
        """Test with no reviews returns empty dict."""
        daily_counts = aggregate_daily_review_counts(db_path=clean_db)

        assert daily_counts == {}

    def test_aggregate_without_date_range(self, db_with_reviews_and_history):
        """Test aggregating all reviews by date."""
        db_path, vocab_ids, kanji_ids, review_ids = db_with_reviews_and_history

        daily_counts = aggregate_daily_review_counts(db_path=db_path)

        assert isinstance(daily_counts, dict)
        # Today should have some reviews
        today_str = date.today().isoformat()
        assert today_str in daily_counts
        assert daily_counts[today_str] > 0

    def test_aggregate_with_date_range(self, db_with_reviews_and_history):
        """Test aggregating with specific date range."""
        db_path, vocab_ids, kanji_ids, review_ids = db_with_reviews_and_history

        today = date.today()
        yesterday = today - timedelta(days=1)

        daily_counts = aggregate_daily_review_counts(
            start_date=yesterday,
            end_date=today,
            db_path=db_path
        )

        assert isinstance(daily_counts, dict)
        # Should have entries for both dates, even if count is 0
        assert yesterday.isoformat() in daily_counts
        assert today.isoformat() in daily_counts

    def test_fills_missing_dates_with_zero(self, db_with_reviews_and_history):
        """Test that missing dates in range are filled with 0."""
        db_path, vocab_ids, kanji_ids, review_ids = db_with_reviews_and_history

        # Use a date range that includes a day with no reviews
        start = date.today() - timedelta(days=7)
        end = date.today()

        daily_counts = aggregate_daily_review_counts(
            start_date=start,
            end_date=end,
            db_path=db_path
        )

        # Should have 8 entries (7 days ago to today inclusive)
        assert len(daily_counts) == 8

        # All dates in range should be present
        current = start
        while current <= end:
            assert current.isoformat() in daily_counts
            current += timedelta(days=1)

    def test_filter_by_start_date_only(self, db_with_reviews_and_history):
        """Test aggregating with only start date."""
        db_path, vocab_ids, kanji_ids, review_ids = db_with_reviews_and_history

        yesterday = date.today() - timedelta(days=1)
        daily_counts = aggregate_daily_review_counts(start_date=yesterday, db_path=db_path)

        assert isinstance(daily_counts, dict)
        # Should have today's date
        assert date.today().isoformat() in daily_counts


# Tests for calculate_average_review_duration

class TestCalculateAverageReviewDuration:
    """Tests for calculate_average_review_duration function."""

    def test_empty_database(self, clean_db):
        """Test with no reviews returns 0.0."""
        avg_duration = calculate_average_review_duration(db_path=clean_db)

        assert avg_duration == 0.0

    def test_average_duration(self, db_with_reviews_and_history):
        """Test calculating average duration from reviews."""
        db_path, vocab_ids, kanji_ids, review_ids = db_with_reviews_and_history

        avg_duration = calculate_average_review_duration(db_path=db_path)

        assert isinstance(avg_duration, float)
        assert avg_duration > 0.0  # We created reviews with durations
        # Duration should be in reasonable range (seconds)
        assert 0.0 < avg_duration < 60.0  # Less than 1 minute per card

    def test_duration_conversion_to_seconds(self, db_with_reviews_and_history):
        """Test that duration is converted from milliseconds to seconds."""
        db_path, vocab_ids, kanji_ids, review_ids = db_with_reviews_and_history

        # We created reviews with durations in milliseconds (e.g., 3000ms = 3s)
        avg_duration = calculate_average_review_duration(db_path=db_path)

        # Average of 2000ms, 3000ms, 3500ms, 4000ms, 5000ms = 3500ms = 3.5s
        assert 2.0 <= avg_duration <= 5.0  # Should be in seconds, not milliseconds

    def test_average_with_date_range(self, db_with_reviews_and_history):
        """Test average duration with date filtering."""
        db_path, vocab_ids, kanji_ids, review_ids = db_with_reviews_and_history

        today = date.today()
        avg_duration = calculate_average_review_duration(
            start_date=today,
            end_date=today,
            db_path=db_path
        )

        assert isinstance(avg_duration, float)
        assert avg_duration >= 0.0

    def test_average_with_start_date_only(self, db_with_reviews_and_history):
        """Test average duration with only start date."""
        db_path, vocab_ids, kanji_ids, review_ids = db_with_reviews_and_history

        yesterday = date.today() - timedelta(days=1)
        avg_duration = calculate_average_review_duration(start_date=yesterday, db_path=db_path)

        assert isinstance(avg_duration, float)
        assert avg_duration >= 0.0


# ============================================================================
# MCQ Statistics Tests
# ============================================================================

@pytest.fixture
def db_with_mcq_reviews_and_history(clean_db):
    """Database with MCQ reviews and history spanning multiple days."""
    from src.japanese_cli.models import ItemType
    from src.japanese_cli.database import get_cursor

    # Add vocabulary items
    vocab_ids = []
    for i in range(5):
        vocab_id = add_vocabulary(
            word=f"単語{i}",
            reading=f"たんご{i}",
            meanings={"vi": [f"từ {i}"], "en": [f"word {i}"]},
            jlpt_level="n5",
            db_path=clean_db
        )
        vocab_ids.append(vocab_id)

    # Add kanji items
    kanji_ids = []
    kanji_chars = ["語", "話", "読", "書", "聞"]
    for i, char in enumerate(kanji_chars):
        kanji_id = add_kanji(
            character=char,
            on_readings=[f"オン{i}"],
            kun_readings=[f"くん{i}"],
            meanings={"vi": [f"kanji {i}"], "en": [f"kanji {i}"]},
            jlpt_level="n5",
            db_path=clean_db
        )
        kanji_ids.append(kanji_id)

    # Create MCQ reviews
    scheduler = MCQReviewScheduler(db_path=clean_db)
    mcq_review_ids = []

    # Create 3 vocab MCQ reviews
    for vocab_id in vocab_ids[:3]:
        review_id = scheduler.create_mcq_review(vocab_id, ItemType.VOCAB)
        mcq_review_ids.append((review_id, ItemType.VOCAB))

    # Create 2 kanji MCQ reviews
    for kanji_id in kanji_ids[:2]:
        review_id = scheduler.create_mcq_review(kanji_id, ItemType.KANJI)
        mcq_review_ids.append((review_id, ItemType.KANJI))

    # Add MCQ review history with mixed correct/incorrect answers
    with get_cursor(clean_db) as cursor:
        # Vocab reviews (3 items): 2 correct, 1 incorrect
        # Review 1: Correct (option A)
        cursor.execute("""
            INSERT INTO mcq_review_history (mcq_review_id, selected_option, is_correct, duration_ms)
            VALUES (?, ?, ?, ?)
        """, (mcq_review_ids[0][0], 0, 1, 3000))

        # Review 2: Correct (option B)
        cursor.execute("""
            INSERT INTO mcq_review_history (mcq_review_id, selected_option, is_correct, duration_ms)
            VALUES (?, ?, ?, ?)
        """, (mcq_review_ids[1][0], 1, 1, 4000))

        # Review 3: Incorrect (option C)
        cursor.execute("""
            INSERT INTO mcq_review_history (mcq_review_id, selected_option, is_correct, duration_ms)
            VALUES (?, ?, ?, ?)
        """, (mcq_review_ids[2][0], 2, 0, 2500))

        # Kanji reviews (2 items): 1 correct, 1 incorrect
        # Review 4: Correct (option A)
        cursor.execute("""
            INSERT INTO mcq_review_history (mcq_review_id, selected_option, is_correct, duration_ms)
            VALUES (?, ?, ?, ?)
        """, (mcq_review_ids[3][0], 0, 1, 3500))

        # Review 5: Incorrect (option D)
        cursor.execute("""
            INSERT INTO mcq_review_history (mcq_review_id, selected_option, is_correct, duration_ms)
            VALUES (?, ?, ?, ?)
        """, (mcq_review_ids[4][0], 3, 0, 2000))

    return clean_db, vocab_ids, kanji_ids, mcq_review_ids


# Tests for get_mcq_accuracy_rate

class TestGetMCQAccuracyRate:
    """Tests for get_mcq_accuracy_rate function."""

    def test_empty_database(self, clean_db):
        """Test with no MCQ reviews returns 0.0."""
        accuracy = get_mcq_accuracy_rate(db_path=clean_db)
        assert accuracy == 0.0

    def test_overall_accuracy(self, db_with_mcq_reviews_and_history):
        """Test calculating overall MCQ accuracy."""
        db_path, vocab_ids, kanji_ids, mcq_review_ids = db_with_mcq_reviews_and_history

        # 3 correct, 2 incorrect = 60% accuracy
        accuracy = get_mcq_accuracy_rate(db_path=db_path)

        assert isinstance(accuracy, float)
        assert accuracy == 60.0  # 3/5 * 100

    def test_filter_by_vocab_type(self, db_with_mcq_reviews_and_history):
        """Test filtering by vocab item type."""
        db_path, vocab_ids, kanji_ids, mcq_review_ids = db_with_mcq_reviews_and_history

        # Vocab: 2 correct, 1 incorrect = 66.7% accuracy
        accuracy = get_mcq_accuracy_rate(item_type="vocab", db_path=db_path)

        assert isinstance(accuracy, float)
        assert 66.0 <= accuracy <= 67.0  # ~66.7%

    def test_filter_by_kanji_type(self, db_with_mcq_reviews_and_history):
        """Test filtering by kanji item type."""
        db_path, vocab_ids, kanji_ids, mcq_review_ids = db_with_mcq_reviews_and_history

        # Kanji: 1 correct, 1 incorrect = 50% accuracy
        accuracy = get_mcq_accuracy_rate(item_type="kanji", db_path=db_path)

        assert accuracy == 50.0  # 1/2 * 100

    def test_filter_by_jlpt_level(self, db_with_mcq_reviews_and_history):
        """Test filtering by JLPT level."""
        db_path, vocab_ids, kanji_ids, mcq_review_ids = db_with_mcq_reviews_and_history

        # All items are N5, so should match overall accuracy
        accuracy = get_mcq_accuracy_rate(jlpt_level="n5", db_path=db_path)

        assert accuracy == 60.0  # 3/5 * 100

    def test_filter_by_jlpt_level_no_matches(self, db_with_mcq_reviews_and_history):
        """Test filtering by JLPT level with no matching reviews."""
        db_path, vocab_ids, kanji_ids, mcq_review_ids = db_with_mcq_reviews_and_history

        # No N1 items
        accuracy = get_mcq_accuracy_rate(jlpt_level="n1", db_path=db_path)

        assert accuracy == 0.0

    def test_filter_by_date_range(self, db_with_mcq_reviews_and_history):
        """Test filtering by date range."""
        db_path, vocab_ids, kanji_ids, mcq_review_ids = db_with_mcq_reviews_and_history

        today = date.today()
        accuracy = get_mcq_accuracy_rate(
            start_date=today,
            end_date=today,
            db_path=db_path
        )

        # All reviews are today, so should match overall
        assert accuracy == 60.0

    def test_filter_combined(self, db_with_mcq_reviews_and_history):
        """Test combined filtering (type + JLPT + date)."""
        db_path, vocab_ids, kanji_ids, mcq_review_ids = db_with_mcq_reviews_and_history

        today = date.today()
        accuracy = get_mcq_accuracy_rate(
            start_date=today,
            end_date=today,
            item_type="vocab",
            jlpt_level="n5",
            db_path=db_path
        )

        assert 66.0 <= accuracy <= 67.0  # Vocab N5 today: 2/3 correct


# Tests for get_mcq_stats_by_type

class TestGetMCQStatsByType:
    """Tests for get_mcq_stats_by_type function."""

    def test_empty_database(self, clean_db):
        """Test with no MCQ reviews returns zeros."""
        stats = get_mcq_stats_by_type(db_path=clean_db)

        assert isinstance(stats, dict)
        assert "vocab" in stats
        assert "kanji" in stats
        assert "overall" in stats

        # All should be zero
        assert stats["vocab"]["total_reviews"] == 0
        assert stats["kanji"]["total_reviews"] == 0
        assert stats["overall"]["total_reviews"] == 0

    def test_stats_structure(self, db_with_mcq_reviews_and_history):
        """Test the structure of returned stats."""
        db_path, vocab_ids, kanji_ids, mcq_review_ids = db_with_mcq_reviews_and_history

        stats = get_mcq_stats_by_type(db_path=db_path)

        # Check structure
        for item_type in ["vocab", "kanji", "overall"]:
            assert item_type in stats
            assert "total_reviews" in stats[item_type]
            assert "correct_count" in stats[item_type]
            assert "incorrect_count" in stats[item_type]
            assert "accuracy_rate" in stats[item_type]

    def test_vocab_stats(self, db_with_mcq_reviews_and_history):
        """Test vocab-specific statistics."""
        db_path, vocab_ids, kanji_ids, mcq_review_ids = db_with_mcq_reviews_and_history

        stats = get_mcq_stats_by_type(db_path=db_path)

        # Vocab: 3 total, 2 correct, 1 incorrect, 66.7% accuracy
        assert stats["vocab"]["total_reviews"] == 3
        assert stats["vocab"]["correct_count"] == 2
        assert stats["vocab"]["incorrect_count"] == 1
        assert 66.0 <= stats["vocab"]["accuracy_rate"] <= 67.0

    def test_kanji_stats(self, db_with_mcq_reviews_and_history):
        """Test kanji-specific statistics."""
        db_path, vocab_ids, kanji_ids, mcq_review_ids = db_with_mcq_reviews_and_history

        stats = get_mcq_stats_by_type(db_path=db_path)

        # Kanji: 2 total, 1 correct, 1 incorrect, 50% accuracy
        assert stats["kanji"]["total_reviews"] == 2
        assert stats["kanji"]["correct_count"] == 1
        assert stats["kanji"]["incorrect_count"] == 1
        assert stats["kanji"]["accuracy_rate"] == 50.0

    def test_overall_stats(self, db_with_mcq_reviews_and_history):
        """Test overall aggregated statistics."""
        db_path, vocab_ids, kanji_ids, mcq_review_ids = db_with_mcq_reviews_and_history

        stats = get_mcq_stats_by_type(db_path=db_path)

        # Overall: 5 total, 3 correct, 2 incorrect, 60% accuracy
        assert stats["overall"]["total_reviews"] == 5
        assert stats["overall"]["correct_count"] == 3
        assert stats["overall"]["incorrect_count"] == 2
        assert stats["overall"]["accuracy_rate"] == 60.0

    def test_filter_by_jlpt_level(self, db_with_mcq_reviews_and_history):
        """Test filtering by JLPT level."""
        db_path, vocab_ids, kanji_ids, mcq_review_ids = db_with_mcq_reviews_and_history

        stats = get_mcq_stats_by_type(jlpt_level="n5", db_path=db_path)

        # All items are N5, so should match unfiltered stats
        assert stats["overall"]["total_reviews"] == 5

    def test_filter_by_date_range(self, db_with_mcq_reviews_and_history):
        """Test filtering by date range."""
        db_path, vocab_ids, kanji_ids, mcq_review_ids = db_with_mcq_reviews_and_history

        today = date.today()
        stats = get_mcq_stats_by_type(
            start_date=today,
            end_date=today,
            db_path=db_path
        )

        # All reviews are today
        assert stats["overall"]["total_reviews"] == 5

    def test_filter_past_date_range(self, db_with_mcq_reviews_and_history):
        """Test filtering by past date range returns zeros."""
        db_path, vocab_ids, kanji_ids, mcq_review_ids = db_with_mcq_reviews_and_history

        past = date.today() - timedelta(days=7)
        stats = get_mcq_stats_by_type(
            start_date=past,
            end_date=past,
            db_path=db_path
        )

        # No reviews from 7 days ago
        assert stats["overall"]["total_reviews"] == 0


# Tests for get_mcq_option_distribution

class TestGetMCQOptionDistribution:
    """Tests for get_mcq_option_distribution function."""

    def test_empty_database(self, clean_db):
        """Test with no MCQ reviews returns all zeros."""
        distribution = get_mcq_option_distribution(db_path=clean_db)

        assert isinstance(distribution, dict)
        assert distribution == {"A": 0, "B": 0, "C": 0, "D": 0}

    def test_option_distribution(self, db_with_mcq_reviews_and_history):
        """Test getting option distribution."""
        db_path, vocab_ids, kanji_ids, mcq_review_ids = db_with_mcq_reviews_and_history

        distribution = get_mcq_option_distribution(db_path=db_path)

        # From fixture:
        # - 2 reviews selected option A (index 0)
        # - 1 review selected option B (index 1)
        # - 1 review selected option C (index 2)
        # - 1 review selected option D (index 3)
        assert distribution["A"] == 2
        assert distribution["B"] == 1
        assert distribution["C"] == 1
        assert distribution["D"] == 1

    def test_all_options_present(self, db_with_mcq_reviews_and_history):
        """Test that all 4 options are always in result."""
        db_path, vocab_ids, kanji_ids, mcq_review_ids = db_with_mcq_reviews_and_history

        distribution = get_mcq_option_distribution(db_path=db_path)

        # All options should be present, even if count is 0
        assert "A" in distribution
        assert "B" in distribution
        assert "C" in distribution
        assert "D" in distribution

    def test_filter_by_date_range(self, db_with_mcq_reviews_and_history):
        """Test filtering by date range."""
        db_path, vocab_ids, kanji_ids, mcq_review_ids = db_with_mcq_reviews_and_history

        today = date.today()
        distribution = get_mcq_option_distribution(
            start_date=today,
            end_date=today,
            db_path=db_path
        )

        # All reviews are today, so should match unfiltered
        assert distribution["A"] == 2
        assert distribution["B"] == 1
        assert distribution["C"] == 1
        assert distribution["D"] == 1

    def test_filter_past_date_range(self, db_with_mcq_reviews_and_history):
        """Test filtering by past date range returns zeros."""
        db_path, vocab_ids, kanji_ids, mcq_review_ids = db_with_mcq_reviews_and_history

        past = date.today() - timedelta(days=7)
        distribution = get_mcq_option_distribution(
            start_date=past,
            end_date=past,
            db_path=db_path
        )

        # No reviews from 7 days ago
        assert distribution == {"A": 0, "B": 0, "C": 0, "D": 0}

    def test_detect_selection_bias(self, db_with_mcq_reviews_and_history):
        """Test that we can detect selection bias."""
        db_path, vocab_ids, kanji_ids, mcq_review_ids = db_with_mcq_reviews_and_history

        distribution = get_mcq_option_distribution(db_path=db_path)

        # User selected A twice, suggesting possible bias toward first option
        max_selections = max(distribution.values())
        assert distribution["A"] == max_selections
