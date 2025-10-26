"""
Statistics calculation module for Japanese Learning CLI.

Provides functions to calculate progress statistics, retention rates,
mastery counts, and time-based analytics from the database.
"""

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from ..database import get_cursor


# Mastery threshold: cards with stability >= 21 days are considered mastered
MASTERY_STABILITY_THRESHOLD = 21.0  # days


def calculate_vocab_counts_by_level(
    jlpt_level: Optional[str] = None,
    db_path: Optional[Path] = None
) -> dict[str, int]:
    """
    Calculate vocabulary counts grouped by JLPT level.

    Args:
        jlpt_level: Optional filter for specific JLPT level
        db_path: Optional database path

    Returns:
        dict: Mapping of JLPT level to count (e.g., {"n5": 81, "n4": 120})
              If jlpt_level is specified, returns {"<level>": count}

    Example:
        counts = calculate_vocab_counts_by_level()
        # {"n5": 81, "n4": 120, "n3": 0, ...}

        n5_count = calculate_vocab_counts_by_level(jlpt_level="n5")
        # {"n5": 81}
    """
    with get_cursor(db_path) as cursor:
        if jlpt_level:
            # Count for specific level
            cursor.execute(
                "SELECT COUNT(*) FROM vocabulary WHERE jlpt_level = ?",
                (jlpt_level,)
            )
            count = cursor.fetchone()[0]
            return {jlpt_level: count}
        else:
            # Count for all levels
            cursor.execute("""
                SELECT jlpt_level, COUNT(*) as count
                FROM vocabulary
                WHERE jlpt_level IS NOT NULL
                GROUP BY jlpt_level
            """)
            rows = cursor.fetchall()

            # Initialize all levels with 0
            counts = {"n5": 0, "n4": 0, "n3": 0, "n2": 0, "n1": 0}

            # Update with actual counts
            for row in rows:
                level = row[0]
                count = row[1]
                if level in counts:
                    counts[level] = count

            # Also get total count (including NULL levels)
            cursor.execute("SELECT COUNT(*) FROM vocabulary")
            total = cursor.fetchone()[0]
            counts["total"] = total

            return counts


def calculate_kanji_counts_by_level(
    jlpt_level: Optional[str] = None,
    db_path: Optional[Path] = None
) -> dict[str, int]:
    """
    Calculate kanji counts grouped by JLPT level.

    Args:
        jlpt_level: Optional filter for specific JLPT level
        db_path: Optional database path

    Returns:
        dict: Mapping of JLPT level to count (e.g., {"n5": 103, "n4": 150})

    Example:
        counts = calculate_kanji_counts_by_level()
        # {"n5": 103, "n4": 0, ...}
    """
    with get_cursor(db_path) as cursor:
        if jlpt_level:
            # Count for specific level
            cursor.execute(
                "SELECT COUNT(*) FROM kanji WHERE jlpt_level = ?",
                (jlpt_level,)
            )
            count = cursor.fetchone()[0]
            return {jlpt_level: count}
        else:
            # Count for all levels
            cursor.execute("""
                SELECT jlpt_level, COUNT(*) as count
                FROM kanji
                WHERE jlpt_level IS NOT NULL
                GROUP BY jlpt_level
            """)
            rows = cursor.fetchall()

            # Initialize all levels with 0
            counts = {"n5": 0, "n4": 0, "n3": 0, "n2": 0, "n1": 0}

            # Update with actual counts
            for row in rows:
                level = row[0]
                count = row[1]
                if level in counts:
                    counts[level] = count

            # Also get total count
            cursor.execute("SELECT COUNT(*) FROM kanji")
            total = cursor.fetchone()[0]
            counts["total"] = total

            return counts


