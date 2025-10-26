"""
Pydantic models for user progress tracking.

Provides data validation, serialization, and statistics management for learning progress.
"""

import json
from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing_extensions import Self


class ProgressStats(BaseModel):
    """
    Model for detailed progress statistics.

    Attributes:
        total_vocab: Total vocabulary words in database
        total_kanji: Total kanji characters in database
        mastered_vocab: Number of mastered vocabulary words
        mastered_kanji: Number of mastered kanji characters
        total_reviews: Total number of reviews completed
        average_retention: Average retention rate (0.0 to 1.0)
    """

    total_vocab: int = Field(default=0, ge=0, description="Total vocabulary words")
    total_kanji: int = Field(default=0, ge=0, description="Total kanji characters")
    mastered_vocab: int = Field(default=0, ge=0, description="Mastered vocabulary words")
    mastered_kanji: int = Field(default=0, ge=0, description="Mastered kanji characters")
    total_reviews: int = Field(default=0, ge=0, description="Total reviews completed")
    average_retention: float = Field(default=0.0, ge=0.0, le=1.0, description="Average retention rate")

    @model_validator(mode='after')
    def validate_mastered_not_exceeding_total(self) -> Self:
        """Ensure mastered counts don't exceed total counts."""
        if self.mastered_vocab > self.total_vocab:
            raise ValueError(f'Mastered vocab ({self.mastered_vocab}) cannot exceed total vocab ({self.total_vocab})')

        if self.mastered_kanji > self.total_kanji:
            raise ValueError(f'Mastered kanji ({self.mastered_kanji}) cannot exceed total kanji ({self.total_kanji})')

        return self

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return self.model_dump()


class Progress(BaseModel):
    """
    Model for user progress tracking and statistics.

    Attributes:
        id: Database ID (None for new entries)
        user_id: User identifier (default: 'default')
        current_level: Current JLPT level being studied
        target_level: Target JLPT level goal
        stats: Detailed progress statistics
        milestones: List of achieved milestone descriptions
        streak_days: Current study streak in days
        last_review_date: Date of last review session
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: Optional[int] = None
    user_id: str = Field(default='default', description="User identifier")
    current_level: str = Field(default='n5', description="Current JLPT level")
    target_level: str = Field(default='n5', description="Target JLPT level")
    stats: ProgressStats = Field(default_factory=ProgressStats, description="Progress statistics")
    milestones: list[str] = Field(default_factory=list, description="Achieved milestones")
    streak_days: int = Field(default=0, ge=0, description="Current study streak")
    last_review_date: Optional[date] = Field(None, description="Last review date")
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now())

    @field_validator('current_level', 'target_level')
    @classmethod
    def validate_jlpt_level(cls, v: str) -> str:
        """Validate JLPT level is one of the allowed values."""
        allowed_levels = ['n5', 'n4', 'n3', 'n2', 'n1']
        if v not in allowed_levels:
            raise ValueError(f'JLPT level must be one of {allowed_levels}, got: {v}')
        return v

    @field_validator('created_at', 'updated_at', mode='before')
    @classmethod
    def parse_datetime(cls, v: Any) -> datetime:
        """Parse datetime from string or datetime object."""
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            # Parse ISO format datetime string from SQLite
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        raise ValueError(f'Invalid datetime value: {v}')

    @field_validator('last_review_date', mode='before')
    @classmethod
    def parse_date(cls, v: Any) -> Optional[date]:
        """Parse date from string or date object."""
        if v is None:
            return None
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            # Parse ISO format date string from SQLite
            return date.fromisoformat(v)
        raise ValueError(f'Invalid date value: {v}')

    @field_validator('stats', mode='before')
    @classmethod
    def parse_stats(cls, v: Any) -> ProgressStats:
        """Parse stats from dict or ProgressStats object."""
        if isinstance(v, ProgressStats):
            return v
        if isinstance(v, dict):
            return ProgressStats(**v)
        if isinstance(v, str):
            # Parse JSON string
            stats_dict = json.loads(v)
            return ProgressStats(**stats_dict)
        raise ValueError(f'Invalid stats value: {v}')

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> 'Progress':
        """
        Create a Progress instance from a database row dictionary.

        Parses JSON fields (stats, milestones) from strings to Python objects.

        Args:
            row: Dictionary from database query (sqlite3.Row converted to dict)

        Returns:
            Progress: Validated progress instance

        Example:
            row = {"user_id": "default", "current_level": "n5",
                   "stats": '{"total_vocab": 500, ...}', ...}
            progress = Progress.from_db_row(row)
        """
        # Create a copy to avoid modifying the original
        data = row.copy()

        # Parse stats JSON field (handled by validator)
        # stats validator will handle string parsing

        # Parse milestones JSON field
        if 'milestones' in data and isinstance(data['milestones'], str):
            data['milestones'] = json.loads(data['milestones']) if data['milestones'] else []

        return cls.model_validate(data)

    def to_db_dict(self, exclude_id: bool = False) -> dict[str, Any]:
        """
        Convert model to dictionary for database insertion/update.

        Serializes complex fields (stats, milestones) to JSON strings.

        Args:
            exclude_id: If True, exclude the id field (for inserts)

        Returns:
            dict: Dictionary ready for database operations

        Example:
            progress = Progress(user_id="default", ...)
            db_dict = progress.to_db_dict(exclude_id=True)
            # Use with database queries
        """
        data = self.model_dump(exclude={'id'} if exclude_id else None)

        # Serialize stats to JSON
        if 'stats' in data:
            if isinstance(data['stats'], ProgressStats):
                data['stats'] = json.dumps(data['stats'].to_dict(), ensure_ascii=False)
            elif isinstance(data['stats'], dict):
                data['stats'] = json.dumps(data['stats'], ensure_ascii=False)

        # Serialize milestones to JSON
        if 'milestones' in data:
            data['milestones'] = json.dumps(data['milestones'], ensure_ascii=False)

        # Convert datetime to ISO string
        if 'created_at' in data and isinstance(data['created_at'], datetime):
            data['created_at'] = data['created_at'].isoformat()

        if 'updated_at' in data and isinstance(data['updated_at'], datetime):
            data['updated_at'] = data['updated_at'].isoformat()

        # Convert date to ISO string
        if 'last_review_date' in data and data['last_review_date'] is not None:
            if isinstance(data['last_review_date'], date):
                data['last_review_date'] = data['last_review_date'].isoformat()

        return data

    def increment_streak(self, review_date: date) -> None:
        """
        Update streak based on review date.

        Increments streak if reviewing on consecutive days, resets if gap > 1 day.

        Args:
            review_date: Date of the review

        Example:
            progress.increment_streak(date.today())
            # Streak updated based on last_review_date
        """
        if self.last_review_date is None:
            # First review ever
            self.streak_days = 1
        elif review_date == self.last_review_date:
            # Same day, don't increment
            pass
        elif (review_date - self.last_review_date).days == 1:
            # Next day, increment streak
            self.streak_days += 1
        elif (review_date - self.last_review_date).days > 1:
            # Gap in reviews, reset streak
            self.streak_days = 1

        self.last_review_date = review_date

    def add_milestone(self, milestone: str) -> None:
        """
        Add a new milestone to the list.

        Args:
            milestone: Description of the milestone achieved

        Example:
            progress.add_milestone("Completed 100 reviews")
        """
        if milestone not in self.milestones:
            self.milestones.append(milestone)

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat() if v else None
        }
    )
