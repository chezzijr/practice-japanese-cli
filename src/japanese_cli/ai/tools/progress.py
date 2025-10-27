"""Progress and statistics tools for the AI agent."""

import json
from datetime import date, timedelta
from typing import Optional

from strands import tool

from japanese_cli.database.queries import get_progress
from japanese_cli.srs.statistics import (
    calculate_vocab_counts_by_level,
    calculate_kanji_counts_by_level,
    calculate_mastered_items,
    calculate_retention_rate,
    get_reviews_by_date_range,
    aggregate_daily_review_counts,
    calculate_average_review_duration,
    get_mcq_accuracy_rate,
)


@tool
def get_progress_stats(
    user_id: str = "default",
    include_detailed_stats: bool = True,
    date_range_days: int = 7
) -> dict:
    """
    Get comprehensive learning progress and statistics for the user.

    This tool provides an overview of the user's Japanese learning journey, including:
    - Current and target JLPT levels
    - Vocabulary and kanji counts by level
    - Mastered items counts
    - Review statistics and retention rates
    - Study streak information
    - Recent activity and performance metrics

    Args:
        user_id: User ID to get progress for (default: "default")
        include_detailed_stats: Include detailed statistics like retention rate,
                                review counts, and activity (default: True)
        date_range_days: Number of days to look back for activity stats (default: 7)

    Returns:
        Dict containing comprehensive progress information including:
        - Basic progress (current/target level, streak)
        - Vocabulary and kanji counts by JLPT level
        - Mastered items statistics
        - Recent review activity
        - Retention rates and performance metrics
        - MCQ (Multiple Choice Questions) accuracy

    Examples:
        - get_progress_stats()  # Get full progress overview
        - get_progress_stats(include_detailed_stats=False)  # Basic overview only
        - get_progress_stats(date_range_days=30)  # Last 30 days activity
    """
    try:
        # Get basic progress data
        progress = get_progress(user_id=user_id)

        if not progress:
            return {
                "status": "success",
                "content": [{
                    "text": (
                        "No progress data found. This is a new user. "
                        "Progress tracking will begin after importing vocabulary/kanji "
                        "or starting reviews."
                    )
                }]
            }

        # Parse stats JSON
        try:
            stats = json.loads(progress["stats"])
        except (json.JSONDecodeError, KeyError):
            stats = {}

        # Build basic progress summary
        result_text = "# Learning Progress Overview\n\n"
        result_text += f"**Current Level**: {progress.get('current_level', 'N/A').upper()}\n"
        result_text += f"**Target Level**: {progress.get('target_level', 'N/A').upper()}\n"
        result_text += f"**Study Streak**: {progress.get('streak_days', 0)} days\n"
        result_text += f"**Last Review**: {progress.get('last_review_date', 'Never')}\n\n"

        # Get counts by level
        vocab_counts = calculate_vocab_counts_by_level()
        kanji_counts = calculate_kanji_counts_by_level()

        result_text += "## Vocabulary & Kanji by Level\n"
        for level in ["n5", "n4", "n3", "n2", "n1"]:
            v_count = vocab_counts.get(level, 0)
            k_count = kanji_counts.get(level, 0)
            result_text += f"- **{level.upper()}**: {v_count} vocab, {k_count} kanji\n"

        result_text += f"\n**Total**: {sum(vocab_counts.values())} vocabulary, {sum(kanji_counts.values())} kanji\n\n"

        # Get mastered items
        mastered = calculate_mastered_items()
        result_text += "## Mastered Items\n"
        result_text += f"- **Vocabulary**: {mastered['vocab']} mastered\n"
        result_text += f"- **Kanji**: {mastered['kanji']} mastered\n"
        result_text += f"- **Total**: {mastered['total']} items mastered\n\n"

        # Include detailed stats if requested
        if include_detailed_stats:
            # Retention rate (overall)
            retention_rate = calculate_retention_rate()
            if retention_rate > 0:
                result_text += "## Performance Metrics\n"
                result_text += f"- **Overall Retention Rate**: {retention_rate:.1f}%\n\n"

            # Recent activity
            end_date = date.today()
            start_date = end_date - timedelta(days=date_range_days - 1)
            recent_reviews = get_reviews_by_date_range(
                start_date=start_date,
                end_date=end_date
            )

            if recent_reviews:
                daily_counts = aggregate_daily_review_counts(
                    start_date=start_date,
                    end_date=end_date
                )
                total_recent = sum(daily_counts.values())
                result_text += f"## Recent Activity (Last {date_range_days} Days)\n"
                result_text += f"- **Total Reviews**: {total_recent}\n"
                result_text += f"- **Average per Day**: {total_recent / date_range_days:.1f}\n"

                # Average duration
                avg_duration_seconds = calculate_average_review_duration(
                    start_date=start_date,
                    end_date=end_date
                )
                if avg_duration_seconds > 0:
                    result_text += f"- **Avg Review Time**: {avg_duration_seconds:.1f} seconds\n"
                result_text += "\n"

            # MCQ accuracy
            mcq_accuracy = get_mcq_accuracy_rate()
            if mcq_accuracy > 0:
                result_text += f"## Multiple Choice Quiz Performance\n"
                result_text += f"- **Overall Accuracy**: {mcq_accuracy:.1%}\n\n"

        # Summary message
        result_text += "---\n\n"
        streak_msg = ""
        if progress.get('streak_days', 0) >= 7:
            streak_msg = f"🎉 Great job maintaining your {progress['streak_days']}-day streak! "
        elif progress.get('streak_days', 0) > 0:
            streak_msg = f"Keep it up! You have a {progress['streak_days']}-day streak going. "

        mastered_pct = 0
        total_items = sum(vocab_counts.values()) + sum(kanji_counts.values())
        if total_items > 0:
            mastered_pct = (mastered['total'] / total_items) * 100
            result_text += f"{streak_msg}You've mastered {mastered_pct:.1f}% of your study materials. "

        result_text += "Keep studying! 頑張ってください！"

        return {
            "status": "success",
            "content": [{"text": result_text}]
        }

    except Exception as e:
        return {
            "status": "error",
            "content": [{
                "text": f"Error retrieving progress statistics: {str(e)}"
            }]
        }
