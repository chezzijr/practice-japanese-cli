"""
MCQ (Multiple Choice Question) generator for Japanese learning.

Dynamically generates multiple-choice questions from vocabulary and kanji items
using intelligent distractor selection strategies.
"""

import json
import random
from pathlib import Path
from typing import Optional

from ..database import get_cursor
from ..models.mcq import MCQQuestion
from ..models.review import ItemType


class MCQGenerator:
    """
    Generates multiple-choice questions dynamically for vocabulary and kanji.

    Uses four intelligent distractor selection strategies:
    1. Same JLPT level - Select from same difficulty level
    2. Similar meanings - Semantic similarity via keyword matching
    3. Similar readings - Phonetic similarity (on-yomi, kun-yomi)
    4. Visually similar - For kanji, similar radicals/strokes
    """

    def __init__(self, db_path: Path | None = None):
        """
        Initialize MCQ generator.

        Args:
            db_path: Path to database (optional)
        """
        self.db_path = db_path

    def _get_effective_language(self, item: dict, requested_language: str) -> str:
        """
        Determine the effective language to use, with fallback to English.

        Args:
            item: Item data dictionary
            requested_language: User's requested language ('vi' or 'en')

        Returns:
            str: The effective language to use ('vi' or 'en')
        """
        meanings = json.loads(item['meanings']) if isinstance(item['meanings'], str) else item['meanings']

        # If requested language exists and has meanings, use it
        if requested_language in meanings and meanings[requested_language]:
            return requested_language

        # Otherwise, fall back to English
        return 'en'

    def generate_question(
        self,
        item_id: int,
        item_type: ItemType,
        question_mode: str = "word_to_meaning",
        language: str = "vi"
    ) -> MCQQuestion:
        """
        Generate a multiple-choice question for an item.

        Args:
            item_id: ID of vocabulary or kanji item
            item_type: Type of item (vocab or kanji)
            question_mode: "word_to_meaning" or "meaning_to_word"
            language: Language for meanings ('vi' or 'en')

        Returns:
            MCQQuestion: Generated question with 4 options

        Raises:
            ValueError: If item not found or insufficient distractors
        """
        # Fetch the item
        if item_type == ItemType.VOCAB:
            item = self._get_vocabulary(item_id)
        else:
            item = self._get_kanji(item_id)

        if not item:
            raise ValueError(f"Item {item_id} ({item_type.value}) not found")

        # Determine effective language (fallback to 'en' if requested language unavailable)
        effective_language = self._get_effective_language(item, language)

        # Generate question based on mode
        if question_mode == "word_to_meaning":
            return self._generate_word_to_meaning(item, item_type, effective_language)
        elif question_mode == "meaning_to_word":
            return self._generate_meaning_to_word(item, item_type, effective_language)
        else:
            raise ValueError(f"Invalid question_mode: {question_mode}")

    def _generate_word_to_meaning(
        self,
        item: dict,
        item_type: ItemType,
        language: str
    ) -> MCQQuestion:
        """
        Generate question: Show word/kanji, ask for meaning.

        Args:
            item: Item data dictionary
            item_type: Type of item
            language: Language for meanings

        Returns:
            MCQQuestion: Question with meaning options
        """
        # Get the word/kanji
        if item_type == ItemType.VOCAB:
            word = item['word']
            reading = item['reading']
            question_text = f"What is the meaning of '{word}' ({reading})?"
        else:
            character = item['character']
            question_text = f"What is the meaning of the kanji '{character}'?"

        # Get correct answer (first meaning in target language)
        # Note: language is guaranteed to exist by _get_effective_language
        meanings = json.loads(item['meanings']) if isinstance(item['meanings'], str) else item['meanings']
        correct_answer = meanings[language][0]  # Use first meaning

        # Get distractors (wrong answers)
        distractors = self._select_distractors(
            item,
            item_type,
            count=3,
            distractor_type="meaning",
            language=language,
            exclude_meaning=correct_answer
        )

        if len(distractors) < 3:
            raise ValueError(f"Insufficient distractors found (got {len(distractors)}, need 3)")

        # Create options and shuffle
        options = [correct_answer] + distractors[:3]
        correct_index = 0  # Track correct answer position before shuffling

        # Shuffle while tracking correct answer
        combined = list(enumerate(options))
        random.shuffle(combined)
        shuffled_indices, shuffled_options = zip(*combined)
        correct_index = shuffled_indices.index(correct_index)

        return MCQQuestion(
            item_id=item['id'],
            item_type=item_type,
            question_text=question_text,
            options=list(shuffled_options),
            correct_index=correct_index,
            jlpt_level=item.get('jlpt_level'),
            explanation=f"'{word if item_type == ItemType.VOCAB else character}' means '{correct_answer}'"
        )

    def _generate_meaning_to_word(
        self,
        item: dict,
        item_type: ItemType,
        language: str
    ) -> MCQQuestion:
        """
        Generate question: Show meaning, ask for word/kanji.

        Args:
            item: Item data dictionary
            item_type: Type of item
            language: Language for meanings

        Returns:
            MCQQuestion: Question with word/kanji options
        """
        # Get the meaning
        # Note: language is guaranteed to exist by _get_effective_language
        meanings = json.loads(item['meanings']) if isinstance(item['meanings'], str) else item['meanings']
        meaning = meanings[language][0]  # Use first meaning
        question_text = f"Which word means '{meaning}'?"

        # Get correct answer (the word/kanji)
        if item_type == ItemType.VOCAB:
            correct_answer = f"{item['word']} ({item['reading']})"
        else:
            correct_answer = item['character']

        # Get distractors
        distractors = self._select_distractors(
            item,
            item_type,
            count=3,
            distractor_type="word",
            language=language
        )

        if len(distractors) < 3:
            raise ValueError(f"Insufficient distractors found (got {len(distractors)}, need 3)")

        # Create options and shuffle
        options = [correct_answer] + distractors[:3]
        correct_index = 0

        # Shuffle while tracking correct answer
        combined = list(enumerate(options))
        random.shuffle(combined)
        shuffled_indices, shuffled_options = zip(*combined)
        correct_index = shuffled_indices.index(correct_index)

        return MCQQuestion(
            item_id=item['id'],
            item_type=item_type,
            question_text=question_text,
            options=list(shuffled_options),
            correct_index=correct_index,
            jlpt_level=item.get('jlpt_level'),
            explanation=f"'{meaning}' is '{correct_answer}'"
        )

    def _select_distractors(
        self,
        item: dict,
        item_type: ItemType,
        count: int,
        distractor_type: str,
        language: str = "vi",
        exclude_meaning: Optional[str] = None
    ) -> list[str]:
        """
        Select distractor answers using multiple strategies.

        Combines all four strategies to create diverse, challenging distractors.

        Args:
            item: The correct item
            item_type: Type of item
            count: Number of distractors needed
            distractor_type: "meaning" or "word"
            language: Language for meanings
            exclude_meaning: Meaning to exclude (for word_to_meaning mode)

        Returns:
            list[str]: List of distractor strings
        """
        all_distractors = []

        # Strategy 1: Same JLPT level (highest priority)
        jlpt_distractors = self._get_same_jlpt_level_distractors(
            item, item_type, distractor_type, language, exclude_meaning
        )
        all_distractors.extend(jlpt_distractors)

        # Strategy 2: Similar meanings (semantic)
        if distractor_type == "meaning" or (distractor_type == "word" and item_type == ItemType.VOCAB):
            similar_meaning_distractors = self._get_similar_meaning_distractors(
                item, item_type, distractor_type, language, exclude_meaning
            )
            all_distractors.extend(similar_meaning_distractors)

        # Strategy 3: Similar readings (phonetic)
        if item_type == ItemType.VOCAB or (item_type == ItemType.KANJI and distractor_type == "word"):
            similar_reading_distractors = self._get_similar_reading_distractors(
                item, item_type, distractor_type, language
            )
            all_distractors.extend(similar_reading_distractors)

        # Strategy 4: Visually similar (for kanji)
        if item_type == ItemType.KANJI:
            visual_distractors = self._get_visually_similar_distractors(
                item, distractor_type, language
            )
            all_distractors.extend(visual_distractors)

        # Remove duplicates while preserving order
        seen = set()
        unique_distractors = []
        for d in all_distractors:
            if d not in seen:
                seen.add(d)
                unique_distractors.append(d)

        # Shuffle and return required count
        random.shuffle(unique_distractors)
        return unique_distractors[:count]

    def _get_same_jlpt_level_distractors(
        self,
        item: dict,
        item_type: ItemType,
        distractor_type: str,
        language: str,
        exclude_meaning: Optional[str] = None
    ) -> list[str]:
        """Get distractors from same JLPT level."""
        jlpt_level = item.get('jlpt_level')
        if not jlpt_level:
            return []

        with get_cursor(self.db_path) as cursor:
            if item_type == ItemType.VOCAB:
                cursor.execute("""
                    SELECT id, word, reading, meanings
                    FROM vocabulary
                    WHERE jlpt_level = ? AND id != ?
                    ORDER BY RANDOM()
                    LIMIT 10
                """, (jlpt_level, item['id']))
            else:
                cursor.execute("""
                    SELECT id, character, meanings
                    FROM kanji
                    WHERE jlpt_level = ? AND id != ?
                    ORDER BY RANDOM()
                    LIMIT 10
                """, (jlpt_level, item['id']))

            rows = cursor.fetchall()

        return self._extract_distractor_text(
            rows, item_type, distractor_type, language, exclude_meaning
        )

    def _get_similar_meaning_distractors(
        self,
        item: dict,
        item_type: ItemType,
        distractor_type: str,
        language: str,
        exclude_meaning: Optional[str] = None
    ) -> list[str]:
        """Get distractors with semantically similar meanings (keyword matching)."""
        # Extract keywords from item's meaning
        meanings = json.loads(item['meanings']) if isinstance(item['meanings'], str) else item['meanings']
        if language not in meanings:
            return []

        # Simple keyword extraction (first word of first meaning)
        keywords = meanings[language][0].lower().split()[:2]  # Use first 2 words

        distractors = []
        with get_cursor(self.db_path) as cursor:
            for keyword in keywords:
                if item_type == ItemType.VOCAB:
                    cursor.execute("""
                        SELECT id, word, reading, meanings
                        FROM vocabulary
                        WHERE id != ? AND meanings LIKE ?
                        ORDER BY RANDOM()
                        LIMIT 5
                    """, (item['id'], f'%{keyword}%'))
                else:
                    cursor.execute("""
                        SELECT id, character, meanings
                        FROM kanji
                        WHERE id != ? AND meanings LIKE ?
                        ORDER BY RANDOM()
                        LIMIT 5
                    """, (item['id'], f'%{keyword}%'))

                rows = cursor.fetchall()
                distractors.extend(self._extract_distractor_text(
                    rows, item_type, distractor_type, language, exclude_meaning
                ))

        return distractors

    def _get_similar_reading_distractors(
        self,
        item: dict,
        item_type: ItemType,
        distractor_type: str,
        language: str
    ) -> list[str]:
        """Get distractors with similar readings (phonetic similarity)."""
        distractors = []

        with get_cursor(self.db_path) as cursor:
            if item_type == ItemType.VOCAB:
                # Match by similar reading (first 2 characters)
                reading_prefix = item['reading'][:2] if len(item['reading']) >= 2 else item['reading']
                cursor.execute("""
                    SELECT id, word, reading, meanings
                    FROM vocabulary
                    WHERE id != ? AND reading LIKE ?
                    ORDER BY RANDOM()
                    LIMIT 5
                """, (item['id'], f'{reading_prefix}%'))
            else:
                # For kanji, match by on/kun readings
                on_readings = json.loads(item.get('on_readings', '[]'))
                if on_readings:
                    # Find kanji with similar on-readings
                    cursor.execute("""
                        SELECT id, character, meanings
                        FROM kanji
                        WHERE id != ? AND on_readings LIKE ?
                        ORDER BY RANDOM()
                        LIMIT 5
                    """, (item['id'], f'%{on_readings[0]}%'))

            rows = cursor.fetchall()
            distractors.extend(self._extract_distractor_text(
                rows, item_type, distractor_type, language, None
            ))

        return distractors

    def _get_visually_similar_distractors(
        self,
        item: dict,
        distractor_type: str,
        language: str
    ) -> list[str]:
        """Get kanji distractors with similar radicals or stroke counts."""
        distractors = []
        radical = item.get('radical')
        stroke_count = item.get('stroke_count')

        with get_cursor(self.db_path) as cursor:
            # Strategy 1: Same radical
            if radical:
                cursor.execute("""
                    SELECT id, character, meanings
                    FROM kanji
                    WHERE id != ? AND radical = ?
                    ORDER BY RANDOM()
                    LIMIT 3
                """, (item['id'], radical))
                rows = cursor.fetchall()
                distractors.extend(self._extract_distractor_text(
                    rows, ItemType.KANJI, distractor_type, language, None
                ))

            # Strategy 2: Similar stroke count (±2)
            if stroke_count:
                cursor.execute("""
                    SELECT id, character, meanings
                    FROM kanji
                    WHERE id != ? AND stroke_count BETWEEN ? AND ?
                    ORDER BY RANDOM()
                    LIMIT 3
                """, (item['id'], stroke_count - 2, stroke_count + 2))
                rows = cursor.fetchall()
                distractors.extend(self._extract_distractor_text(
                    rows, ItemType.KANJI, distractor_type, language, None
                ))

        return distractors

    def _extract_distractor_text(
        self,
        rows: list,
        item_type: ItemType,
        distractor_type: str,
        language: str,
        exclude_meaning: Optional[str] = None
    ) -> list[str]:
        """
        Extract distractor text from database rows.

        Args:
            rows: Database rows
            item_type: Type of item
            distractor_type: "meaning" or "word"
            language: Language for meanings
            exclude_meaning: Meaning to exclude

        Returns:
            list[str]: Extracted distractor strings
        """
        distractors = []

        for row in rows:
            row_dict = dict(row)
            meanings = json.loads(row_dict['meanings']) if isinstance(row_dict['meanings'], str) else row_dict['meanings']

            if distractor_type == "meaning":
                # Extract meaning with fallback to English
                effective_lang = language if (language in meanings and meanings[language]) else 'en'
                if effective_lang in meanings and meanings[effective_lang]:
                    meaning = meanings[effective_lang][0]
                    if exclude_meaning and meaning == exclude_meaning:
                        continue
                    distractors.append(meaning)
            else:
                # Extract word/kanji
                if item_type == ItemType.VOCAB:
                    word = row_dict['word']
                    reading = row_dict['reading']
                    distractors.append(f"{word} ({reading})")
                else:
                    distractors.append(row_dict['character'])

        return distractors

    def _get_vocabulary(self, vocab_id: int) -> Optional[dict]:
        """Get vocabulary item by ID."""
        with get_cursor(self.db_path) as cursor:
            cursor.execute("SELECT * FROM vocabulary WHERE id = ?", (vocab_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def _get_kanji(self, kanji_id: int) -> Optional[dict]:
        """Get kanji item by ID."""
        with get_cursor(self.db_path) as cursor:
            cursor.execute("SELECT * FROM kanji WHERE id = ?", (kanji_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
