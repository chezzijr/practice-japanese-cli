"""
Review scheduler for Japanese Learning CLI.

High-level coordinator between database, models, and FSRS for managing
review sessions and spaced repetition workflows.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fsrs import Card

from ..database import (
    add_review_history,
    create_review as db_create_review,
    get_due_cards,
    get_review as db_get_review,
    update_review as db_update_review,
    get_vocabulary_by_id,
    get_kanji_by_id,
)
from ..models import Review, ReviewHistory, ItemType
from .fsrs import FSRSManager


class ReviewScheduler:
    """
    High-level scheduler for managing review sessions.

    Coordinates between the database layer, Review models, and FSRS to provide
    a simple API for creating reviews, getting due cards, and processing reviews.

    Attributes:
        fsrs_manager: The FSRS manager instance
        db_path: Optional database path (uses default if None)

    Example:
        scheduler = ReviewScheduler()

        # Create a review for vocabulary item
        review_id = scheduler.create_new_review(vocab_id, ItemType.VOCAB)

        # Get due reviews
        due_reviews = scheduler.get_due_reviews(limit=20)

        # Process a review
        updated_review = scheduler.process_review(review_id, rating=3, duration_ms=5000)
    """

    def __init__(
        self,
        fsrs_manager: Optional[FSRSManager] = None,
        db_path: Optional[Path] = None,
    ):
        """
        Initialize review scheduler.

        Args:
            fsrs_manager: Optional FSRS manager (creates default if None)
            db_path: Optional database path (uses default if None)

        Example:
            # Use defaults
            scheduler = ReviewScheduler()

            # Custom FSRS configuration
            custom_fsrs = FSRSManager(desired_retention=0.95)
            scheduler = ReviewScheduler(fsrs_manager=custom_fsrs)
        """
        self.fsrs_manager = fsrs_manager or FSRSManager()
        self.db_path = db_path

    def create_new_review(
        self, item_id: int, item_type: ItemType | str
    ) -> int:
        """
        Create a new review entry for a vocabulary or kanji item.

        Creates a fresh FSRS card in Learning state and stores it in the database.

        Args:
            item_id: ID of vocabulary or kanji item
            item_type: Type of item (ItemType.VOCAB or ItemType.KANJI)

        Returns:
            int: ID of created review entry

        Raises:
            ValueError: If item_id is invalid or item doesn't exist

        Example:
            review_id = scheduler.create_new_review(1, ItemType.VOCAB)
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

        # Create review using Review model
        review = Review.create_new(item_id=item_id, item_type=item_type)

        # Store in database
        review_id = db_create_review(
            item_id=review.item_id,
            item_type=review.item_type.value,
            fsrs_card_state=review.fsrs_card_state,
            due_date=review.due_date,
            db_path=self.db_path,
        )

        return review_id

    def get_due_reviews(
        self,
        limit: Optional[int] = None,
        jlpt_level: Optional[str] = None,
        item_type: Optional[ItemType | str] = None,
    ) -> list[Review]:
        """
        Get reviews that are due for study.

        Retrieves cards from database and converts them to Review model instances.

        Args:
            limit: Maximum number of reviews to return (optional)
            jlpt_level: Filter by JLPT level (n5, n4, n3, n2, n1) (optional)
            item_type: Filter by item type (vocab or kanji) (optional)

        Returns:
            list[Review]: List of due Review instances

        Example:
            # Get all due reviews
            due = scheduler.get_due_reviews()

            # Get 20 N5 vocabulary reviews
            due = scheduler.get_due_reviews(limit=20, jlpt_level='n5', item_type=ItemType.VOCAB)
        """
        # Convert ItemType to string if needed
        item_type_str = None
        if item_type is not None:
            if isinstance(item_type, ItemType):
                item_type_str = item_type.value
            else:
                item_type_str = item_type

        # Get due cards from database
        due_cards = get_due_cards(
            limit=limit,
            jlpt_level=jlpt_level,
            item_type=item_type_str,
            db_path=self.db_path,
        )

        # Convert to Review models
        reviews = [Review.from_db_row(card) for card in due_cards]

        return reviews

    def get_review_by_item(
        self, item_id: int, item_type: ItemType | str
    ) -> Optional[Review]:
        """
        Get review entry for a specific item.

        Args:
            item_id: ID of vocabulary or kanji item
            item_type: Type of item (ItemType.VOCAB or ItemType.KANJI)

        Returns:
            Review or None: Review instance if found, None otherwise

        Example:
            review = scheduler.get_review_by_item(1, ItemType.VOCAB)
            if review:
                print(f"Due: {review.due_date}")
        """
        # Convert ItemType to string if needed
        if isinstance(item_type, ItemType):
            item_type_str = item_type.value
        else:
            item_type_str = item_type

        # Get from database
        review_row = db_get_review(
            item_id=item_id, item_type=item_type_str, db_path=self.db_path
        )

        if review_row is None:
            return None

        # Convert to Review model
        return Review.from_db_row(review_row)

    def process_review(
        self, review_id: int, rating: int, duration_ms: Optional[int] = None
    ) -> Review:
        """
        Process a review and update card state.

        This is the main workflow method that:
        1. Loads review from database
        2. Gets FSRS card from review
        3. Processes the review with FSRS scheduler
        4. Updates review model with new card state
        5. Saves updated review to database
        6. Records review in history
        7. Returns updated Review

        Args:
            review_id: ID of review entry to process
            rating: Rating (1=Again, 2=Hard, 3=Good, 4=Easy)
            duration_ms: Time spent reviewing in milliseconds (optional)

        Returns:
            Review: Updated review instance

        Raises:
            ValueError: If review_id not found or rating invalid

        Example:
            # User reviewed a card and rated it "Good"
            updated_review = scheduler.process_review(
                review_id=5,
                rating=3,
                duration_ms=4500
            )
            print(f"Next review: {updated_review.due_date}")
        """
        # Validate rating
        if rating not in [1, 2, 3, 4]:
            raise ValueError(
                f"Rating must be 1-4, got {rating}. "
                "1=Again, 2=Hard, 3=Good, 4=Easy"
            )

        # Load review from database
        # First get by ID (we need to query by review.id, not item_id)
        # The get_review function gets by item_id/item_type, so we need to
        # query directly or modify our approach

        # For now, we'll need to get the review differently
        # Let's get all due cards and find the one with matching id
        # This is not ideal, but works for now
        # TODO: Add get_review_by_id to database queries

        from ..database import get_cursor

        with get_cursor(self.db_path) as cursor:
            cursor.execute("SELECT * FROM reviews WHERE id = ?", (review_id,))
            review_row = cursor.fetchone()

        if review_row is None:
            raise ValueError(f"Review with id {review_id} not found")

        # Convert to Review model
        review = Review.from_db_row(dict(review_row))

        # Get FSRS card from review
        card = review.get_card()

        # Process review with FSRS
        updated_card, review_log = self.fsrs_manager.review_card(card, rating)

        # Update review model with new card state
        review.update_from_card(updated_card)

        # Save to database (db function handles last_reviewed and review_count)
        db_update_review(
            review_id=review.id,
            fsrs_card_state=review.fsrs_card_state,
            due_date=review.due_date,
            db_path=self.db_path,
        )

        # Update local model to reflect database changes
        review.last_reviewed = datetime.now(timezone.utc)
        review.review_count += 1
        review.updated_at = datetime.now(timezone.utc)

        # Record in history
        add_review_history(
            review_id=review.id,
            rating=rating,
            duration_ms=duration_ms,
            db_path=self.db_path,
        )

        return review

    def get_review_count(
        self, jlpt_level: Optional[str] = None, item_type: Optional[ItemType | str] = None
    ) -> int:
        """
        Get total count of reviews in the system.

        Args:
            jlpt_level: Filter by JLPT level (optional)
            item_type: Filter by item type (optional)

        Returns:
            int: Total number of reviews

        Example:
            total = scheduler.get_review_count()
            n5_vocab = scheduler.get_review_count(jlpt_level='n5', item_type=ItemType.VOCAB)
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
            query = "SELECT COUNT(*) FROM reviews"
            params = []
        # Case: filter by item_type only
        elif jlpt_level is None and item_type_str is not None:
            query = "SELECT COUNT(*) FROM reviews WHERE item_type = ?"
            params = [item_type_str]
        # Case: filter by both item_type and jlpt_level
        elif jlpt_level is not None and item_type_str is not None:
            if item_type_str == "vocab":
                query = """
                    SELECT COUNT(*) FROM reviews r
                    JOIN vocabulary v ON r.item_id = v.id
                    WHERE r.item_type = 'vocab' AND v.jlpt_level = ?
                """
            else:  # kanji
                query = """
                    SELECT COUNT(*) FROM reviews r
                    JOIN kanji k ON r.item_id = k.id
                    WHERE r.item_type = 'kanji' AND k.jlpt_level = ?
                """
            params = [jlpt_level]
        # Case: filter by jlpt_level only (need to query both vocab and kanji)
        else:  # jlpt_level is not None and item_type_str is None
            query = """
                SELECT COUNT(*) FROM (
                    SELECT r.id FROM reviews r
                    JOIN vocabulary v ON r.item_id = v.id
                    WHERE r.item_type = 'vocab' AND v.jlpt_level = ?
                    UNION ALL
                    SELECT r.id FROM reviews r
                    JOIN kanji k ON r.item_id = k.id
                    WHERE r.item_type = 'kanji' AND k.jlpt_level = ?
                )
            """
            params = [jlpt_level, jlpt_level]

        with get_cursor(self.db_path) as cursor:
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result[0] if result else 0