def calculate_mastered_items(
    jlpt_level: Optional[str] = None,
    item_type: Optional[str] = None,
    db_path: Optional[Path] = None
) -> dict[str, int]:
    """
    Calculate count of mastered items (stability >= 21 days).

    An item is considered "mastered" if its FSRS stability is at least
    21 days (3 weeks), indicating strong long-term retention.

    Args:
        jlpt_level: Optional filter for JLPT level
        item_type: Optional filter ('vocab' or 'kanji')
        db_path: Optional database path

    Returns:
        dict: Counts by type (e.g., {"vocab": 50, "kanji": 20, "total": 70})

    Example:
        mastered = calculate_mastered_items()
        # {"vocab": 50, "kanji": 20, "total": 70}

        mastered_n5 = calculate_mastered_items(jlpt_level="n5")
        # {"vocab": 30, "kanji": 15, "total": 45}
    """
    with get_cursor(db_path) as cursor:
        counts = {"vocab": 0, "kanji": 0, "total": 0}

        # Query for mastered vocabulary
        if item_type is None or item_type == "vocab":
            if jlpt_level:
                query = """
                    SELECT COUNT(*) FROM reviews r
                    JOIN vocabulary v ON r.item_id = v.id
                    WHERE r.item_type = 'vocab'
                    AND v.jlpt_level = ?
                    AND json_extract(r.fsrs_card_state, '$.stability') >= ?
                """
                cursor.execute(query, (jlpt_level, MASTERY_STABILITY_THRESHOLD))
            else:
                query = """
                    SELECT COUNT(*) FROM reviews r
                    WHERE r.item_type = 'vocab'
                    AND json_extract(r.fsrs_card_state, '$.stability') >= ?
                """
                cursor.execute(query, (MASTERY_STABILITY_THRESHOLD,))

            counts["vocab"] = cursor.fetchone()[0]

        # Query for mastered kanji
        if item_type is None or item_type == "kanji":
            if jlpt_level:
                query = """
                    SELECT COUNT(*) FROM reviews r
                    JOIN kanji k ON r.item_id = k.id
                    WHERE r.item_type = 'kanji'
                    AND k.jlpt_level = ?
                    AND json_extract(r.fsrs_card_state, '$.stability') >= ?
                """
                cursor.execute(query, (jlpt_level, MASTERY_STABILITY_THRESHOLD))
            else:
                query = """
                    SELECT COUNT(*) FROM reviews r
                    WHERE r.item_type = 'kanji'
                    AND json_extract(r.fsrs_card_state, '$.stability') >= ?
                """
                cursor.execute(query, (MASTERY_STABILITY_THRESHOLD,))

            counts["kanji"] = cursor.fetchone()[0]

        counts["total"] = counts["vocab"] + counts["kanji"]
        return counts


def calculate_retention_rate(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db_path: Optional[Path] = None
) -> float:
    """
    Calculate retention rate from review history.

    Retention rate = (Good + Easy) / Total Reviews × 100%
    - Ratings 3 (Good) and 4 (Easy) count as "retained"
    - Ratings 1 (Again) and 2 (Hard) count as "not retained"

    Args:
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
        db_path: Optional database path

    Returns:
        float: Retention rate as percentage (0.0 to 100.0)

    Example:
        # All-time retention
        rate = calculate_retention_rate()
        # 85.5

        # Last 7 days retention
        rate = calculate_retention_rate(
            start_date=date.today() - timedelta(days=7),
            end_date=date.today()
        )
    """
    with get_cursor(db_path) as cursor:
        # Build query based on date filters
        if start_date and end_date:
            query = """
                SELECT rating, COUNT(*) as count
                FROM review_history
                WHERE DATE(reviewed_at) >= ? AND DATE(reviewed_at) <= ?
                GROUP BY rating
            """
            cursor.execute(query, (start_date.isoformat(), end_date.isoformat()))
        elif start_date:
            query = """
                SELECT rating, COUNT(*) as count
                FROM review_history
                WHERE DATE(reviewed_at) >= ?
                GROUP BY rating
            """
            cursor.execute(query, (start_date.isoformat(),))
        else:
            query = """
                SELECT rating, COUNT(*) as count
                FROM review_history
                GROUP BY rating
            """
            cursor.execute(query)

        rows = cursor.fetchall()

        # Count by rating
        rating_counts = {1: 0, 2: 0, 3: 0, 4: 0}
        for row in rows:
            rating = row[0]
            count = row[1]
            if rating in rating_counts:
                rating_counts[rating] = count

        # Calculate retention rate
        total = sum(rating_counts.values())
        if total == 0:
            return 0.0

        retained = rating_counts[3] + rating_counts[4]  # Good + Easy
        retention_rate = (retained / total) * 100.0

        return round(retention_rate, 1)


