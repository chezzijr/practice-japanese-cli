"""
FSRS wrapper for Japanese Learning CLI.

Provides a clean interface to the FSRS spaced repetition library with configurable
parameters and convenient utility methods.
"""

from datetime import datetime, timedelta
from typing import Optional

from fsrs import Card, Rating, ReviewLog, Scheduler


class FSRSManager:
    """
    Wrapper around the FSRS Scheduler for spaced repetition.

    Provides convenient methods for creating cards, scheduling reviews, and
    converting between rating formats. Encapsulates FSRS configuration.

    Attributes:
        scheduler: The FSRS Scheduler instance
        desired_retention: Target retention rate (0.0-1.0)
        learning_steps: Steps for learning phase
        relearning_steps: Steps for relearning phase
        maximum_interval: Maximum interval in days
        enable_fuzzing: Whether to add randomness to intervals

    Example:
        manager = FSRSManager()
        card = manager.create_new_card()
        card, log = manager.review_card(card, 3)  # Rating.Good
    """

    def __init__(
        self,
        desired_retention: float = 0.9,
        learning_steps: Optional[tuple[timedelta, ...]] = None,
        relearning_steps: Optional[tuple[timedelta, ...]] = None,
        maximum_interval: int = 36500,
        enable_fuzzing: bool = True,
    ):
        """
        Initialize FSRS manager with configuration.

        Args:
            desired_retention: Target retention rate (default 0.9 = 90%)
            learning_steps: Learning phase intervals (default: 1min, 10min)
            relearning_steps: Relearning phase intervals (default: 10min)
            maximum_interval: Maximum interval in days (default: 36500 = 100 years)
            enable_fuzzing: Add randomness to intervals (default: True)

        Example:
            # Use defaults
            manager = FSRSManager()

            # Custom retention
            manager = FSRSManager(desired_retention=0.95)

            # Custom learning steps
            from datetime import timedelta
            manager = FSRSManager(
                learning_steps=(timedelta(minutes=5), timedelta(hours=1))
            )
        """
        # Store configuration
        self.desired_retention = desired_retention
        self.learning_steps = learning_steps or (
            timedelta(minutes=1),
            timedelta(minutes=10),
        )
        self.relearning_steps = relearning_steps or (timedelta(minutes=10),)
        self.maximum_interval = maximum_interval
        self.enable_fuzzing = enable_fuzzing

        # Create scheduler with configuration
        self.scheduler = Scheduler(
            desired_retention=desired_retention,
            learning_steps=self.learning_steps,
            relearning_steps=self.relearning_steps,
            maximum_interval=maximum_interval,
            enable_fuzzing=enable_fuzzing,
        )

    def create_new_card(self) -> Card:
        """
        Create a new FSRS card with initial state.

        Returns:
            Card: A new FSRS card ready for first review

        Example:
            card = manager.create_new_card()
            # Card is in Learning state, due immediately
        """
        return Card()

    def review_card(
        self, card: Card, rating: int | Rating
    ) -> tuple[Card, ReviewLog]:
        """
        Process a review and update card state.

        Args:
            card: The FSRS card to review
            rating: Rating (1-4 or Rating enum)
                - 1 / Rating.Again: Forgot, review soon
                - 2 / Rating.Hard: Difficult, shorter interval
                - 3 / Rating.Good: Correct, normal interval
                - 4 / Rating.Easy: Very easy, longer interval

        Returns:
            tuple[Card, ReviewLog]: Updated card and review log

        Raises:
            ValueError: If rating is not 1-4 or valid Rating enum

        Example:
            card, log = manager.review_card(card, 3)
            card, log = manager.review_card(card, Rating.Good)
        """
        # Convert int to Rating enum if needed
        if isinstance(rating, int):
            rating_enum = self.rating_from_int(rating)
        else:
            rating_enum = rating

        # Use FSRS scheduler to process review
        return self.scheduler.review_card(card, rating_enum)

    @staticmethod
    def rating_from_int(rating: int) -> Rating:
        """
        Convert integer rating (1-4) to FSRS Rating enum.

        Args:
            rating: Integer rating (1=Again, 2=Hard, 3=Good, 4=Easy)

        Returns:
            Rating: FSRS Rating enum value

        Raises:
            ValueError: If rating is not 1, 2, 3, or 4

        Example:
            rating = FSRSManager.rating_from_int(3)  # Rating.Good
        """
        rating_map = {
            1: Rating.Again,
            2: Rating.Hard,
            3: Rating.Good,
            4: Rating.Easy,
        }

        if rating not in rating_map:
            raise ValueError(
                f"Rating must be 1-4, got {rating}. "
                "1=Again, 2=Hard, 3=Good, 4=Easy"
            )

        return rating_map[rating]

    @staticmethod
    def rating_to_int(rating: Rating) -> int:
        """
        Convert FSRS Rating enum to integer (1-4).

        Args:
            rating: FSRS Rating enum value

        Returns:
            int: Integer rating (1=Again, 2=Hard, 3=Good, 4=Easy)

        Example:
            rating_int = FSRSManager.rating_to_int(Rating.Good)  # 3
        """
        rating_map = {
            Rating.Again: 1,
            Rating.Hard: 2,
            Rating.Good: 3,
            Rating.Easy: 4,
        }
        return rating_map[rating]

    @staticmethod
    def get_due_date(card: Card) -> datetime:
        """
        Extract due date from FSRS card.

        Args:
            card: FSRS Card instance

        Returns:
            datetime: When the card is due for review

        Example:
            card = manager.create_new_card()
            due = manager.get_due_date(card)
        """
        return card.due

    def is_card_due(self, card: Card, now: Optional[datetime] = None) -> bool:
        """
        Check if a card is currently due for review.

        Args:
            card: FSRS Card instance
            now: Current time (default: datetime.now(timezone.utc))

        Returns:
            bool: True if card is due, False otherwise

        Example:
            if manager.is_card_due(card):
                # Present card for review
        """
        if now is None:
            from datetime import timezone
            now = datetime.now(timezone.utc)

        return card.due <= now
