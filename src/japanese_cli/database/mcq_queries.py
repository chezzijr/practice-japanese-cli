"""
Database query utilities for MCQ reviews.

Provides CRUD operations for mcq_reviews and mcq_review_history tables.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .connection import get_cursor


# ============================================================================
# MCQ Review Queries
# ============================================================================

def create_mcq_review(
    item_id: int,
    item_type: str,
    fsrs_card_state: dict[str, Any],
    due_date: datetime,
    db_path: Path | None = None
) -> int:
    """
    Create a new MCQ review entry for an item.

    Args:
        item_id: ID of vocabulary or kanji item
        item_type: 'vocab' or 'kanji'
        fsrs_card_state: FSRS Card state from Card.to_dict()
        due_date: Next review date
        db_path: Database path (optional)

    Returns:
        int: ID of newly created MCQ review entry
    """
    with get_cursor(db_path) as cursor:
        cursor.execute("""
            INSERT INTO mcq_reviews (
                item_id, item_type, fsrs_card_state, due_date,
                last_reviewed, review_count
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            item_id,
            item_type,
            json.dumps(fsrs_card_state, ensure_ascii=False, default=str),
            due_date.isoformat(),
            None,
            0
        ))
        return cursor.lastrowid


def get_mcq_review(
    item_id: int,
    item_type: str,
    db_path: Path | None = None
) -> Optional[dict[str, Any]]:
    """
    Get MCQ review entry for a specific item.

    Args:
        item_id: ID of vocabulary or kanji item
        item_type: 'vocab' or 'kanji'
        db_path: Database path (optional)

    Returns:
        dict or None: MCQ review data, or None if not found
    """
    with get_cursor(db_path) as cursor:
        cursor.execute(
            "SELECT * FROM mcq_reviews WHERE item_id = ? AND item_type = ?",
            (item_id, item_type)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def get_mcq_review_by_id(
    review_id: int,
    db_path: Path | None = None
) -> Optional[dict[str, Any]]:
    """
    Get MCQ review entry by ID.

    Args:
        review_id: MCQ review ID
        db_path: Database path (optional)

    Returns:
        dict or None: MCQ review data, or None if not found
    """
    with get_cursor(db_path) as cursor:
        cursor.execute("SELECT * FROM mcq_reviews WHERE id = ?", (review_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def update_mcq_review(
    review_id: int,
    fsrs_card_state: dict[str, Any],
    due_date: datetime,
    db_path: Path | None = None
) -> bool:
    """
    Update an MCQ review entry with new FSRS state.

    Args:
        review_id: MCQ review ID
        fsrs_card_state: Updated FSRS Card state
        due_date: New due date
        db_path: Database path (optional)

    Returns:
        bool: True if updated, False if not found
    """
    with get_cursor(db_path) as cursor:
        now = datetime.now(timezone.utc)
        cursor.execute("""
            UPDATE mcq_reviews
            SET fsrs_card_state = ?, due_date = ?, last_reviewed = ?,
                review_count = review_count + 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            json.dumps(fsrs_card_state, ensure_ascii=False, default=str),
            due_date.isoformat(),
            now.isoformat(),
            review_id
        ))
        return cursor.rowcount > 0


def get_due_mcq_cards(
    item_type: Optional[str] = None,
    jlpt_level: Optional[str] = None,
    limit: Optional[int] = None,
    db_path: Path | None = None
) -> list[dict[str, Any]]:
    """
    Get MCQ cards that are due for review.

    Args:
        item_type: Filter by 'vocab' or 'kanji' (optional)
        jlpt_level: Filter by JLPT level (optional)
        limit: Maximum number of cards (optional)
        db_path: Database path (optional)

    Returns:
        list[dict]: List of due MCQ review entries with item data
    """
    with get_cursor(db_path) as cursor:
        now = datetime.now(timezone.utc).isoformat()

        # Base query joins mcq_reviews with vocabulary or kanji
        # Note: Both queries must have same columns for UNION ALL
        if item_type == "vocab" or item_type is None:
            query_vocab = """
                SELECT r.id, r.item_id, r.item_type, r.fsrs_card_state, r.due_date,
                       r.last_reviewed, r.review_count, r.created_at, r.updated_at,
                       v.word as content, v.reading, v.meanings, v.jlpt_level
                FROM mcq_reviews r
                JOIN vocabulary v ON r.item_id = v.id
                WHERE r.item_type = 'vocab' AND r.due_date <= ?
            """
            params_vocab: list[Any] = [now]

            if jlpt_level:
                query_vocab += " AND v.jlpt_level = ?"
                params_vocab.append(jlpt_level)

        if item_type == "kanji" or item_type is None:
            query_kanji = """
                SELECT r.id, r.item_id, r.item_type, r.fsrs_card_state, r.due_date,
                       r.last_reviewed, r.review_count, r.created_at, r.updated_at,
                       k.character as content, k.vietnamese_reading as reading, k.meanings, k.jlpt_level
                FROM mcq_reviews r
                JOIN kanji k ON r.item_id = k.id
                WHERE r.item_type = 'kanji' AND r.due_date <= ?
            """
            params_kanji: list[Any] = [now]

            if jlpt_level:
                query_kanji += " AND k.jlpt_level = ?"
                params_kanji.append(jlpt_level)

        # Combine queries
        if item_type == "vocab":
            query = query_vocab + " ORDER BY r.due_date ASC"
            params = params_vocab
        elif item_type == "kanji":
            query = query_kanji + " ORDER BY r.due_date ASC"
            params = params_kanji
        else:
            # For UNION ALL, wrap in subquery for ORDER BY
            query = f"""
                SELECT * FROM (
                    {query_vocab}
                    UNION ALL
                    {query_kanji}
                ) ORDER BY due_date ASC
            """
            params = params_vocab + params_kanji

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor.execute(query, tuple(params))
        return [dict(row) for row in cursor.fetchall()]


def delete_mcq_review(
    item_id: int,
    item_type: str,
    db_path: Path | None = None
) -> bool:
    """
    Delete an MCQ review entry.

    Args:
        item_id: ID of vocabulary or kanji item
        item_type: 'vocab' or 'kanji'
        db_path: Database path (optional)

    Returns:
        bool: True if deleted, False if not found
    """
    with get_cursor(db_path) as cursor:
        cursor.execute(
            "DELETE FROM mcq_reviews WHERE item_id = ? AND item_type = ?",
            (item_id, item_type)
        )
        return cursor.rowcount > 0


# ============================================================================
# MCQ Review History Queries
# ============================================================================

def add_mcq_review_history(
    mcq_review_id: int,
    selected_option: int,
    is_correct: bool,
    duration_ms: Optional[int] = None,
    db_path: Path | None = None
) -> int:
    """
    Add an MCQ review history entry.

    Args:
        mcq_review_id: MCQ review ID
        selected_option: Index of selected option (0-3)
        is_correct: Whether the answer was correct
        duration_ms: Time spent in milliseconds
        db_path: Database path (optional)

    Returns:
        int: ID of newly created history entry
    """
    with get_cursor(db_path) as cursor:
        cursor.execute("""
            INSERT INTO mcq_review_history (mcq_review_id, selected_option, is_correct, duration_ms)
            VALUES (?, ?, ?, ?)
        """, (mcq_review_id, selected_option, int(is_correct), duration_ms))
        return cursor.lastrowid


def get_mcq_review_history(
    mcq_review_id: int,
    limit: Optional[int] = None,
    db_path: Path | None = None
) -> list[dict[str, Any]]:
    """
    Get MCQ review history for a specific MCQ review.

    Args:
        mcq_review_id: MCQ review ID
        limit: Maximum number of history entries (optional)
        db_path: Database path (optional)

    Returns:
        list[dict]: List of history entries, ordered by most recent first
    """
    with get_cursor(db_path) as cursor:
        query = """
            SELECT * FROM mcq_review_history
            WHERE mcq_review_id = ?
            ORDER BY reviewed_at DESC
        """
        params: list[Any] = [mcq_review_id]

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor.execute(query, tuple(params))
        return [dict(row) for row in cursor.fetchall()]


def get_mcq_stats(
    item_type: Optional[str] = None,
    jlpt_level: Optional[str] = None,
    days: int = 30,
    db_path: Path | None = None
) -> dict[str, Any]:
    """
    Get MCQ statistics for a given period.

    Args:
        item_type: Filter by 'vocab' or 'kanji' (optional)
        jlpt_level: Filter by JLPT level (optional)
        days: Number of days to look back (default: 30)
        db_path: Database path (optional)

    Returns:
        dict: Statistics including total, correct count, accuracy rate
    """
    with get_cursor(db_path) as cursor:
        # Build query with filters
        query = """
            SELECT
                COUNT(*) as total_reviews,
                SUM(CASE WHEN h.is_correct = 1 THEN 1 ELSE 0 END) as correct_count
            FROM mcq_review_history h
            JOIN mcq_reviews r ON h.mcq_review_id = r.id
            WHERE h.reviewed_at >= datetime('now', '-' || ? || ' days')
        """
        params: list[Any] = [days]

        if item_type:
            query += " AND r.item_type = ?"
            params.append(item_type)

        if jlpt_level:
            # Join with vocabulary or kanji to filter by JLPT level
            if item_type == "vocab":
                query = query.replace(
                    "FROM mcq_review_history h",
                    "FROM mcq_review_history h"
                )
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
            total = row['total_reviews'] or 0
            correct = row['correct_count'] or 0
            accuracy = (correct / total * 100) if total > 0 else 0.0

            return {
                "total_reviews": total,
                "correct_count": correct,
                "incorrect_count": total - correct,
                "accuracy_rate": round(accuracy, 2)
            }

        return {
            "total_reviews": 0,
            "correct_count": 0,
            "incorrect_count": 0,
            "accuracy_rate": 0.0
        }