def get_most_reviewed_items(
    limit: int = 10,
    item_type: Optional[str] = None,
    db_path: Optional[Path] = None
) -> list[dict[str, Any]]:
    """
    Get most frequently reviewed items.

    Args:
        limit: Maximum number of items to return
        item_type: Optional filter ('vocab' or 'kanji')
        db_path: Optional database path

    Returns:
        list[dict]: List of items with review counts, sorted by count descending
                    Each dict contains: item_id, item_type, word/character, review_count

    Example:
        top_items = get_most_reviewed_items(limit=5)
        # [
        #   {"item_id": 75, "item_type": "vocab", "word": "単語", "review_count": 50},
        #   {"item_id": 1, "item_type": "kanji", "character": "語", "review_count": 45},
        #   ...
        # ]
    """
    with get_cursor(db_path) as cursor:
        if item_type == "vocab":
            query = """
                SELECT r.item_id, r.item_type, v.word, r.review_count
                FROM reviews r
                JOIN vocabulary v ON r.item_id = v.id
                WHERE r.item_type = 'vocab'
                ORDER BY r.review_count DESC
                LIMIT ?
            """
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            return [
                {
                    "item_id": row[0],
                    "item_type": row[1],
                    "word": row[2],
                    "review_count": row[3]
                }
                for row in rows
            ]
        elif item_type == "kanji":
            query = """
                SELECT r.item_id, r.item_type, k.character, r.review_count
                FROM reviews r
                JOIN kanji k ON r.item_id = k.id
                WHERE r.item_type = 'kanji'
                ORDER BY r.review_count DESC
                LIMIT ?
            """
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            return [
                {
                    "item_id": row[0],
                    "item_type": row[1],
                    "character": row[2],
                    "review_count": row[3]
                }
                for row in rows
            ]
        else:
            # Get both vocab and kanji, then combine and sort
            vocab_query = """
                SELECT r.item_id, r.item_type, v.word as text, r.review_count
                FROM reviews r
                JOIN vocabulary v ON r.item_id = v.id
                WHERE r.item_type = 'vocab'
            """
            cursor.execute(vocab_query)
            vocab_rows = cursor.fetchall()

            kanji_query = """
                SELECT r.item_id, r.item_type, k.character as text, r.review_count
                FROM reviews r
                JOIN kanji k ON r.item_id = k.id
                WHERE r.item_type = 'kanji'
            """
            cursor.execute(kanji_query)
            kanji_rows = cursor.fetchall()

            # Combine and sort
            all_items = []
            for row in vocab_rows:
                all_items.append({
                    "item_id": row[0],
                    "item_type": row[1],
                    "word": row[2],
                    "review_count": row[3]
                })
            for row in kanji_rows:
                all_items.append({
                    "item_id": row[0],
                    "item_type": row[1],
                    "character": row[2],
                    "review_count": row[3]
                })

            # Sort by review_count descending and take top N
            all_items.sort(key=lambda x: x["review_count"], reverse=True)
            return all_items[:limit]


