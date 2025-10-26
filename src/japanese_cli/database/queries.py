"""
Database query utilities for Japanese Learning CLI.

Provides CRUD operations for all database tables.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .connection import get_cursor, get_db_connection, get_db_path


# ============================================================================
# Vocabulary Queries
# ============================================================================

def add_vocabulary(
    word: str,
    reading: str,
    meanings: dict[str, list[str]],
    vietnamese_reading: Optional[str] = None,
    jlpt_level: Optional[str] = None,
    part_of_speech: Optional[str] = None,
    tags: Optional[list[str]] = None,
    notes: Optional[str] = None,
    db_path: Path | None = None
) -> int:
    """
    Add a new vocabulary word to the database.

    Args:
        word: Japanese word (kanji/kana)
        reading: Reading in hiragana/katakana
        meanings: Dictionary of meanings by language {"vi": [...], "en": [...]}
        vietnamese_reading: Optional Sino-Vietnamese reading
        jlpt_level: JLPT level (n5, n4, n3, n2, n1)
        part_of_speech: Part of speech
        tags: List of tags
        notes: User notes
        db_path: Database path (optional)

    Returns:
        int: ID of newly created vocabulary entry
    """
    with get_cursor(db_path) as cursor:
        cursor.execute("""
            INSERT INTO vocabulary (
                word, reading, meanings, vietnamese_reading, jlpt_level,
                part_of_speech, tags, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            word,
            reading,
            json.dumps(meanings, ensure_ascii=False),
            vietnamese_reading,
            jlpt_level,
            part_of_speech,
            json.dumps(tags or [], ensure_ascii=False),
            notes
        ))
        return cursor.lastrowid


