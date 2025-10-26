"""
SRS (Spaced Repetition System) module for Japanese Learning CLI.

Provides high-level interfaces for managing flashcard reviews with FSRS algorithm.
"""

from .fsrs import FSRSManager
from .scheduler import ReviewScheduler

__all__ = [
    "FSRSManager",
    "ReviewScheduler",
]