def get_reviews_by_date_range(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db_path: Optional[Path] = None
) -> list[dict[str, Any]]:
    """
    Get review history entries within a date range.

    Args:
        start_date: Optional start date (inclusive)
        end_date: Optional end date (inclusive)
        db_path: Optional database path

    Returns:
        list[dict]: Review history entries with all fields

    Example:
        # Last 7 days
        reviews = get_reviews_by_date_range(
            start_date=date.today() - timedelta(days=7),
            end_date=date.today()
        )
    """
    with get_cursor(db_path) as cursor:
        if start_date and end_date:
            query = """
                SELECT * FROM review_history
                WHERE DATE(reviewed_at) >= ? AND DATE(reviewed_at) <= ?
                ORDER BY reviewed_at DESC
            """
            cursor.execute(query, (start_date.isoformat(), end_date.isoformat()))
        elif start_date:
            query = """
                SELECT * FROM review_history
                WHERE DATE(reviewed_at) >= ?
                ORDER BY reviewed_at DESC
            """
            cursor.execute(query, (start_date.isoformat(),))
        else:
            query = """
                SELECT * FROM review_history
                ORDER BY reviewed_at DESC
            """
            cursor.execute(query)

        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def aggregate_daily_review_counts(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db_path: Optional[Path] = None
) -> dict[str, int]:
    """
    Aggregate review counts grouped by date.

    Args:
        start_date: Optional start date
        end_date: Optional end date
        db_path: Optional database path

    Returns:
        dict: Mapping of ISO date string to review count
              (e.g., {"2025-10-20": 15, "2025-10-21": 20})

    Example:
        daily_counts = aggregate_daily_review_counts(
            start_date=date.today() - timedelta(days=7),
            end_date=date.today()
        )
        # {"2025-10-19": 0, "2025-10-20": 15, ..., "2025-10-26": 20}
    """
    with get_cursor(db_path) as cursor:
        if start_date and end_date:
            query = """
                SELECT DATE(reviewed_at) as review_date, COUNT(*) as count
                FROM review_history
                WHERE DATE(reviewed_at) >= ? AND DATE(reviewed_at) <= ?
                GROUP BY DATE(reviewed_at)
                ORDER BY review_date
            """
            cursor.execute(query, (start_date.isoformat(), end_date.isoformat()))
        elif start_date:
            query = """
                SELECT DATE(reviewed_at) as review_date, COUNT(*) as count
                FROM review_history
                WHERE DATE(reviewed_at) >= ?
                GROUP BY DATE(reviewed_at)
                ORDER BY review_date
            """
            cursor.execute(query, (start_date.isoformat(),))
        else:
            query = """
                SELECT DATE(reviewed_at) as review_date, COUNT(*) as count
                FROM review_history
                GROUP BY DATE(reviewed_at)
                ORDER BY review_date
            """
            cursor.execute(query)

        rows = cursor.fetchall()

        # Convert to dict
        daily_counts = {}
        for row in rows:
            date_str = row[0]
            count = row[1]
            daily_counts[date_str] = count

        # If date range specified, fill in missing dates with 0
        if start_date and end_date:
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.isoformat()
                if date_str not in daily_counts:
                    daily_counts[date_str] = 0
                current_date += timedelta(days=1)

        return daily_counts


def calculate_average_review_duration(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db_path: Optional[Path] = None
) -> float:
    """
    Calculate average time spent per review in seconds.

    Args:
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
        db_path: Optional database path

    Returns:
        float: Average duration in seconds (0.0 if no reviews)

    Example:
        avg_duration = calculate_average_review_duration()
        # 4.5 (seconds per card)
    """
    with get_cursor(db_path) as cursor:
        if start_date and end_date:
            query = """
                SELECT AVG(duration_ms) as avg_ms
                FROM review_history
                WHERE DATE(reviewed_at) >= ? AND DATE(reviewed_at) <= ?
                AND duration_ms IS NOT NULL
            """
            cursor.execute(query, (start_date.isoformat(), end_date.isoformat()))
        elif start_date:
            query = """
                SELECT AVG(duration_ms) as avg_ms
                FROM review_history
                WHERE DATE(reviewed_at) >= ?
                AND duration_ms IS NOT NULL
            """
            cursor.execute(query, (start_date.isoformat(),))
        else:
            query = """
                SELECT AVG(duration_ms) as avg_ms
                FROM review_history
                WHERE duration_ms IS NOT NULL
            """
            cursor.execute(query)

        result = cursor.fetchone()
        avg_ms = result[0] if result and result[0] else 0.0

        # Convert milliseconds to seconds
        return round(avg_ms / 1000.0, 1)


# ============================================================================
# MCQ Statistics Functions
# ============================================================================


