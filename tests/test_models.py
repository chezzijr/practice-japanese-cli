"""
Comprehensive tests for Pydantic data models.

Tests validation, serialization, and database conversion for all models.
"""

import json
from datetime import date, datetime, timezone

import pytest
from fsrs import Card, Rating
from pydantic import ValidationError

from japanese_cli.models import (
    Example,
    GrammarPoint,
    ItemType,
    Kanji,
    Progress,
    ProgressStats,
    Review,
    ReviewHistory,
    Vocabulary,
)


# ============================================================================
# Vocabulary Model Tests
# ============================================================================

class TestVocabulary:
    """Tests for Vocabulary model."""

    def test_vocabulary_creation_success(self):
        """Test creating a valid vocabulary entry."""
        vocab = Vocabulary(
            word="単語",
            reading="たんご",
            meanings={"vi": ["từ vựng"], "en": ["word", "vocabulary"]},
            vietnamese_reading="đơn ngữ",
            jlpt_level="n5",
            part_of_speech="noun",
            tags=["common", "basic"],
            notes="Test note"
        )

        assert vocab.word == "単語"
        assert vocab.reading == "たんご"
        assert vocab.meanings == {"vi": ["từ vựng"], "en": ["word", "vocabulary"]}
        assert vocab.vietnamese_reading == "đơn ngữ"
        assert vocab.jlpt_level == "n5"
        assert vocab.part_of_speech == "noun"
        assert vocab.tags == ["common", "basic"]
        assert vocab.notes == "Test note"

    def test_vocabulary_valid_jlpt_levels(self):
        """Test all valid JLPT levels."""
        for level in ['n5', 'n4', 'n3', 'n2', 'n1', None]:
            vocab = Vocabulary(
                word="単語",
                reading="たんご",
                meanings={"vi": ["từ vựng"]},
                jlpt_level=level
            )
            assert vocab.jlpt_level == level

    def test_vocabulary_invalid_jlpt_level(self):
        """Test that invalid JLPT level raises error."""
        with pytest.raises(ValidationError) as exc_info:
            Vocabulary(
                word="単語",
                reading="たんご",
                meanings={"vi": ["từ vựng"]},
                jlpt_level="n6"
            )

        assert "JLPT level must be one of" in str(exc_info.value)

    def test_vocabulary_empty_meanings(self):
        """Test that empty meanings dict raises error."""
        with pytest.raises(ValidationError) as exc_info:
            Vocabulary(
                word="単語",
                reading="たんご",
                meanings={}
            )

        assert "Meanings dictionary cannot be empty" in str(exc_info.value)

    def test_vocabulary_meanings_with_empty_lists(self):
        """Test that meanings with only empty lists raises error."""
        with pytest.raises(ValidationError) as exc_info:
            Vocabulary(
                word="単語",
                reading="たんご",
                meanings={"vi": [], "en": []}
            )

        assert "At least one language must have at least one meaning" in str(exc_info.value)

    def test_vocabulary_from_db_row(self):
        """Test converting from database row to model."""
        db_row = {
            "id": 1,
            "word": "単語",
            "reading": "たんご",
            "meanings": '{"vi": ["từ vựng"], "en": ["word"]}',
            "vietnamese_reading": "đơn ngữ",
            "jlpt_level": "n5",
            "part_of_speech": "noun",
            "tags": '["common", "basic"]',
            "notes": "Test",
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00"
        }

        vocab = Vocabulary.from_db_row(db_row)

        assert vocab.id == 1
        assert vocab.word == "単語"
        assert vocab.meanings == {"vi": ["từ vựng"], "en": ["word"]}
        assert vocab.tags == ["common", "basic"]

    def test_vocabulary_to_db_dict(self):
        """Test converting model to database dict."""
        vocab = Vocabulary(
            word="単語",
            reading="たんご",
            meanings={"vi": ["từ vựng"]},
            tags=["common"]
        )

        db_dict = vocab.to_db_dict(exclude_id=True)

        assert db_dict["word"] == "単語"
        assert db_dict["reading"] == "たんご"
        # Meanings should be JSON string
        assert isinstance(db_dict["meanings"], str)
        meanings = json.loads(db_dict["meanings"])
        assert meanings == {"vi": ["từ vựng"]}
        # Tags should be JSON string
        assert isinstance(db_dict["tags"], str)
        tags = json.loads(db_dict["tags"])
        assert tags == ["common"]


# ============================================================================
# Kanji Model Tests
# ============================================================================

