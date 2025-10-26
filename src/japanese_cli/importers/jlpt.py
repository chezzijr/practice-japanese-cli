"""
JLPT level mapping utilities for filtering vocabulary and kanji by JLPT level.

Loads manual reference lists (CSV/JSON) for each JLPT level and provides
fast lookup methods for filtering during import.
"""

import csv
from pathlib import Path
from typing import Optional, Set, Tuple


class JLPTLevelMapper:
    """
    JLPT level mapper that loads reference lists and provides lookup methods.

    Loads N5 vocabulary and kanji lists from data/dict/ directory and caches
    them in memory for O(1) lookup during import operations.

    Attributes:
        n5_vocab: Set of (word, reading) tuples for N5 vocabulary
        n5_kanji: Set of kanji characters for N5 level
        data_dir: Path to directory containing JLPT reference files
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize JLPT level mapper and load reference lists.

        Args:
            data_dir: Path to data/dict/ directory (defaults to project data/dict/)

        Raises:
            FileNotFoundError: If reference files are not found
            ValueError: If reference files are malformed
        """
        if data_dir is None:
            # Default to project data/dict/ directory
            data_dir = Path(__file__).parent.parent.parent.parent / "data" / "dict"

        self.data_dir = Path(data_dir)

        # Initialize empty sets
        self.n5_vocab: Set[Tuple[str, str]] = set()
        self.n5_kanji: Set[str] = set()

        # Load reference lists
        self._load_n5_vocab()
        self._load_n5_kanji()

    def _load_n5_vocab(self) -> None:
        """
        Load N5 vocabulary list from CSV file.

        Expected CSV format:
            word,reading
            単語,たんご
            ...

        Raises:
            FileNotFoundError: If n5_vocab.csv is not found
            ValueError: If CSV is malformed
        """
        vocab_file = self.data_dir / "n5_vocab.csv"

        if not vocab_file.exists():
            raise FileNotFoundError(
                f"N5 vocabulary file not found: {vocab_file}\n"
                f"Please ensure n5_vocab.csv exists in {self.data_dir}"
            )

        with open(vocab_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            # Validate header
            if "word" not in reader.fieldnames or "reading" not in reader.fieldnames:
                raise ValueError(
                    f"Invalid CSV format in {vocab_file}. "
                    f"Expected headers: word,reading"
                )

            # Load all vocabulary as (word, reading) tuples
            for row in reader:
                word = row["word"].strip()
                reading = row["reading"].strip()

                if word and reading:
                    self.n5_vocab.add((word, reading))

    def _load_n5_kanji(self) -> None:
        """
        Load N5 kanji list from text file.

        Expected format: One kanji character per line

        Raises:
            FileNotFoundError: If n5_kanji.txt is not found
        """
        kanji_file = self.data_dir / "n5_kanji.txt"

        if not kanji_file.exists():
            raise FileNotFoundError(
                f"N5 kanji file not found: {kanji_file}\n"
                f"Please ensure n5_kanji.txt exists in {self.data_dir}"
            )

        with open(kanji_file, "r", encoding="utf-8") as f:
            for line in f:
                kanji = line.strip()
                if kanji:  # Skip empty lines
                    self.n5_kanji.add(kanji)

    def is_n5_vocab(self, word: str, reading: str) -> bool:
        """
        Check if a vocabulary word is in the N5 level.

        Args:
            word: Japanese word (kanji/kana)
            reading: Reading in hiragana/katakana

        Returns:
            bool: True if word is in N5 vocabulary list

        Example:
            >>> mapper = JLPTLevelMapper()
            >>> mapper.is_n5_vocab("単語", "たんご")
            True
            >>> mapper.is_n5_vocab("未知", "みち")
            False
        """
        return (word, reading) in self.n5_vocab

    def is_n5_kanji(self, character: str) -> bool:
        """
        Check if a kanji character is in the N5 level.

        Args:
            character: Single kanji character

        Returns:
            bool: True if kanji is in N5 kanji list

        Example:
            >>> mapper = JLPTLevelMapper()
            >>> mapper.is_n5_kanji("語")
            True
            >>> mapper.is_n5_kanji("鬱")
            False
        """
        return character in self.n5_kanji

    def get_n5_vocab_count(self) -> int:
        """
        Get the total count of N5 vocabulary words.

        Returns:
            int: Number of N5 vocabulary entries
        """
        return len(self.n5_vocab)

    def get_n5_kanji_count(self) -> int:
        """
        Get the total count of N5 kanji.

        Returns:
            int: Number of N5 kanji characters
        """
        return len(self.n5_kanji)

    def __repr__(self) -> str:
        """String representation showing loaded counts."""
        return (
            f"JLPTLevelMapper("
            f"n5_vocab={len(self.n5_vocab)}, "
            f"n5_kanji={len(self.n5_kanji)})"
        )