def get_mcq_accuracy_rate(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    item_type: Optional[str] = None,
    jlpt_level: Optional[str] = None,
    db_path: Optional[Path] = None
) -> float:
    """
    Calculate MCQ accuracy rate (percentage of correct answers).

    Args:
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
        item_type: Optional filter ('vocab' or 'kanji')
        jlpt_level: Optional filter for JLPT level
        db_path: Optional database path

    Returns:
        float: Accuracy rate as percentage (0.0 to 100.0)

    Example:
        # All-time MCQ accuracy
        rate = get_mcq_accuracy_rate()
        # 82.5

        # Last 7 days for N5 vocabulary
        rate = get_mcq_accuracy_rate(
            start_date=date.today() - timedelta(days=7),
            end_date=date.today(),
            item_type="vocab",
            jlpt_level="n5"
        )
    """
    with get_cursor(db_path) as cursor:
        # Build query with filters
        query = """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN h.is_correct = 1 THEN 1 ELSE 0 END) as correct_count
            FROM mcq_review_history h
            JOIN mcq_reviews r ON h.mcq_review_id = r.id
            WHERE 1=1
        """
        params: list[Any] = []

        # Date filtering
        if start_date and end_date:
            query += " AND DATE(h.reviewed_at) >= ? AND DATE(h.reviewed_at) <= ?"
            params.extend([start_date.isoformat(), end_date.isoformat()])
        elif start_date:
            query += " AND DATE(h.reviewed_at) >= ?"
            params.append(start_date.isoformat())

        # Item type filtering
        if item_type:
            query += " AND r.item_type = ?"
            params.append(item_type)

        # JLPT level filtering
        if jlpt_level:
            if item_type == "vocab":
                query += " AND r.item_id IN (SELECT id FROM vocabulary WHERE jlpt_level = ?)"
                params.append(jlpt_level)
            elif item_type == "kanji":
                query += " AND r.item_id IN (SELECT id FROM kanji WHERE jlpt_level = ?)"
                params.append(jlpt_level)
            else:
                # Both types - check both tables
                query += """ AND (
                    (r.item_type = 'vocab' AND r.item_id IN (SELECT id FROM vocabulary WHERE jlpt_level = ?))
                    OR (r.item_type = 'kanji' AND r.item_id IN (SELECT id FROM kanji WHERE jlpt_level = ?))
                )"""
                params.extend([jlpt_level, jlpt_level])

        cursor.execute(query, tuple(params))
        row = cursor.fetchone()

        if row:
            total = row[0] or 0
            correct = row[1] or 0

            if total == 0:
                return 0.0

            accuracy = (correct / total) * 100.0
            return round(accuracy, 1)

        return 0.0