class TestKanji:
    """Tests for Kanji model."""

    def test_kanji_creation_success(self):
        """Test creating a valid kanji entry."""
        kanji = Kanji(
            character="語",
            on_readings=["ゴ"],
            kun_readings=["かた.る", "かた.らう"],
            meanings={"vi": ["ngữ"], "en": ["word", "language"]},
            vietnamese_reading="ngữ",
            jlpt_level="n5",
            stroke_count=14,
            radical="言",
            notes="Test note"
        )

        assert kanji.character == "語"
        assert kanji.on_readings == ["ゴ"]
        assert kanji.kun_readings == ["かた.る", "かた.らう"]
        assert kanji.vietnamese_reading == "ngữ"
        assert kanji.stroke_count == 14

    def test_kanji_character_length_validation(self):
        """Test that character must be exactly 1 character."""
        with pytest.raises(ValidationError):
            Kanji(
                character="語語",  # Too long
                meanings={"vi": ["test"]}
            )

    def test_kanji_invalid_jlpt_level(self):
        """Test that invalid JLPT level raises error."""
        with pytest.raises(ValidationError) as exc_info:
            Kanji(
                character="語",
                meanings={"vi": ["ngữ"]},
                jlpt_level="invalid"
            )

        assert "JLPT level must be one of" in str(exc_info.value)

    def test_kanji_requires_reading_or_meaning(self):
        """Test that kanji needs at least one reading or meaning."""
        # Should fail with no readings and empty meanings
        with pytest.raises(ValidationError):
            Kanji(
                character="語",
                on_readings=[],
                kun_readings=[],
                meanings={"vi": []}
            )

    def test_kanji_from_db_row(self):
        """Test converting from database row to model."""
        db_row = {
            "id": 1,
            "character": "語",
            "on_readings": '["ゴ"]',
            "kun_readings": '["かた.る"]',
            "meanings": '{"vi": ["ngữ"]}',
            "vietnamese_reading": "ngữ",
            "jlpt_level": "n5",
            "stroke_count": 14,
            "radical": "言",
            "notes": None,
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00"
        }

        kanji = Kanji.from_db_row(db_row)

        assert kanji.id == 1
        assert kanji.character == "語"
        assert kanji.on_readings == ["ゴ"]
        assert kanji.kun_readings == ["かた.る"]

    def test_kanji_to_db_dict(self):
        """Test converting model to database dict."""
        kanji = Kanji(
            character="語",
            on_readings=["ゴ"],
            kun_readings=["かた.る"],
            meanings={"vi": ["ngữ"]}
        )

        db_dict = kanji.to_db_dict(exclude_id=True)

        assert db_dict["character"] == "語"
        # Readings should be JSON strings
        assert isinstance(db_dict["on_readings"], str)
        assert json.loads(db_dict["on_readings"]) == ["ゴ"]
        assert isinstance(db_dict["kun_readings"], str)
        assert json.loads(db_dict["kun_readings"]) == ["かた.る"]


# ============================================================================
# Grammar Model Tests
# ============================================================================

class TestGrammarPoint:
    """Tests for GrammarPoint and Example models."""

    def test_example_creation_success(self):
        """Test creating a valid example."""
        example = Example(
            jp="私は学生です",
            vi="Tôi là học sinh",
            en="I am a student"
        )

        assert example.jp == "私は学生です"
        assert example.vi == "Tôi là học sinh"
        assert example.en == "I am a student"

    def test_example_without_english(self):
        """Test creating example without English translation."""
        example = Example(
            jp="私は学生です",
            vi="Tôi là học sinh"
        )

        assert example.en is None

    def test_grammar_creation_success(self):
        """Test creating a valid grammar point."""
        grammar = GrammarPoint(
            title="は (wa) particle",
            structure="Noun + は + Predicate",
            explanation="Marks the topic of a sentence",
            jlpt_level="n5",
            examples=[
                Example(jp="私は学生です", vi="Tôi là học sinh", en="I am a student")
            ],
            related_grammar=[1, 2],
            notes="Common particle"
        )

        assert grammar.title == "は (wa) particle"
        assert len(grammar.examples) == 1
        assert grammar.related_grammar == [1, 2]

    def test_grammar_requires_examples(self):
        """Test that grammar point needs at least one example."""
        with pytest.raises(ValidationError) as exc_info:
            GrammarPoint(
                title="Test",
                explanation="Test explanation",
                examples=[]
            )

        assert "Grammar point must have at least one example" in str(exc_info.value)

    def test_grammar_invalid_jlpt_level(self):
        """Test that invalid JLPT level raises error."""
        with pytest.raises(ValidationError):
            GrammarPoint(
                title="Test",
                explanation="Test",
                jlpt_level="invalid",
                examples=[Example(jp="test", vi="test")]
            )

    def test_grammar_from_db_row(self):
        """Test converting from database row to model."""
        db_row = {
            "id": 1,
            "title": "は particle",
            "structure": "Noun + は",
            "explanation": "Topic marker",
            "jlpt_level": "n5",
            "examples": '[{"jp": "私は学生です", "vi": "Tôi là học sinh", "en": "I am a student"}]',
            "related_grammar": '[1, 2]',
            "notes": None,
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00"
        }

        grammar = GrammarPoint.from_db_row(db_row)

        assert grammar.id == 1
        assert len(grammar.examples) == 1
        assert grammar.examples[0].jp == "私は学生です"
        assert grammar.related_grammar == [1, 2]

    def test_grammar_to_db_dict(self):
        """Test converting model to database dict."""
        grammar = GrammarPoint(
            title="Test",
            explanation="Test",
            examples=[Example(jp="test", vi="test")],
            related_grammar=[1, 2]
        )

        db_dict = grammar.to_db_dict(exclude_id=True)

        # Examples should be JSON string
        assert isinstance(db_dict["examples"], str)
        examples = json.loads(db_dict["examples"])
        assert len(examples) == 1
        assert examples[0]["jp"] == "test"

        # Related grammar should be JSON string
        assert isinstance(db_dict["related_grammar"], str)
        related = json.loads(db_dict["related_grammar"])
        assert related == [1, 2]


