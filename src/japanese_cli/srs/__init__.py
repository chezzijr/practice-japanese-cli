"""
SRS (Spaced Repetition System) module for Japanese Learning CLI.

Provides high-level interfaces for managing flashcard reviews with FSRS algorithm.
"""

from .fsrs import FSRSManager
from .mcq_scheduler import MCQReviewScheduler
from .scheduler import ReviewScheduler
from .statistics import (
    MASTERY_STABILITY_THRESHOLD,
    aggregate_daily_review_counts,
    calculate_average_review_duration,
    calculate_kanji_counts_by_level,
    calculate_mastered_items,
    calculate_retention_rate,
    calculate_vocab_counts_by_level,
    get_mcq_accuracy_rate,
    get_mcq_option_distribution,
    get_mcq_stats_by_type,
    get_most_reviewed_items,
    get_reviews_by_date_range,
)

__all__ = [
    "FSRSManager",
    "ReviewScheduler",
    "MCQReviewScheduler",
    # Statistics
    "MASTERY_STABILITY_THRESHOLD",
    "calculate_vocab_counts_by_level",
    "calculate_kanji_counts_by_level",
    "calculate_mastered_items",
    "calculate_retention_rate",
    "get_most_reviewed_items",
    "get_reviews_by_date_range",
    "aggregate_daily_review_counts",
    "calculate_average_review_duration",
    # MCQ Statistics
    "get_mcq_accuracy_rate",
    "get_mcq_stats_by_type",
    "get_mcq_option_distribution",
]
