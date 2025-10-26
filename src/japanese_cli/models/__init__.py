"""
Pydantic data models for Japanese Learning CLI.

This module provides validated data models for all entities in the application:
- Vocabulary: Japanese words with readings and meanings
- Kanji: Kanji characters with on/kun readings
- GrammarPoint: Grammar explanations with examples
- Review: FSRS card state for spaced repetition
- Progress: User progress tracking and statistics

All models provide:
- Pydantic v2 validation
- JSON serialization/deserialization
- Database row conversion (from_db_row, to_db_dict)
"""

# Vocabulary models
from .vocabulary import Vocabulary

# Kanji models
from .kanji import Kanji

# Grammar models
from .grammar import Example, GrammarPoint

# Review models
from .review import ItemType, Review, ReviewHistory

# Progress models
from .progress import Progress, ProgressStats

__all__ = [
    # Vocabulary
    "Vocabulary",
    # Kanji
    "Kanji",
    # Grammar
    "Example",
    "GrammarPoint",
    # Review
    "ItemType",
    "Review",
    "ReviewHistory",
    # Progress
    "Progress",
    "ProgressStats",
]

__version__ = "0.1.0"