# ============================================================================
# Review Model Tests
# ============================================================================

class TestReview:
    """Tests for Review and ReviewHistory models."""

    def test_review_creation_success(self):
        """Test creating a valid review entry."""
        card = Card()
        card_state = card.to_dict()
        due_date = datetime.fromisoformat(card_state['due'].replace('Z', '+00:00'))

        review = Review(
            item_id=1,
            item_type=ItemType.VOCAB,
            fsrs_card_state=card_state,
            due_date=due_date,
            review_count=0
        )

        assert review.item_id == 1
        assert review.item_type == ItemType.VOCAB
        assert review.review_count == 0

    def test_review_create_new(self):
        """Test creating a new review with fresh FSRS state."""
        review = Review.create_new(item_id=1, item_type=ItemType.VOCAB)

        assert review.item_id == 1
        assert review.item_type == ItemType.VOCAB
        assert review.review_count == 0
        assert review.fsrs_card_state is not None
        assert 'card_id' in review.fsrs_card_state

    def test_review_get_card(self):
        """Test reconstructing FSRS Card from review."""
        review = Review.create_new(item_id=1, item_type=ItemType.VOCAB)
        card = review.get_card()

        assert isinstance(card, Card)
        assert card.card_id == review.fsrs_card_state['card_id']

    def test_review_update_from_card(self):
        """Test updating review state from FSRS Card."""
        review = Review.create_new(item_id=1, item_type=ItemType.VOCAB)
        card = review.get_card()

        # Simulate a review (this would normally be done by scheduler)
        from fsrs import Scheduler
        scheduler = Scheduler()
        card, review_log = scheduler.review_card(card, Rating.Good)

        # Update review from card
        old_due = review.due_date
        review.update_from_card(card)

        # Due date should be updated
        assert review.due_date != old_due
        assert review.fsrs_card_state == card.to_dict()

    def test_review_from_db_row(self):
        """Test converting from database row to model."""
        card = Card()
        card_state = card.to_dict()

        db_row = {
            "id": 1,
            "item_id": 1,
            "item_type": "vocab",
            "fsrs_card_state": json.dumps(card_state),
            "due_date": card_state['due'],
            "last_reviewed": None,
            "review_count": 0,
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00"
        }

        review = Review.from_db_row(db_row)

        assert review.id == 1
        assert review.item_type == ItemType.VOCAB
        assert isinstance(review.fsrs_card_state, dict)

    def test_review_to_db_dict(self):
        """Test converting model to database dict."""
        review = Review.create_new(item_id=1, item_type=ItemType.VOCAB)
        db_dict = review.to_db_dict(exclude_id=True)

        assert db_dict["item_id"] == 1
        assert db_dict["item_type"] == "vocab"  # Enum converted to string
        # Card state should be JSON string
        assert isinstance(db_dict["fsrs_card_state"], str)
        card_state = json.loads(db_dict["fsrs_card_state"])
        assert 'card_id' in card_state

    def test_review_history_creation_success(self):
        """Test creating a valid review history entry."""
        history = ReviewHistory(
            review_id=1,
            rating=3,
            duration_ms=5000
        )

        assert history.review_id == 1
        assert history.rating == 3
        assert history.duration_ms == 5000

    def test_review_history_rating_validation(self):
        """Test that rating must be between 1 and 4."""
        with pytest.raises(ValidationError):
            ReviewHistory(review_id=1, rating=0)

        with pytest.raises(ValidationError):
            ReviewHistory(review_id=1, rating=5)

    def test_review_history_get_rating_enum(self):
        """Test converting rating to FSRS Rating enum."""
        ratings = {
            1: Rating.Again,
            2: Rating.Hard,
            3: Rating.Good,
            4: Rating.Easy
        }

        for rating_int, rating_enum in ratings.items():
            history = ReviewHistory(review_id=1, rating=rating_int)
            assert history.get_rating_enum() == rating_enum


