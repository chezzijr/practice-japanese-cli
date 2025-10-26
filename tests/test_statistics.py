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
from src.japanese_cli.srs import ReviewScheduler
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
