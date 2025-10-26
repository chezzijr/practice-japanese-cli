"""
Pydantic models for Japanese grammar points.

Provides data validation, serialization, and database integration for grammar explanations.
"""

import json
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing_extensions import Self


class Example(BaseModel):
    """
    Model for grammar example sentences.

    Attributes:
        jp: Japanese sentence
        vi: Vietnamese translation
        en: English translation (optional)
    """

    jp: str = Field(..., min_length=1, description="Japanese sentence")
    vi: str = Field(..., min_length=1, description="Vietnamese translation")
    en: Optional[str] = Field(None, description="English translation")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return self.model_dump(exclude_none=False)


class GrammarPoint(BaseModel):
    """
    Model for Japanese grammar points with explanations and examples.

    Attributes:
        id: Database ID (None for new entries)
        title: Grammar point title (e.g., "は (wa) particle")
        structure: Grammar structure pattern (e.g., "Noun + は + Predicate")
        explanation: Vietnamese/English explanation
        jlpt_level: JLPT level (n5, n4, n3, n2, n1, or None)
        examples: List of example sentences with translations
        related_grammar: List of related grammar point IDs
        notes: User notes
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: Optional[int] = None
    title: str = Field(..., min_length=1, description="Grammar point title")
    structure: Optional[str] = Field(None, description="Grammar structure pattern")
    explanation: str = Field(..., min_length=1, description="Explanation")
    jlpt_level: Optional[str] = Field(None, description="JLPT level (n5, n4, n3, n2, n1)")
    examples: list[Example] = Field(default_factory=list, description="Example sentences")
    related_grammar: list[int] = Field(
        default_factory=list,
        description="Related grammar point IDs"
    )
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

    @model_validator(mode='after')
    def validate_has_examples(self) -> Self:
        """Ensure at least one example is provided."""
        if not self.examples or len(self.examples) == 0:
            raise ValueError('Grammar point must have at least one example')

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
    def from_db_row(cls, row: dict[str, Any]) -> 'GrammarPoint':
        """
        Create a GrammarPoint instance from a database row dictionary.

        Parses JSON fields (examples, related_grammar) from strings to Python objects.

        Args:
            row: Dictionary from database query (sqlite3.Row converted to dict)

        Returns:
            GrammarPoint: Validated grammar point instance

        Example:
            row = {"title": "は particle", "explanation": "...",
                   "examples": '[{"jp": "私は学生です", "vi": "..."}]', ...}
            grammar = GrammarPoint.from_db_row(row)
        """
        # Create a copy to avoid modifying the original
        data = row.copy()

        # Parse examples JSON field
        if 'examples' in data and isinstance(data['examples'], str):
            examples_data = json.loads(data['examples']) if data['examples'] else []
            # Convert dict examples to Example model instances
            data['examples'] = [Example(**ex) if isinstance(ex, dict) else ex
                                for ex in examples_data]

        # Parse related_grammar JSON field
        if 'related_grammar' in data and isinstance(data['related_grammar'], str):
            data['related_grammar'] = json.loads(data['related_grammar']) if data['related_grammar'] else []

        return cls.model_validate(data)

    def to_db_dict(self, exclude_id: bool = False) -> dict[str, Any]:
        """
        Convert model to dictionary for database insertion/update.

        Serializes complex fields (examples, related_grammar) to JSON strings.

        Args:
            exclude_id: If True, exclude the id field (for inserts)

        Returns:
            dict: Dictionary ready for database operations

        Example:
            grammar = GrammarPoint(title="は particle", ...)
            db_dict = grammar.to_db_dict(exclude_id=True)
            # Use with database queries
        """
        data = self.model_dump(exclude={'id'} if exclude_id else None)

        # Serialize examples to JSON
        if 'examples' in data:
            # Convert Example models to dicts
            examples_dicts = [
                ex.to_dict() if isinstance(ex, Example) else ex
                for ex in data['examples']
            ]
            data['examples'] = json.dumps(examples_dicts, ensure_ascii=False)

        # Serialize related_grammar to JSON
        if 'related_grammar' in data:
            data['related_grammar'] = json.dumps(data['related_grammar'], ensure_ascii=False)

        # Convert datetime to ISO string
        if 'created_at' in data and isinstance(data['created_at'], datetime):
            data['created_at'] = data['created_at'].isoformat()

        if 'updated_at' in data and isinstance(data['updated_at'], datetime):
            data['updated_at'] = data['updated_at'].isoformat()

        return data

    model_config = ConfigDict(
        # Pydantic v2 handles datetime serialization automatically
    )