# ============================================================================
# Progress Model Tests
# ============================================================================

class TestProgress:
    """Tests for Progress and ProgressStats models."""

    def test_progress_stats_creation_success(self):
        """Test creating valid progress stats."""
        stats = ProgressStats(
            total_vocab=500,
            total_kanji=103,
            mastered_vocab=50,
            mastered_kanji=20,
            total_reviews=1000,
            average_retention=0.85
        )

        assert stats.total_vocab == 500
        assert stats.mastered_vocab == 50
        assert stats.average_retention == 0.85

    def test_progress_stats_mastered_exceeding_total(self):
        """Test that mastered cannot exceed total."""
        with pytest.raises(ValidationError) as exc_info:
            ProgressStats(
                total_vocab=100,
                mastered_vocab=150  # More than total
            )

        assert "cannot exceed total vocab" in str(exc_info.value)

    def test_progress_creation_success(self):
        """Test creating valid progress entry."""
        progress = Progress(
            user_id="default",
            current_level="n5",
            target_level="n4",
            stats=ProgressStats(total_vocab=500),
            milestones=["First 100 reviews"],
            streak_days=5,
            last_review_date=date.today()
        )

        assert progress.user_id == "default"
        assert progress.current_level == "n5"
        assert progress.target_level == "n4"
        assert progress.streak_days == 5

    def test_progress_invalid_jlpt_level(self):
        """Test that invalid JLPT level raises error."""
        with pytest.raises(ValidationError):
            Progress(current_level="invalid")

        with pytest.raises(ValidationError):
            Progress(target_level="n6")

    def test_progress_increment_streak_first_review(self):
        """Test streak increment on first review."""
        progress = Progress()
        progress.increment_streak(date.today())

        assert progress.streak_days == 1
        assert progress.last_review_date == date.today()

    def test_progress_increment_streak_consecutive_days(self):
        """Test streak increment on consecutive days."""
        from datetime import timedelta

        progress = Progress()
        today = date.today()
        yesterday = today - timedelta(days=1)

        # Set last review to yesterday
        progress.last_review_date = yesterday
        progress.streak_days = 1

        # Review today
        progress.increment_streak(today)

        assert progress.streak_days == 2

    def test_progress_increment_streak_same_day(self):
        """Test that reviewing same day doesn't increment."""
        progress = Progress()
        today = date.today()

        progress.increment_streak(today)
        assert progress.streak_days == 1

        progress.increment_streak(today)
        assert progress.streak_days == 1  # Not incremented

    def test_progress_increment_streak_reset_after_gap(self):
        """Test streak resets after gap > 1 day."""
        from datetime import timedelta

        progress = Progress()
        today = date.today()
        three_days_ago = today - timedelta(days=3)

        # Set last review to 3 days ago
        progress.last_review_date = three_days_ago
        progress.streak_days = 5

        # Review today
        progress.increment_streak(today)

        assert progress.streak_days == 1  # Reset

    def test_progress_add_milestone(self):
        """Test adding milestones."""
        progress = Progress()

        progress.add_milestone("First 10 reviews")
        assert "First 10 reviews" in progress.milestones

        # Adding duplicate should not duplicate
        progress.add_milestone("First 10 reviews")
        assert progress.milestones.count("First 10 reviews") == 1

    def test_progress_from_db_row(self):
        """Test converting from database row to model."""
        db_row = {
            "id": 1,
            "user_id": "default",
            "current_level": "n5",
            "target_level": "n4",
            "stats": '{"total_vocab": 500, "total_kanji": 103, "mastered_vocab": 50, "mastered_kanji": 20, "total_reviews": 1000, "average_retention": 0.85}',
            "milestones": '["First 100 reviews"]',
            "streak_days": 5,
            "last_review_date": "2024-01-15",
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-15T12:00:00"
        }

        progress = Progress.from_db_row(db_row)

        assert progress.id == 1
        assert progress.stats.total_vocab == 500
        assert progress.milestones == ["First 100 reviews"]
        assert progress.streak_days == 5

    def test_progress_to_db_dict(self):
        """Test converting model to database dict."""
        progress = Progress(
            user_id="default",
            current_level="n5",
            stats=ProgressStats(total_vocab=500),
            milestones=["Test"]
        )

        db_dict = progress.to_db_dict(exclude_id=True)

        # Stats should be JSON string
        assert isinstance(db_dict["stats"], str)
        stats = json.loads(db_dict["stats"])
        assert stats["total_vocab"] == 500

        # Milestones should be JSON string
        assert isinstance(db_dict["milestones"], str)
        milestones = json.loads(db_dict["milestones"])
        assert milestones == ["Test"]
