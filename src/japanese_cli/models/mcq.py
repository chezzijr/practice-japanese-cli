"""
Pydantic models for multiple-choice question (MCQ) reviews.

Provides data validation, serialization, and FSRS integration for MCQ-based learning.
"""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from fsrs import Card
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .review import ItemType


@dataclass
class MCQQuestion:
    """
    Runtime representation of a generated multiple-choice question.

    This is not stored in the database - it's generated dynamically during review sessions.

    Attributes:
        item_id: ID of the vocabulary or kanji item
        item_type: Type of item (vocab or kanji)
        question_text: The question to display (e.g., Vietnamese/English meaning)
        options: List of 4 answer choices (Japanese words/kanji)
        correct_index: Index of the correct answer in options (0-3)
        jlpt_level: JLPT level of the item (for filtering)
        explanation: Optional explanation of the answer
    """

    item_id: int
    item_type: ItemType
    question_text: str
    options: list[str]
    correct_index: int
    jlpt_level: Optional[str] = None
    explanation: Optional[str] = None

    def __post_init__(self):
        """Validate question structure."""
        if len(self.options) != 4:
            raise ValueError(f"MCQ must have exactly 4 options, got {len(self.options)}")
        if not 0 <= self.correct_index < 4:
            raise ValueError(f"correct_index must be 0-3, got {self.correct_index}")

    def is_correct(self, selected_index: int) -> bool:
        """
        Check if the selected answer is correct.

        Args:
            selected_index: Index of the selected option (0-3)

        Returns:
            bool: True if correct, False otherwise
        """
        return selected_index == self.correct_index

    def get_correct_answer(self) -> str:
        """Get the correct answer text."""
        return self.options[self.correct_index]


class MCQReview(BaseModel):
    """
    Model for MCQ review state tracking with FSRS integration.

    Tracks MCQ review state separately from flashcard reviews.

    Attributes:
        id: Database ID (None for new entries)
        item_id: Foreign key to vocabulary.id or kanji.id
        item_type: Type of item ('vocab' or 'kanji')
        fsrs_card_state: FSRS Card state as dictionary
        due_date: Next review date
        last_reviewed: Last review timestamp
        review_count: Total number of MCQ reviews completed
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: Optional[int] = None
    item_id: int = Field(..., ge=1, description="Foreign key to vocabulary or kanji")
    item_type: ItemType = Field(..., description="Type of item (vocab or kanji)")
    fsrs_card_state: dict[str, Any] = Field(..., description="FSRS Card state dictionary")
    due_date: datetime = Field(..., description="Next review date")
    last_reviewed: Optional[datetime] = Field(None, description="Last review timestamp")
    review_count: int = Field(default=0, ge=0, description="Total MCQ reviews completed")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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
    def from_db_row(cls, row: dict[str, Any]) -> 'MCQReview':
        """
        Create an MCQReview instance from a database row dictionary.

        Parses JSON fsrs_card_state field from string to dictionary.

        Args:
            row: Dictionary from database query (sqlite3.Row converted to dict)

        Returns:
            MCQReview: Validated MCQ review instance

        Example:
            row = {"item_id": 1, "item_type": "vocab",
                   "fsrs_card_state": '{"card_id": 123, ...}', ...}
            mcq_review = MCQReview.from_db_row(row)
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
            mcq_review = MCQReview(item_id=1, item_type=ItemType.VOCAB, ...)
            db_dict = mcq_review.to_db_dict(exclude_id=True)
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
            mcq_review = MCQReview.from_db_row(row)
            card = mcq_review.get_card()
            # Use card with FSRS scheduler
        """
        return Card.from_dict(self.fsrs_card_state)

    def update_from_card(self, card: Card) -> None:
        """
        Update MCQ review state from FSRS Card object.

        Updates fsrs_card_state and due_date from the card.

        Args:
            card: FSRS Card instance after review

        Example:
            card, review_log = scheduler.review_card(card, Rating.Good)
            mcq_review.update_from_card(card)
            # mcq_review.fsrs_card_state and mcq_review.due_date are now updated
        """
        self.fsrs_card_state = card.to_dict()
        # Extract due date from card state
        if 'due' in self.fsrs_card_state:
            due_str = self.fsrs_card_state['due']
            self.due_date = datetime.fromisoformat(due_str.replace('Z', '+00:00'))

    @classmethod
    def create_new(cls, item_id: int, item_type: ItemType) -> 'MCQReview':
        """
        Create a new MCQ review with fresh FSRS card state.

        Args:
            item_id: ID of vocabulary or kanji item
            item_type: Type of item (vocab or kanji)

        Returns:
            MCQReview: New MCQ review instance with initial FSRS state

        Example:
            mcq_review = MCQReview.create_new(item_id=1, item_type=ItemType.VOCAB)
            # mcq_review has a new FSRS card ready for first MCQ review
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
        # Pydantic v2 handles datetime serialization automatically
    )


class MCQReviewHistory(BaseModel):
    """
    Model for individual MCQ review history entries.

    Records each MCQ review session for analytics and progress tracking.

    Attributes:
        id: Database ID (None for new entries)
        mcq_review_id: Foreign key to mcq_reviews.id
        selected_option: Index of the option selected by user (0-3)
        is_correct: Whether the selection was correct (True/False)
        duration_ms: Time spent on question in milliseconds
        reviewed_at: When the review occurred
    """

    id: Optional[int] = None
    mcq_review_id: int = Field(..., ge=1, description="Foreign key to mcq_reviews table")
    selected_option: int = Field(..., ge=0, le=3, description="Selected option index (0-3)")
    is_correct: bool = Field(..., description="Whether the answer was correct")
    duration_ms: Optional[int] = Field(None, ge=0, description="Question duration in milliseconds")
    reviewed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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
    def from_db_row(cls, row: dict[str, Any]) -> 'MCQReviewHistory':
        """
        Create an MCQReviewHistory instance from a database row dictionary.

        Args:
            row: Dictionary from database query (sqlite3.Row converted to dict)

        Returns:
            MCQReviewHistory: Validated MCQ review history instance
        """
        data = row.copy()

        # Convert SQLite integer (0/1) to boolean if needed
        if 'is_correct' in data and isinstance(data['is_correct'], int):
            data['is_correct'] = bool(data['is_correct'])

        return cls.model_validate(data)

    def to_db_dict(self, exclude_id: bool = False) -> dict[str, Any]:
        """
        Convert model to dictionary for database insertion/update.

        Args:
            exclude_id: If True, exclude the id field (for inserts)

        Returns:
            dict: Dictionary ready for database operations
        """
        data = self.model_dump(exclude={'id'} if exclude_id else None)

        # Convert boolean to integer for SQLite
        if 'is_correct' in data and isinstance(data['is_correct'], bool):
            data['is_correct'] = int(data['is_correct'])

        # Convert datetime to ISO string
        if 'reviewed_at' in data and isinstance(data['reviewed_at'], datetime):
            data['reviewed_at'] = data['reviewed_at'].isoformat()

        return data

    model_config = ConfigDict(
        # Pydantic v2 handles datetime serialization automatically
    )