def get_mcq_stats_by_type(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    jlpt_level: Optional[str] = None,
    db_path: Optional[Path] = None
) -> dict[str, dict[str, Any]]:
    """
    Get MCQ statistics broken down by item type (vocab vs kanji).

    Provides separate accuracy and review counts for vocabulary and kanji items,
    allowing comparison of performance across different content types.

    Args:
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
        jlpt_level: Optional filter for JLPT level
        db_path: Optional database path

    Returns:
        dict: Statistics by type with structure:
              {
                  "vocab": {
                      "total_reviews": int,
                      "correct_count": int,
                      "incorrect_count": int,
                      "accuracy_rate": float
                  },
                  "kanji": {...},
                  "overall": {...}
              }

    Example:
        stats = get_mcq_stats_by_type(jlpt_level="n5")
        # {
        #     "vocab": {"total_reviews": 50, "correct_count": 42, "accuracy_rate": 84.0},
        #     "kanji": {"total_reviews": 30, "correct_count": 25, "accuracy_rate": 83.3},
        #     "overall": {"total_reviews": 80, "correct_count": 67, "accuracy_rate": 83.8}
        # }
    """
    with get_cursor(db_path) as cursor:
        # Build base query with date filtering
        base_query = """
            SELECT
                r.item_type,
                COUNT(*) as total,
                SUM(CASE WHEN h.is_correct = 1 THEN 1 ELSE 0 END) as correct_count
            FROM mcq_review_history h
            JOIN mcq_reviews r ON h.mcq_review_id = r.id
            WHERE 1=1
        """
        params: list[Any] = []

        # Date filtering
        if start_date and end_date:
            base_query += " AND DATE(h.reviewed_at) >= ? AND DATE(h.reviewed_at) <= ?"
            params.extend([start_date.isoformat(), end_date.isoformat()])
        elif start_date:
            base_query += " AND DATE(h.reviewed_at) >= ?"
            params.append(start_date.isoformat())

        # JLPT level filtering
        if jlpt_level:
            base_query += """ AND (
                (r.item_type = 'vocab' AND r.item_id IN (SELECT id FROM vocabulary WHERE jlpt_level = ?))
                OR (r.item_type = 'kanji' AND r.item_id IN (SELECT id FROM kanji WHERE jlpt_level = ?))
            )"""
            params.extend([jlpt_level, jlpt_level])

        base_query += " GROUP BY r.item_type"

        cursor.execute(base_query, tuple(params))
        rows = cursor.fetchall()

        # Initialize result structure
        result = {
            "vocab": {
                "total_reviews": 0,
                "correct_count": 0,
                "incorrect_count": 0,
                "accuracy_rate": 0.0
            },
            "kanji": {
                "total_reviews": 0,
                "correct_count": 0,
                "incorrect_count": 0,
                "accuracy_rate": 0.0
            },
            "overall": {
                "total_reviews": 0,
                "correct_count": 0,
                "incorrect_count": 0,
                "accuracy_rate": 0.0
            }
        }

        # Process rows
        for row in rows:
            item_type = row[0]
            total = row[1] or 0
            correct = row[2] or 0
            incorrect = total - correct
            accuracy = (correct / total * 100.0) if total > 0 else 0.0

            if item_type in result:
                result[item_type] = {
                    "total_reviews": total,
                    "correct_count": correct,
                    "incorrect_count": incorrect,
                    "accuracy_rate": round(accuracy, 1)
                }

        # Calculate overall stats
        vocab_total = result["vocab"]["total_reviews"]
        vocab_correct = result["vocab"]["correct_count"]
        kanji_total = result["kanji"]["total_reviews"]
        kanji_correct = result["kanji"]["correct_count"]

        overall_total = vocab_total + kanji_total
        overall_correct = vocab_correct + kanji_correct
        overall_accuracy = (overall_correct / overall_total * 100.0) if overall_total > 0 else 0.0

        result["overall"] = {
            "total_reviews": overall_total,
            "correct_count": overall_correct,
            "incorrect_count": overall_total - overall_correct,
            "accuracy_rate": round(overall_accuracy, 1)
        }

        return result


def get_mcq_option_distribution(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db_path: Optional[Path] = None
) -> dict[str, int]:
    """
    Get distribution of selected MCQ options (A/B/C/D).

    Useful for detecting selection bias - users might unconsciously favor
    certain positions (e.g., always choosing A or avoiding D).

    Args:
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
        db_path: Optional database path

    Returns:
        dict: Mapping of option label to selection count
              (e.g., {"A": 45, "B": 38, "C": 42, "D": 35})

    Example:
        # Check if user has selection bias
        dist = get_mcq_option_distribution()
        # {"A": 45, "B": 38, "C": 42, "D": 35}

        # Last 30 days distribution
        dist = get_mcq_option_distribution(
            start_date=date.today() - timedelta(days=30),
            end_date=date.today()
        )
    """
    with get_cursor(db_path) as cursor:
        # Build query with date filtering
        query = """
            SELECT selected_option, COUNT(*) as count
            FROM mcq_review_history
            WHERE 1=1
        """
        params: list[Any] = []

        # Date filtering
        if start_date and end_date:
            query += " AND DATE(reviewed_at) >= ? AND DATE(reviewed_at) <= ?"
            params.extend([start_date.isoformat(), end_date.isoformat()])
        elif start_date:
            query += " AND DATE(reviewed_at) >= ?"
            params.append(start_date.isoformat())

        query += " GROUP BY selected_option ORDER BY selected_option"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

        # Initialize all options with 0
        distribution = {"A": 0, "B": 0, "C": 0, "D": 0}
        option_labels = ["A", "B", "C", "D"]

        # Map selected_option (0-3) to labels (A-D)
        for row in rows:
            option_index = row[0]
            count = row[1]
            if 0 <= option_index < 4:
                label = option_labels[option_index]
                distribution[label] = count

        return distribution
