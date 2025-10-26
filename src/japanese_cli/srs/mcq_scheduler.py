"""
MCQ Review scheduler for Japanese Learning CLI.

High-level coordinator between database, models, and FSRS for managing
MCQ review sessions with spaced repetition.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fsrs import Card

from ..database import (
    add_mcq_review_history,
    create_mcq_review as db_create_mcq_review,
    get_due_mcq_cards,
    get_mcq_review as db_get_mcq_review,
    get_mcq_review_by_id as db_get_mcq_review_by_id,
    update_mcq_review as db_update_mcq_review,
    get_vocabulary_by_id,
    get_kanji_by_id,
)
from ..models import MCQReview, ItemType
from .fsrs import FSRSManager


class MCQReviewScheduler:
    """
    High-level scheduler for managing MCQ review sessions.

    Coordinates between the database layer, MCQReview models, and FSRS to provide
    a simple API for creating MCQ reviews, getting due cards, and processing answers.

    Unlike regular flashcard reviews which use 4-level ratings (Again/Hard/Good/Easy),
    MCQ reviews use binary correctness (correct/incorrect) which maps to:
    - Correct → Rating.Good (3)
    - Incorrect → Rating.Again (1)

    Attributes:
        fsrs_manager: The FSRS manager instance
        db_path: Optional database path (uses default if None)

    Example:
        scheduler = MCQReviewScheduler()

        # Create an MCQ review for vocabulary item
        review_id = scheduler.create_mcq_review(vocab_id, ItemType.VOCAB)

        # Get due MCQ reviews
        due_mcqs = scheduler.get_due_mcqs(limit=20)

        # Process an MCQ review (user answered correctly, selected option 2)
        updated_review = scheduler.process_mcq_review(
            review_id=review_id,
            is_correct=True,
            selected_option=2,
            duration_ms=5000
        )
    """

    def __init__(
        self,
        fsrs_manager: Optional[FSRSManager] = None,
        db_path: Optional[Path] = None,
    ):
        """
        Initialize MCQ review scheduler.

        Args:
            fsrs_manager: Optional FSRS manager (creates default if None)
            db_path: Optional database path (uses default if None)

        Example:
            # Use defaults
            scheduler = MCQReviewScheduler()

            # Custom FSRS configuration
            custom_fsrs = FSRSManager(desired_retention=0.95)
            scheduler = MCQReviewScheduler(fsrs_manager=custom_fsrs)
        """
        self.fsrs_manager = fsrs_manager or FSRSManager()
        self.db_path = db_path

    def create_mcq_review(
        self, item_id: int, item_type: ItemType | str
    ) -> int:
        """
        Create a new MCQ review entry for a vocabulary or kanji item.

        Creates a fresh FSRS card in Learning state and stores it in the database.
        This is separate from regular flashcard reviews - the same item can have
        both a flashcard review and an MCQ review with independent FSRS states.

        Args:
            item_id: ID of vocabulary or kanji item
            item_type: Type of item (ItemType.VOCAB or ItemType.KANJI)

        Returns:
            int: ID of created MCQ review entry

        Raises:
            ValueError: If item_id is invalid or item doesn't exist

        Example:
            review_id = scheduler.create_mcq_review(1, ItemType.VOCAB)
        """
        # Convert string to ItemType if needed
        if isinstance(item_type, str):
            item_type = ItemType(item_type)

        # Verify item exists
        if item_type == ItemType.VOCAB:
            item = get_vocabulary_by_id(item_id, db_path=self.db_path)
            if item is None:
                raise ValueError(f"Vocabulary with id {item_id} not found")
        else:  # ItemType.KANJI
            item = get_kanji_by_id(item_id, db_path=self.db_path)
            if item is None:
                raise ValueError(f"Kanji with id {item_id} not found")

        # Create MCQ review using MCQReview model
        mcq_review = MCQReview.create_new(item_id=item_id, item_type=item_type)

        # Store in database
        review_id = db_create_mcq_review(
            item_id=mcq_review.item_id,
            item_type=mcq_review.item_type.value,
            fsrs_card_state=mcq_review.fsrs_card_state,
            due_date=mcq_review.due_date,
            db_path=self.db_path,
        )

        return review_id

    def get_due_mcqs(
        self,
        limit: Optional[int] = None,
        jlpt_level: Optional[str] = None,
        item_type: Optional[ItemType | str] = None,
    ) -> list[MCQReview]:
        """
        Get MCQ reviews that are due for study.

        Retrieves cards from database and converts them to MCQReview model instances.

        Args:
            limit: Maximum number of reviews to return (optional)
            jlpt_level: Filter by JLPT level (n5, n4, n3, n2, n1) (optional)
            item_type: Filter by item type (vocab or kanji) (optional)

        Returns:
            list[MCQReview]: List of due MCQ review instances

        Example:
            # Get all due MCQ reviews
            due = scheduler.get_due_mcqs()

            # Get 20 N5 vocabulary MCQ reviews
            due = scheduler.get_due_mcqs(limit=20, jlpt_level='n5', item_type=ItemType.VOCAB)
        """
        # Convert ItemType to string if needed
        item_type_str = None
        if item_type is not None:
            if isinstance(item_type, ItemType):
                item_type_str = item_type.value
            else:
                item_type_str = item_type

        # Get due cards from database
        due_cards = get_due_mcq_cards(
            item_type=item_type_str,
            jlpt_level=jlpt_level,
            limit=limit,
            db_path=self.db_path,
        )

        # Convert to MCQReview models
        mcq_reviews = [MCQReview.from_db_row(card) for card in due_cards]

        return mcq_reviews

    def get_mcq_review_by_item(
        self, item_id: int, item_type: ItemType | str
    ) -> Optional[MCQReview]:
        """
        Get MCQ review entry for a specific item.

        Args:
            item_id: ID of vocabulary or kanji item
            item_type: Type of item (ItemType.VOCAB or ItemType.KANJI)

        Returns:
            MCQReview or None: MCQ review instance if found, None otherwise

        Example:
            review = scheduler.get_mcq_review_by_item(1, ItemType.VOCAB)
            if review:
                print(f"Due: {review.due_date}")
        """
        # Convert ItemType to string if needed
        if isinstance(item_type, ItemType):
            item_type_str = item_type.value
        else:
            item_type_str = item_type

        # Get from database
        review_row = db_get_mcq_review(
            item_id=item_id, item_type=item_type_str, db_path=self.db_path
        )

        if review_row is None:
            return None

        # Convert to MCQReview model
        return MCQReview.from_db_row(review_row)

    def process_mcq_review(
        self,
        review_id: int,
        is_correct: bool,
        selected_option: int,
        duration_ms: Optional[int] = None,
    ) -> MCQReview:
        """
        Process an MCQ review and update card state.

        This is the main workflow method that:
        1. Loads MCQ review from database
        2. Gets FSRS card from review
        3. Converts is_correct to FSRS rating (correct→Good, incorrect→Again)
        4. Processes the review with FSRS scheduler
        5. Updates review model with new card state
        6. Saves updated review to database
        7. Records review in mcq_review_history (includes selected_option)
        8. Returns updated MCQReview

        Args:
            review_id: ID of MCQ review entry to process
            is_correct: Whether the user answered correctly
            selected_option: Index of option selected by user (0-3 for A/B/C/D)
            duration_ms: Time spent on question in milliseconds (optional)

        Returns:
            MCQReview: Updated MCQ review instance

        Raises:
            ValueError: If review_id not found or selected_option invalid

        Example:
            # User answered correctly (selected option B which was correct)
            updated_review = scheduler.process_mcq_review(
                review_id=5,
                is_correct=True,
                selected_option=1,  # B (0=A, 1=B, 2=C, 3=D)
                duration_ms=4500
            )
            print(f"Next review: {updated_review.due_date}")
        """
        # Validate selected_option
        if not 0 <= selected_option <= 3:
            raise ValueError(
                f"selected_option must be 0-3, got {selected_option}. "
                "0=A, 1=B, 2=C, 3=D"
            )

        # Load review from database
        review_row = db_get_mcq_review_by_id(review_id, db_path=self.db_path)

        if review_row is None:
            raise ValueError(f"MCQ review with id {review_id} not found")

        # Convert to MCQReview model
        mcq_review = MCQReview.from_db_row(review_row)

        # Get FSRS card from review
        card = mcq_review.get_card()

        # Convert is_correct to FSRS rating
        # Correct answer → Rating.Good (3)
        # Incorrect answer → Rating.Again (1)
        rating = 3 if is_correct else 1

        # Process review with FSRS
        updated_card, review_log = self.fsrs_manager.review_card(card, rating)

        # Update review model with new card state
        mcq_review.update_from_card(updated_card)

        # Save to database (db function handles last_reviewed and review_count)
        db_update_mcq_review(
            review_id=mcq_review.id,
            fsrs_card_state=mcq_review.fsrs_card_state,
            due_date=mcq_review.due_date,
            db_path=self.db_path,
        )

        # Update local model to reflect database changes
        mcq_review.last_reviewed = datetime.now(timezone.utc)
        mcq_review.review_count += 1
        mcq_review.updated_at = datetime.now(timezone.utc)

        # Record in history (includes selected_option for MCQ analytics)
        add_mcq_review_history(
            mcq_review_id=mcq_review.id,
            selected_option=selected_option,
            is_correct=is_correct,
            duration_ms=duration_ms,
            db_path=self.db_path,
        )

        return mcq_review

    def get_mcq_review_count(
        self, jlpt_level: Optional[str] = None, item_type: Optional[ItemType | str] = None
    ) -> int:
        """
        Get total count of MCQ reviews in the system.

        Args:
            jlpt_level: Filter by JLPT level (optional)
            item_type: Filter by item type (optional)

        Returns:
            int: Total number of MCQ reviews

        Example:
            total = scheduler.get_mcq_review_count()
            n5_vocab = scheduler.get_mcq_review_count(jlpt_level='n5', item_type=ItemType.VOCAB)
        """
        from ..database import get_cursor

        # Convert ItemType to string if needed
        item_type_str = None
        if item_type is not None:
            if isinstance(item_type, ItemType):
                item_type_str = item_type.value
            else:
                item_type_str = item_type

        # Simple case: no filters
        if jlpt_level is None and item_type_str is None:
            query = "SELECT COUNT(*) FROM mcq_reviews"
            params = []
        # Case: filter by item_type only
        elif jlpt_level is None and item_type_str is not None:
            query = "SELECT COUNT(*) FROM mcq_reviews WHERE item_type = ?"
            params = [item_type_str]
        # Case: filter by both item_type and jlpt_level
        elif jlpt_level is not None and item_type_str is not None:
            if item_type_str == "vocab":
                query = """
                    SELECT COUNT(*) FROM mcq_reviews r
                    JOIN vocabulary v ON r.item_id = v.id
                    WHERE r.item_type = 'vocab' AND v.jlpt_level = ?
                """
            else:  # kanji
                query = """
                    SELECT COUNT(*) FROM mcq_reviews r
                    JOIN kanji k ON r.item_id = k.id
                    WHERE r.item_type = 'kanji' AND k.jlpt_level = ?
                """
            params = [jlpt_level]
        # Case: filter by jlpt_level only (need to query both vocab and kanji)
        else:  # jlpt_level is not None and item_type_str is None
            query = """
                SELECT COUNT(*) FROM (
                    SELECT r.id FROM mcq_reviews r
                    JOIN vocabulary v ON r.item_id = v.id
                    WHERE r.item_type = 'vocab' AND v.jlpt_level = ?
                    UNION ALL
                    SELECT r.id FROM mcq_reviews r
                    JOIN kanji k ON r.item_id = k.id
                    WHERE r.item_type = 'kanji' AND k.jlpt_level = ?
                )
            """
            params = [jlpt_level, jlpt_level]

        with get_cursor(self.db_path) as cursor:
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result[0] if result else 0
