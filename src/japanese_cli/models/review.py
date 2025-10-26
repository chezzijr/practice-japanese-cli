"""
Pydantic models for review sessions and FSRS card state.

Provides data validation, serialization, and FSRS integration for spaced repetition.
"""

import json
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from fsrs import Card, Rating
from pydantic import BaseModel, ConfigDict, Field, field_validator

class ItemType(str, Enum):
    """Type of item being reviewed."""
    VOCAB = "vocab"
    KANJI = "kanji"


class Review(BaseModel):
    """
    Model for review state tracking with FSRS integration.

    Links vocabulary or kanji items to their FSRS card state for spaced repetition.

    Attributes:
        id: Database ID (None for new entries)
        item_id: Foreign key to vocabulary.id or kanji.id
        item_type: Type of item ('vocab' or 'kanji')
        fsrs_card_state: FSRS Card state as dictionary
        due_date: Next review date
        last_reviewed: Last review timestamp
        review_count: Total number of reviews completed
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: Optional[int] = None
    item_id: int = Field(..., ge=1, description="Foreign key to vocabulary or kanji")
    item_type: ItemType = Field(..., description="Type of item (vocab or kanji)")
    fsrs_card_state: dict[str, Any] = Field(..., description="FSRS Card state dictionary")
    due_date: datetime = Field(..., description="Next review date")
    last_reviewed: Optional[datetime] = Field(None, description="Last review timestamp")
    review_count: int = Field(default=0, ge=0, description="Total reviews completed")
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now())

    @field_validator('created_at', 'updated_at', 'due_date', 'last_reviewed', mode='before')
    @classmethod
    def parse_datetime(cls, v: Any) -> Optional[datetime]:
        """Parse datetime from string or datetime object."""
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            # Parse ISO format datetime string from SQLite
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        raise ValueError(f'Invalid datetime value: {v}')

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> 'Review':
        """
        Create a Review instance from a database row dictionary.

        Parses JSON fsrs_card_state field from string to dictionary.

        Args:
            row: Dictionary from database query (sqlite3.Row converted to dict)

        Returns:
            Review: Validated review instance

        Example:
            row = {"item_id": 1, "item_type": "vocab",
                   "fsrs_card_state": '{"card_id": 123, ...}', ...}
            review = Review.from_db_row(row)
        """
        # Create a copy to avoid modifying the original
        data = row.copy()

        # Parse fsrs_card_state JSON field
        if 'fsrs_card_state' in data and isinstance(data['fsrs_card_state'], str):
            data['fsrs_card_state'] = json.loads(data['fsrs_card_state'])

        return cls.model_validate(data)

    def to_db_dict(self, exclude_id: bool = False) -> dict[str, Any]:
        """
        Convert model to dictionary for database insertion/update.

        Serializes fsrs_card_state to JSON string.

        Args:
            exclude_id: If True, exclude the id field (for inserts)

        Returns:
            dict: Dictionary ready for database operations

        Example:
            review = Review(item_id=1, item_type=ItemType.VOCAB, ...)
            db_dict = review.to_db_dict(exclude_id=True)
            # Use with database queries
        """
        data = self.model_dump(exclude={'id'} if exclude_id else None)

        # Convert enum to string
        if 'item_type' in data and isinstance(data['item_type'], ItemType):
            data['item_type'] = data['item_type'].value

        # Serialize fsrs_card_state to JSON
        if 'fsrs_card_state' in data and isinstance(data['fsrs_card_state'], dict):
            data['fsrs_card_state'] = json.dumps(data['fsrs_card_state'], ensure_ascii=False)

        # Convert datetime to ISO string
        for field in ['created_at', 'updated_at', 'due_date', 'last_reviewed']:
            if field in data and data[field] is not None and isinstance(data[field], datetime):
                data[field] = data[field].isoformat()

        return data

    def get_card(self) -> Card:
        """
        Reconstruct FSRS Card object from stored state.

        Returns:
            Card: FSRS Card instance

        Example:
            review = Review.from_db_row(row)
            card = review.get_card()
            # Use card with FSRS scheduler
        """
        return Card.from_dict(self.fsrs_card_state)

    def update_from_card(self, card: Card) -> None:
        """
        Update review state from FSRS Card object.

        Updates fsrs_card_state and due_date from the card.

        Args:
            card: FSRS Card instance after review

        Example:
            card, review_log = scheduler.review_card(card, Rating.Good)
            review.update_from_card(card)
            # review.fsrs_card_state and review.due_date are now updated
        """
        self.fsrs_card_state = card.to_dict()
        # Extract due date from card state
        if 'due' in self.fsrs_card_state:
            due_str = self.fsrs_card_state['due']
            self.due_date = datetime.fromisoformat(due_str.replace('Z', '+00:00'))

    @classmethod
    def create_new(cls, item_id: int, item_type: ItemType) -> 'Review':
        """
        Create a new review with fresh FSRS card state.

        Args:
            item_id: ID of vocabulary or kanji item
            item_type: Type of item (vocab or kanji)

        Returns:
            Review: New review instance with initial FSRS state

        Example:
            review = Review.create_new(item_id=1, item_type=ItemType.VOCAB)
            # review has a new FSRS card ready for first review
        """
        card = Card()
        card_state = card.to_dict()

        # Extract due date
        due_str = card_state['due']
        due_date = datetime.fromisoformat(due_str.replace('Z', '+00:00'))

        return cls(
            item_id=item_id,
            item_type=item_type,
            fsrs_card_state=card_state,
            due_date=due_date,
            last_reviewed=None,
            review_count=0
        )

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat() if v else None}
    )


class ReviewHistory(BaseModel):
    """
    Model for individual review history entries.

    Records each review session for analytics and progress tracking.

    Attributes:
        id: Database ID (None for new entries)
        review_id: Foreign key to reviews.id
        rating: FSRS rating (1=Again, 2=Hard, 3=Good, 4=Easy)
        duration_ms: Time spent reviewing in milliseconds
        reviewed_at: When the review occurred
    """

    id: Optional[int] = None
    review_id: int = Field(..., ge=1, description="Foreign key to reviews table")
    rating: int = Field(..., ge=1, le=4, description="FSRS rating (1-4)")
    duration_ms: Optional[int] = Field(None, ge=0, description="Review duration in milliseconds")
    reviewed_at: datetime = Field(default_factory=lambda: datetime.now())

    @field_validator('reviewed_at', mode='before')
    @classmethod
    def parse_datetime(cls, v: Any) -> datetime:
        """Parse datetime from string or datetime object."""
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            # Parse ISO format datetime string from SQLite
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        raise ValueError(f'Invalid datetime value: {v}')

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> 'ReviewHistory':
        """
        Create a ReviewHistory instance from a database row dictionary.

        Args:
            row: Dictionary from database query (sqlite3.Row converted to dict)

        Returns:
            ReviewHistory: Validated review history instance
        """
        return cls.model_validate(row)

    def to_db_dict(self, exclude_id: bool = False) -> dict[str, Any]:
        """
        Convert model to dictionary for database insertion/update.

        Args:
            exclude_id: If True, exclude the id field (for inserts)

        Returns:
            dict: Dictionary ready for database operations
        """
        data = self.model_dump(exclude={'id'} if exclude_id else None)

        # Convert datetime to ISO string
        if 'reviewed_at' in data and isinstance(data['reviewed_at'], datetime):
            data['reviewed_at'] = data['reviewed_at'].isoformat()

        return data

    def get_rating_enum(self) -> Rating:
        """
        Convert integer rating to FSRS Rating enum.

        Returns:
            Rating: FSRS Rating enum value

        Example:
            history = ReviewHistory(rating=3, ...)
            rating = history.get_rating_enum()  # Rating.Good
        """
        rating_map = {
            1: Rating.Again,
            2: Rating.Hard,
            3: Rating.Good,
            4: Rating.Easy
        }
        return rating_map[self.rating]

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )
