"""
Pydantic models for Japanese kanji characters.

Provides data validation, serialization, and database integration for kanji.
"""

import json
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing_extensions import Self


class Kanji(BaseModel):
    """
    Model for Japanese kanji characters with readings and meanings.

    Attributes:
        id: Database ID (None for new entries)
        character: Single kanji character (e.g., "語")
        on_readings: List of on-yomi readings (e.g., ["ゴ"])
        kun_readings: List of kun-yomi readings (e.g., ["かた.る", "かた.らう"])
        meanings: Dictionary of meanings by language {"vi": [...], "en": [...]}
        vietnamese_reading: Hán Việt reading (e.g., "ngữ")
        jlpt_level: JLPT level (n5, n4, n3, n2, n1, or None)
        stroke_count: Number of strokes
        radical: Radical character
        notes: User notes
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: Optional[int] = None
    character: str = Field(..., min_length=1, max_length=1, description="Single kanji character")
    on_readings: list[str] = Field(default_factory=list, description="On-yomi readings")
    kun_readings: list[str] = Field(default_factory=list, description="Kun-yomi readings")
    meanings: dict[str, list[str]] = Field(
        ...,
        description="Meanings by language code (e.g., {'vi': [...], 'en': [...]})"
    )
    vietnamese_reading: Optional[str] = Field(None, description="Hán Việt reading")
    jlpt_level: Optional[str] = Field(None, description="JLPT level (n5, n4, n3, n2, n1)")
    stroke_count: Optional[int] = Field(None, ge=1, description="Number of strokes")
    radical: Optional[str] = Field(None, description="Radical character")
    notes: Optional[str] = Field(None, description="User notes")
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now())

    @field_validator('jlpt_level')
    @classmethod
    def validate_jlpt_level(cls, v: Optional[str]) -> Optional[str]:
        """Validate JLPT level is one of the allowed values."""
        if v is None:
            return v

        allowed_levels = ['n5', 'n4', 'n3', 'n2', 'n1']
        if v not in allowed_levels:
            raise ValueError(f'JLPT level must be one of {allowed_levels}, got: {v}')

        return v

    @field_validator('character')
    @classmethod
    def validate_kanji_character(cls, v: str) -> str:
        """Ensure character is a single valid kanji."""
        # Import here to avoid circular imports
        import sys
        if 'japanese_cli.ui.japanese_utils' in sys.modules:
            from japanese_cli.ui.japanese_utils import is_kanji, is_hiragana, is_katakana, is_romaji
        else:
            # If utils not loaded yet, just check length (during import time)
            if len(v) != 1:
                raise ValueError('Character must be exactly one character')
            return v

        # Already validated by Field(..., min_length=1, max_length=1) but double-check
        if len(v) != 1:
            raise ValueError('Character must be exactly one character')

        if is_romaji(v):
            raise ValueError(
                f'Character must be a kanji character, not romaji. '
                f'Received: "{v}"'
            )

        if is_hiragana(v):
            raise ValueError(
                f'Character must be a kanji character, not hiragana. '
                f'Received: "{v}"'
            )

        if is_katakana(v):
            raise ValueError(
                f'Character must be a kanji character, not katakana. '
                f'Received: "{v}"'
            )

        if not is_kanji(v):
            raise ValueError(
                f'Character must be a valid kanji character. '
                f'Received: "{v}"'
            )

        return v

    @model_validator(mode='after')
    def validate_readings_or_meanings(self) -> Self:
        """Ensure kanji has at least one reading or meaning."""
        has_reading = len(self.on_readings) > 0 or len(self.kun_readings) > 0
        has_meaning = any(
            meanings_list and len(meanings_list) > 0
            for meanings_list in self.meanings.values()
        )

        if not has_reading and not has_meaning:
            raise ValueError('Kanji must have at least one reading or one meaning')

        return self

    @model_validator(mode='after')
    def validate_meanings_not_empty(self) -> Self:
        """Ensure meanings dictionary is not empty."""
        if not self.meanings:
            raise ValueError('Meanings dictionary cannot be empty')

        return self

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

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> 'Kanji':
        """
        Create a Kanji instance from a database row dictionary.

        Parses JSON fields (on_readings, kun_readings, meanings) from strings to Python objects.

        Args:
            row: Dictionary from database query (sqlite3.Row converted to dict)

        Returns:
            Kanji: Validated kanji instance

        Example:
            row = {"character": "語", "on_readings": '["ゴ"]',
                   "meanings": '{"vi": ["ngữ"]}', ...}
            kanji = Kanji.from_db_row(row)
        """
        # Create a copy to avoid modifying the original
        data = row.copy()

        # Parse JSON fields
        if 'on_readings' in data and isinstance(data['on_readings'], str):
            data['on_readings'] = json.loads(data['on_readings']) if data['on_readings'] else []

        if 'kun_readings' in data and isinstance(data['kun_readings'], str):
            data['kun_readings'] = json.loads(data['kun_readings']) if data['kun_readings'] else []

        if 'meanings' in data and isinstance(data['meanings'], str):
            data['meanings'] = json.loads(data['meanings'])

        return cls.model_validate(data)

    def to_db_dict(self, exclude_id: bool = False) -> dict[str, Any]:
        """
        Convert model to dictionary for database insertion/update.

        Serializes complex fields (on_readings, kun_readings, meanings) to JSON strings.

        Args:
            exclude_id: If True, exclude the id field (for inserts)

        Returns:
            dict: Dictionary ready for database operations

        Example:
            kanji = Kanji(character="語", on_readings=["ゴ"], ...)
            db_dict = kanji.to_db_dict(exclude_id=True)
            # Use with database queries
        """
        data = self.model_dump(exclude={'id'} if exclude_id else None)

        # Serialize JSON fields
        if 'on_readings' in data:
            data['on_readings'] = json.dumps(data['on_readings'], ensure_ascii=False)

        if 'kun_readings' in data:
            data['kun_readings'] = json.dumps(data['kun_readings'], ensure_ascii=False)

        if 'meanings' in data:
            data['meanings'] = json.dumps(data['meanings'], ensure_ascii=False)

        # Convert datetime to ISO string
        if 'created_at' in data and isinstance(data['created_at'], datetime):
            data['created_at'] = data['created_at'].isoformat()

        if 'updated_at' in data and isinstance(data['updated_at'], datetime):
            data['updated_at'] = data['updated_at'].isoformat()

        return data

    model_config = ConfigDict(
        # Pydantic v2 handles datetime serialization automatically
    )
