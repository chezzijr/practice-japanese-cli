"""
Pydantic models for Japanese vocabulary entries.

Provides data validation, serialization, and database integration for vocabulary words.
"""

import json
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing_extensions import Self


class Vocabulary(BaseModel):
    """
    Model for Japanese vocabulary words with readings and meanings.

    Attributes:
        id: Database ID (None for new entries)
        word: Japanese word in kanji/kana (e.g., "単語")
        reading: Reading in hiragana/katakana (e.g., "たんご")
        meanings: Dictionary of meanings by language {"vi": [...], "en": [...]}
        vietnamese_reading: Optional Sino-Vietnamese reading (e.g., "đơn ngữ")
        jlpt_level: JLPT level (n5, n4, n3, n2, n1, or None)
        part_of_speech: Part of speech (noun, verb, adjective, etc.)
        tags: List of tags for categorization
        notes: User notes
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: Optional[int] = None
    word: str = Field(..., min_length=1, description="Japanese word in kanji/kana")
    reading: str = Field(..., min_length=1, description="Reading in hiragana/katakana")
    meanings: dict[str, list[str]] = Field(
        ...,
        description="Meanings by language code (e.g., {'vi': [...], 'en': [...]})"
    )
    vietnamese_reading: Optional[str] = Field(None, description="Sino-Vietnamese reading")
    jlpt_level: Optional[str] = Field(None, description="JLPT level (n5, n4, n3, n2, n1)")
    part_of_speech: Optional[str] = Field(None, description="Part of speech")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
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

    @field_validator('word', 'reading')
    @classmethod
    def validate_japanese_characters(cls, v: str, info) -> str:
        """Ensure word and reading contain Japanese characters, not romaji."""
        # Import here to avoid circular imports
        import sys
        if 'japanese_cli.ui.japanese_utils' in sys.modules:
            from japanese_cli.ui.japanese_utils import contains_japanese, is_romaji
        else:
            # If utils not loaded yet, skip validation (during import time)
            return v

        field_name = info.field_name.capitalize()

        if is_romaji(v):
            raise ValueError(
                f'{field_name} must be in Japanese characters (hiragana, katakana, or kanji), not romaji. '
                f'Received: "{v}"'
            )

        if not contains_japanese(v):
            raise ValueError(
                f'{field_name} must contain Japanese characters. '
                f'Received: "{v}"'
            )

        return v

    @model_validator(mode='after')
    def validate_meanings_not_empty(self) -> Self:
        """Ensure at least one language has at least one meaning."""
        if not self.meanings:
            raise ValueError('Meanings dictionary cannot be empty')

        # Check that at least one language has at least one meaning
        has_meaning = any(
            meanings_list and len(meanings_list) > 0
            for meanings_list in self.meanings.values()
        )

        if not has_meaning:
            raise ValueError('At least one language must have at least one meaning')

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
    def from_db_row(cls, row: dict[str, Any]) -> 'Vocabulary':
        """
        Create a Vocabulary instance from a database row dictionary.

        Parses JSON fields (meanings, tags) from strings to Python objects.

        Args:
            row: Dictionary from database query (sqlite3.Row converted to dict)

        Returns:
            Vocabulary: Validated vocabulary instance

        Example:
            row = {"word": "単語", "reading": "たんご",
                   "meanings": '{"vi": ["từ vựng"]}', ...}
            vocab = Vocabulary.from_db_row(row)
        """
        # Create a copy to avoid modifying the original
        data = row.copy()

        # Parse JSON fields
        if 'meanings' in data and isinstance(data['meanings'], str):
            data['meanings'] = json.loads(data['meanings'])

        if 'tags' in data and isinstance(data['tags'], str):
            data['tags'] = json.loads(data['tags']) if data['tags'] else []

        return cls.model_validate(data)

    def to_db_dict(self, exclude_id: bool = False) -> dict[str, Any]:
        """
        Convert model to dictionary for database insertion/update.

        Serializes complex fields (meanings, tags) to JSON strings.

        Args:
            exclude_id: If True, exclude the id field (for inserts)

        Returns:
            dict: Dictionary ready for database operations

        Example:
            vocab = Vocabulary(word="単語", reading="たんご", ...)
            db_dict = vocab.to_db_dict(exclude_id=True)
            # Use with database queries
        """
        data = self.model_dump(exclude={'id'} if exclude_id else None)

        # Serialize JSON fields
        if 'meanings' in data:
            data['meanings'] = json.dumps(data['meanings'], ensure_ascii=False)

        if 'tags' in data:
            data['tags'] = json.dumps(data['tags'], ensure_ascii=False)

        # Convert datetime to ISO string
        if 'created_at' in data and isinstance(data['created_at'], datetime):
            data['created_at'] = data['created_at'].isoformat()

        if 'updated_at' in data and isinstance(data['updated_at'], datetime):
            data['updated_at'] = data['updated_at'].isoformat()

        return data

    model_config = ConfigDict(
        # Pydantic v2 handles datetime serialization automatically
    )