def get_vocabulary_by_id(vocab_id: int, db_path: Path | None = None) -> Optional[dict[str, Any]]:
    """
    Get a vocabulary entry by ID.

    Args:
        vocab_id: Vocabulary ID
        db_path: Database path (optional)

    Returns:
        dict or None: Vocabulary data as dictionary, or None if not found
    """
    with get_cursor(db_path) as cursor:
        cursor.execute("SELECT * FROM vocabulary WHERE id = ?", (vocab_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def get_vocabulary_by_word(
    word: str,
    reading: str,
    db_path: Path | None = None
) -> Optional[dict[str, Any]]:
    """
    Get a vocabulary entry by word and reading.

    Args:
        word: Japanese word (kanji/kana)
        reading: Reading in hiragana/katakana
        db_path: Database path (optional)

    Returns:
        dict or None: Vocabulary data as dictionary, or None if not found
    """
    with get_cursor(db_path) as cursor:
        cursor.execute(
            "SELECT * FROM vocabulary WHERE word = ? AND reading = ?",
            (word, reading)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def list_vocabulary(
    jlpt_level: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0,
    db_path: Path | None = None
) -> list[dict[str, Any]]:
    """
    List vocabulary entries with optional filtering.

    Args:
        jlpt_level: Filter by JLPT level (optional)
        limit: Maximum number of results (optional)
        offset: Number of results to skip (default: 0)
        db_path: Database path (optional)

    Returns:
        list[dict]: List of vocabulary entries
    """
    with get_cursor(db_path) as cursor:
        query = "SELECT * FROM vocabulary"
        params: list[Any] = []

        if jlpt_level:
            query += " WHERE jlpt_level = ?"
            params.append(jlpt_level)

        query += " ORDER BY created_at DESC"

        if limit:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def search_vocabulary(
    search_term: str,
    jlpt_level: Optional[str] = None,
    db_path: Path | None = None
) -> list[dict[str, Any]]:
    """
    Search vocabulary by word, reading, or meanings.

    Args:
        search_term: Term to search for
        jlpt_level: Filter by JLPT level (optional)
        db_path: Database path (optional)

    Returns:
        list[dict]: Matching vocabulary entries
    """
    with get_cursor(db_path) as cursor:
        query = """
            SELECT * FROM vocabulary
            WHERE word LIKE ? OR reading LIKE ? OR meanings LIKE ?
        """
        params: list[Any] = [f"%{search_term}%"] * 3

        if jlpt_level:
            query += " AND jlpt_level = ?"
            params.append(jlpt_level)

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def search_vocabulary_by_reading(
    reading: str,
    exact_match: bool = True,
    db_path: Path | None = None
) -> list[dict[str, Any]]:
    """
    Search vocabulary entries by reading (hiragana/katakana).

    Args:
        reading: Reading to search for (in hiragana/katakana)
        exact_match: If True, find exact matches; if False, find partial matches
        db_path: Database path (optional)

    Returns:
        list[dict]: Matching vocabulary entries with all fields

    Example:
        >>> # Find all words read as "たんご"
        >>> matches = search_vocabulary_by_reading("たんご")
        >>> # Find words with reading containing "たん"
        >>> matches = search_vocabulary_by_reading("たん", exact_match=False)
    """
    with get_cursor(db_path) as cursor:
        if exact_match:
            query = "SELECT * FROM vocabulary WHERE reading = ? ORDER BY created_at DESC"
            params = [reading]
        else:
            query = "SELECT * FROM vocabulary WHERE reading LIKE ? ORDER BY created_at DESC"
            params = [f"%{reading}%"]

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def update_vocabulary(vocab_id: int, **kwargs) -> bool:
    """
    Update a vocabulary entry.

    Args:
        vocab_id: Vocabulary ID
        **kwargs: Fields to update (word, reading, meanings, etc.)

    Returns:
        bool: True if updated, False if not found
    """
    # Extract db_path from kwargs if present
    db_path = kwargs.pop("db_path", None)

    if not kwargs:
        return False

    # Handle JSON fields
    if "meanings" in kwargs and isinstance(kwargs["meanings"], dict):
        kwargs["meanings"] = json.dumps(kwargs["meanings"], ensure_ascii=False)
    if "tags" in kwargs and isinstance(kwargs["tags"], list):
        kwargs["tags"] = json.dumps(kwargs["tags"], ensure_ascii=False)

    # Build UPDATE query
    fields = ", ".join(f"{k} = ?" for k in kwargs.keys())
    values = list(kwargs.values())
    values.append(vocab_id)

    with get_cursor(db_path) as cursor:
        cursor.execute(f"""
            UPDATE vocabulary
            SET {fields}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, values)
        return cursor.rowcount > 0


def delete_vocabulary(vocab_id: int, db_path: Path | None = None) -> bool:
    """
    Delete a vocabulary entry.

    Args:
        vocab_id: Vocabulary ID
        db_path: Database path (optional)

    Returns:
        bool: True if deleted, False if not found
    """
    with get_cursor(db_path) as cursor:
        cursor.execute("DELETE FROM vocabulary WHERE id = ?", (vocab_id,))
        return cursor.rowcount > 0


# ============================================================================
# Kanji Queries
# ============================================================================

def add_kanji(
    character: str,
    on_readings: list[str],
    kun_readings: list[str],
    meanings: dict[str, list[str]],
    vietnamese_reading: Optional[str] = None,
    jlpt_level: Optional[str] = None,
    stroke_count: Optional[int] = None,
    radical: Optional[str] = None,
    notes: Optional[str] = None,
    db_path: Path | None = None
) -> int:
    """
    Add a new kanji character to the database.

    Args:
        character: Single kanji character
        on_readings: List of on'yomi readings
        kun_readings: List of kun'yomi readings
        meanings: Dictionary of meanings by language
        vietnamese_reading: Hán Việt reading
        jlpt_level: JLPT level
        stroke_count: Number of strokes
        radical: Radical character
        notes: User notes
        db_path: Database path (optional)

    Returns:
        int: ID of newly created kanji entry
    """
    with get_cursor(db_path) as cursor:
        cursor.execute("""
            INSERT INTO kanji (
                character, on_readings, kun_readings, meanings,
                vietnamese_reading, jlpt_level, stroke_count, radical, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            character,
            json.dumps(on_readings, ensure_ascii=False),
            json.dumps(kun_readings, ensure_ascii=False),
            json.dumps(meanings, ensure_ascii=False),
            vietnamese_reading,
            jlpt_level,
            stroke_count,
            radical,
            notes
        ))
        return cursor.lastrowid


def get_kanji_by_id(kanji_id: int, db_path: Path | None = None) -> Optional[dict[str, Any]]:
    """
    Get a kanji entry by ID.

    Args:
        kanji_id: Kanji ID
        db_path: Database path (optional)

    Returns:
        dict or None: Kanji data as dictionary, or None if not found
    """
    with get_cursor(db_path) as cursor:
        cursor.execute("SELECT * FROM kanji WHERE id = ?", (kanji_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def get_kanji_by_character(character: str, db_path: Path | None = None) -> Optional[dict[str, Any]]:
    """
    Get a kanji entry by character.

    Args:
        character: Kanji character
        db_path: Database path (optional)

    Returns:
        dict or None: Kanji data as dictionary, or None if not found
    """
    with get_cursor(db_path) as cursor:
        cursor.execute("SELECT * FROM kanji WHERE character = ?", (character,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def list_kanji(
    jlpt_level: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0,
    db_path: Path | None = None
) -> list[dict[str, Any]]:
    """
    List kanji entries with optional filtering.

    Args:
        jlpt_level: Filter by JLPT level (optional)
        limit: Maximum number of results (optional)
        offset: Number of results to skip (default: 0)
        db_path: Database path (optional)

    Returns:
        list[dict]: List of kanji entries
    """
    with get_cursor(db_path) as cursor:
        query = "SELECT * FROM kanji"
        params: list[Any] = []

        if jlpt_level:
            query += " WHERE jlpt_level = ?"
            params.append(jlpt_level)

        query += " ORDER BY created_at DESC"

        if limit:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def search_kanji(
    search_term: str,
    jlpt_level: Optional[str] = None,
    db_path: Path | None = None
) -> list[dict[str, Any]]:
    """
    Search kanji by character, readings, or meanings.

    Args:
        search_term: Term to search for
        jlpt_level: Filter by JLPT level (optional)
        db_path: Database path (optional)

    Returns:
        list[dict]: Matching kanji entries
    """
    with get_cursor(db_path) as cursor:
        query = """
            SELECT * FROM kanji
            WHERE character LIKE ? OR on_readings LIKE ?
            OR kun_readings LIKE ? OR meanings LIKE ?
        """
        params: list[Any] = [f"%{search_term}%"] * 4

        if jlpt_level:
            query += " AND jlpt_level = ?"
            params.append(jlpt_level)

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def search_kanji_by_reading(
    reading: str,
    reading_type: str = "both",
    db_path: Path | None = None
) -> list[dict[str, Any]]:
    """
    Search kanji entries by reading (on-yomi or kun-yomi).

    Args:
        reading: Reading to search for (in hiragana/katakana)
        reading_type: Type of reading - 'on', 'kun', or 'both' (default: 'both')
        db_path: Database path (optional)

    Returns:
        list[dict]: Matching kanji entries with all fields

    Example:
        >>> # Find kanji with on-yomi reading "ゴ"
        >>> matches = search_kanji_by_reading("ゴ", reading_type="on")
        >>> # Find kanji with kun-yomi reading "かた.る"
        >>> matches = search_kanji_by_reading("かた.る", reading_type="kun")
        >>> # Find kanji with either on or kun reading containing "がく"
        >>> matches = search_kanji_by_reading("がく", reading_type="both")
    """
    with get_cursor(db_path) as cursor:
        if reading_type == "on":
            query = "SELECT * FROM kanji WHERE on_readings LIKE ? ORDER BY created_at DESC"
            params = [f"%{reading}%"]
        elif reading_type == "kun":
            query = "SELECT * FROM kanji WHERE kun_readings LIKE ? ORDER BY created_at DESC"
            params = [f"%{reading}%"]
        else:  # both
            query = """
                SELECT * FROM kanji
                WHERE on_readings LIKE ? OR kun_readings LIKE ?
                ORDER BY created_at DESC
            """
            params = [f"%{reading}%", f"%{reading}%"]

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def update_kanji(kanji_id: int, **kwargs) -> bool:
    """
    Update a kanji entry.

    Args:
        kanji_id: Kanji ID
        **kwargs: Fields to update

    Returns:
        bool: True if updated, False if not found
    """
    # Extract db_path from kwargs if present
    db_path = kwargs.pop("db_path", None)

    if not kwargs:
        return False

    # Handle JSON fields
    json_fields = ["on_readings", "kun_readings", "meanings"]
    for field in json_fields:
        if field in kwargs and isinstance(kwargs[field], (list, dict)):
            kwargs[field] = json.dumps(kwargs[field], ensure_ascii=False)

    fields = ", ".join(f"{k} = ?" for k in kwargs.keys())
    values = list(kwargs.values())
    values.append(kanji_id)

    with get_cursor(db_path) as cursor:
        cursor.execute(f"""
            UPDATE kanji
            SET {fields}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, values)
        return cursor.rowcount > 0


def delete_kanji(kanji_id: int, db_path: Path | None = None) -> bool:
    """
    Delete a kanji entry.

    Args:
        kanji_id: Kanji ID
        db_path: Database path (optional)

    Returns:
        bool: True if deleted, False if not found
    """
    with get_cursor(db_path) as cursor:
        cursor.execute("DELETE FROM kanji WHERE id = ?", (kanji_id,))
        return cursor.rowcount > 0


# ============================================================================
# Grammar Queries
# ============================================================================

def add_grammar(
    title: str,
    explanation: str,
    examples: list[dict[str, str]],
    structure: Optional[str] = None,
    jlpt_level: Optional[str] = None,
    related_grammar: Optional[list[int]] = None,
    notes: Optional[str] = None,
    db_path: Path | None = None
) -> int:
    """
    Add a new grammar point to the database.

    Args:
        title: Grammar point title
        explanation: Explanation text
        examples: List of example dicts with "jp", "vi", "en" keys
        structure: Grammar structure pattern
        jlpt_level: JLPT level
        related_grammar: List of related grammar IDs
        notes: User notes
        db_path: Database path (optional)

    Returns:
        int: ID of newly created grammar entry
    """
    with get_cursor(db_path) as cursor:
        cursor.execute("""
            INSERT INTO grammar_points (
                title, structure, explanation, jlpt_level,
                examples, related_grammar, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            title,
            structure,
            explanation,
            jlpt_level,
            json.dumps(examples, ensure_ascii=False),
            json.dumps(related_grammar or [], ensure_ascii=False),
            notes
        ))
        return cursor.lastrowid


def get_grammar_by_id(grammar_id: int, db_path: Path | None = None) -> Optional[dict[str, Any]]:
    """
    Get a grammar point by ID.

    Args:
        grammar_id: Grammar ID
        db_path: Database path (optional)

    Returns:
        dict or None: Grammar data as dictionary, or None if not found
    """
    with get_cursor(db_path) as cursor:
        cursor.execute("SELECT * FROM grammar_points WHERE id = ?", (grammar_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def list_grammar(
    jlpt_level: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0,
    db_path: Path | None = None
) -> list[dict[str, Any]]:
    """
    List grammar points with optional filtering.

    Args:
        jlpt_level: Filter by JLPT level (optional)
        limit: Maximum number of results (optional)
        offset: Number of results to skip (default: 0)
        db_path: Database path (optional)

    Returns:
        list[dict]: List of grammar entries
    """
    with get_cursor(db_path) as cursor:
        query = "SELECT * FROM grammar_points"
        params: list[Any] = []

        if jlpt_level:
            query += " WHERE jlpt_level = ?"
            params.append(jlpt_level)

        query += " ORDER BY created_at DESC"

        if limit:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def update_grammar(grammar_id: int, **kwargs) -> bool:
    """
    Update a grammar point.

    Args:
        grammar_id: Grammar ID
        **kwargs: Fields to update

    Returns:
        bool: True if updated, False if not found
    """
    # Extract db_path from kwargs if present
    db_path = kwargs.pop("db_path", None)

    if not kwargs:
        return False

    # Handle JSON fields
    json_fields = ["examples", "related_grammar"]
    for field in json_fields:
        if field in kwargs and isinstance(kwargs[field], list):
            kwargs[field] = json.dumps(kwargs[field], ensure_ascii=False)

    fields = ", ".join(f"{k} = ?" for k in kwargs.keys())
    values = list(kwargs.values())
    values.append(grammar_id)

    with get_cursor(db_path) as cursor:
        cursor.execute(f"""
            UPDATE grammar_points
            SET {fields}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, values)
        return cursor.rowcount > 0


def delete_grammar(grammar_id: int, db_path: Path | None = None) -> bool:
    """
    Delete a grammar point.

    Args:
        grammar_id: Grammar ID
        db_path: Database path (optional)

    Returns:
        bool: True if deleted, False if not found
    """
    with get_cursor(db_path) as cursor:
        cursor.execute("DELETE FROM grammar_points WHERE id = ?", (grammar_id,))
        return cursor.rowcount > 0


# ============================================================================
# Review Queries
# ============================================================================

def create_review(
    item_id: int,
    item_type: str,
    fsrs_card_state: dict[str, Any],
    due_date: datetime,
    db_path: Path | None = None
) -> int:
    """
    Create a new review entry for a flashcard.

    Args:
        item_id: ID of vocabulary or kanji item
        item_type: 'vocab' or 'kanji'
        fsrs_card_state: FSRS Card state from Card.to_dict()
        due_date: Next review date
        db_path: Database path (optional)

    Returns:
        int: ID of newly created review entry
    """
    with get_cursor(db_path) as cursor:
        cursor.execute("""
            INSERT INTO reviews (
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


def get_review(item_id: int, item_type: str, db_path: Path | None = None) -> Optional[dict[str, Any]]:
    """
    Get review entry for a specific item.

    Args:
        item_id: ID of vocabulary or kanji item
        item_type: 'vocab' or 'kanji'
        db_path: Database path (optional)

    Returns:
        dict or None: Review data, or None if not found
    """
    with get_cursor(db_path) as cursor:
        cursor.execute(
            "SELECT * FROM reviews WHERE item_id = ? AND item_type = ?",
            (item_id, item_type)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def update_review(
    review_id: int,
    fsrs_card_state: dict[str, Any],
    due_date: datetime,
    db_path: Path | None = None
) -> bool:
    """
    Update a review entry with new FSRS state.

    Args:
        review_id: Review ID
        fsrs_card_state: Updated FSRS Card state
        due_date: New due date
        db_path: Database path (optional)

    Returns:
        bool: True if updated, False if not found
    """
    with get_cursor(db_path) as cursor:
        now = datetime.now(timezone.utc)
        cursor.execute("""
            UPDATE reviews
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


def get_due_cards(
    item_type: Optional[str] = None,
    jlpt_level: Optional[str] = None,
    limit: Optional[int] = None,
    db_path: Path | None = None
) -> list[dict[str, Any]]:
    """
    Get cards that are due for review.

    Args:
        item_type: Filter by 'vocab' or 'kanji' (optional)
        jlpt_level: Filter by JLPT level (optional)
        limit: Maximum number of cards (optional)
        db_path: Database path (optional)

    Returns:
        list[dict]: List of due review entries with item data
    """
    with get_cursor(db_path) as cursor:
        now = datetime.now(timezone.utc).isoformat()

        # Base query joins reviews with vocabulary or kanji
        if item_type == "vocab" or item_type is None:
            query_vocab = """
                SELECT r.*, v.word as content, v.reading, v.meanings, v.jlpt_level, 'vocab' as item_type_name
                FROM reviews r
                JOIN vocabulary v ON r.item_id = v.id
                WHERE r.item_type = 'vocab' AND r.due_date <= ?
            """
            params_vocab: list[Any] = [now]

            if jlpt_level:
                query_vocab += " AND v.jlpt_level = ?"
                params_vocab.append(jlpt_level)

        if item_type == "kanji" or item_type is None:
            query_kanji = """
                SELECT r.*, k.character as content, k.vietnamese_reading as reading, k.meanings, k.jlpt_level, 'kanji' as item_type_name
                FROM reviews r
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

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


# ============================================================================
# Review History Queries
# ============================================================================

def add_review_history(
    review_id: int,
    rating: int,
    duration_ms: Optional[int] = None,
    db_path: Path | None = None
) -> int:
    """
    Add a review history entry.

    Args:
        review_id: Review ID
        rating: FSRS rating (1-4)
        duration_ms: Time spent in milliseconds
        db_path: Database path (optional)

    Returns:
        int: ID of newly created history entry
    """
    with get_cursor(db_path) as cursor:
        cursor.execute("""
            INSERT INTO review_history (review_id, rating, duration_ms)
            VALUES (?, ?, ?)
        """, (review_id, rating, duration_ms))
        return cursor.lastrowid


# ============================================================================
# Progress Queries
# ============================================================================

def get_progress(user_id: str = "default", db_path: Path | None = None) -> Optional[dict[str, Any]]:
    """
    Get user progress data.

    Args:
        user_id: User ID (default: "default")
        db_path: Database path (optional)

    Returns:
        dict or None: Progress data, or None if not found
    """
    with get_cursor(db_path) as cursor:
        cursor.execute("SELECT * FROM progress WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def init_progress(
    user_id: str = "default",
    current_level: str = "n5",
    target_level: str = "n5",
    db_path: Path | None = None
) -> int:
    """
    Initialize progress for a user.

    Args:
        user_id: User ID (default: "default")
        current_level: Current JLPT level
        target_level: Target JLPT level
        db_path: Database path (optional)

    Returns:
        int: ID of progress entry
    """
    initial_stats = {
        "total_vocab": 0,
        "total_kanji": 0,
        "mastered_vocab": 0,
        "mastered_kanji": 0,
        "total_reviews": 0,
        "average_retention": 0.0
    }

    with get_cursor(db_path) as cursor:
        cursor.execute("""
            INSERT INTO progress (user_id, current_level, target_level, stats)
            VALUES (?, ?, ?, ?)
        """, (
            user_id,
            current_level,
            target_level,
            json.dumps(initial_stats, ensure_ascii=False)
        ))
        return cursor.lastrowid


def update_progress(
    stats: dict[str, Any],
    user_id: str = "default",
    db_path: Path | None = None
) -> bool:
    """
    Update progress statistics.

    Args:
        stats: Statistics dictionary
        user_id: User ID (default: "default")
        db_path: Database path (optional)

    Returns:
        bool: True if updated, False if not found
    """
    with get_cursor(db_path) as cursor:
        cursor.execute("""
            UPDATE progress
            SET stats = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (json.dumps(stats, ensure_ascii=False), user_id))
        return cursor.rowcount > 0


def increment_streak(user_id: str = "default", db_path: Path | None = None) -> bool:
    """
    Increment the user's study streak.

    Args:
        user_id: User ID (default: "default")
        db_path: Database path (optional)

    Returns:
        bool: True if updated, False if not found
    """
    with get_cursor(db_path) as cursor:
        today = datetime.now(timezone.utc).date()
        cursor.execute("""
            UPDATE progress
            SET streak_days = streak_days + 1,
                last_review_date = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (today.isoformat(), user_id))
        return cursor.rowcount > 0


def update_progress_level(
    current_level: Optional[str] = None,
    target_level: Optional[str] = None,
    user_id: str = "default",
    db_path: Path | None = None
) -> bool:
    """
    Update user's current and/or target JLPT level.

    Args:
        current_level: New current JLPT level (optional, n5/n4/n3/n2/n1)
        target_level: New target JLPT level (optional, n5/n4/n3/n2/n1)
        user_id: User ID (default: "default")
        db_path: Database path (optional)

    Returns:
        bool: True if updated, False if not found

    Example:
        # Update target level to N4
        update_progress_level(target_level="n4")

        # Update both levels
        update_progress_level(current_level="n4", target_level="n3")
    """
    if current_level is None and target_level is None:
        # Nothing to update
        return False

    with get_cursor(db_path) as cursor:
        # Build dynamic UPDATE query based on what's provided
        update_fields = []
        params = []

        if current_level is not None:
            update_fields.append("current_level = ?")
            params.append(current_level)

        if target_level is not None:
            update_fields.append("target_level = ?")
            params.append(target_level)

        update_fields.append("updated_at = CURRENT_TIMESTAMP")

        query = f"""
            UPDATE progress
            SET {', '.join(update_fields)}
            WHERE user_id = ?
        """
        params.append(user_id)

        cursor.execute(query, params)
        return cursor.rowcount > 0
