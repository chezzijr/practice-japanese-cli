"""
JLPT level mapping utilities for filtering vocabulary and kanji by JLPT level.

Loads manual reference lists (CSV/JSON) for each JLPT level and provides
fast lookup methods for filtering during import.
"""

import csv
from pathlib import Path
from typing import Dict, Optional, Set, Tuple

from .utils import download_jlpt_files


class JLPTLevelMapper:
    """
    JLPT level mapper that loads reference lists and provides lookup methods.

    Loads N1-N5 vocabulary and kanji lists from data/dict/ directory and caches
    them in memory for O(1) lookup during import operations.

    Attributes:
        vocab_sets: Dictionary mapping levels to vocabulary sets
        kanji_sets: Dictionary mapping levels to kanji character sets
        data_dir: Path to directory containing JLPT reference files

    Example:
        >>> mapper = JLPTLevelMapper()
        >>> mapper.is_vocab_at_level("単語", "たんご", "n5")
        True
        >>> mapper.is_kanji_at_level("語", "n5")
        True
    """

    VALID_LEVELS = {"n1", "n2", "n3", "n4", "n5"}

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        levels: Optional[set] = None,
        auto_download: bool = True,
    ):
        """
        Initialize JLPT level mapper and load reference lists.

        Uses smart path resolution that checks for project directory first,
        then falls back to user data directory. If files are missing and
        auto_download is True, downloads them from GitHub.

        Args:
            data_dir: Path to data/dict/ directory (defaults to auto-detected path)
            levels: Set of levels to load (default: {"n5"} for backward compatibility)
            auto_download: Auto-download missing files from GitHub (default: True)

        Raises:
            FileNotFoundError: If reference files are not found and auto_download=False
            ValueError: If reference files are malformed or invalid level specified
        """
        if data_dir is None:
            # Smart path resolution: check project dir first, then user data dir
            project_data_dir = Path(__file__).parent.parent.parent.parent / "data" / "dict"
            user_data_dir = Path.home() / ".local" / "share" / "japanese-cli" / "dict"

            # Prefer project directory if it exists (development mode)
            if project_data_dir.exists():
                data_dir = project_data_dir
            else:
                # Otherwise use user data directory (installed mode)
                data_dir = user_data_dir

        self.data_dir = Path(data_dir)
        self.auto_download = auto_download

        # Validate levels
        if levels is None:
            levels = {"n5"}  # Default to N5 only for backward compatibility

        invalid_levels = levels - self.VALID_LEVELS
        if invalid_levels:
            raise ValueError(f"Invalid JLPT levels: {invalid_levels}. Valid levels: {self.VALID_LEVELS}")

        # Initialize dictionaries to store vocab and kanji sets for each level
        self.vocab_sets: Dict[str, Set[Tuple[str, str]]] = {level: set() for level in levels}
        self.kanji_sets: Dict[str, Set[str]] = {level: set() for level in levels}

        # Load reference lists for specified levels
        for level in levels:
            self._load_vocab(level)
            self._load_kanji(level)

        # Backward compatibility: expose N5 sets as attributes
        if "n5" in self.vocab_sets:
            self.n5_vocab = self.vocab_sets["n5"]
            self.n5_kanji = self.kanji_sets["n5"]
        else:
            self.n5_vocab = set()
            self.n5_kanji = set()

    def _load_vocab(self, level: str) -> None:
        """
        Load vocabulary list for a specific JLPT level from CSV file.

        Automatically downloads missing files if auto_download is enabled.

        Args:
            level: JLPT level (n1, n2, n3, n4, or n5)

        Expected CSV format:
            word,reading
            単語,たんご
            ...

        Raises:
            FileNotFoundError: If vocab CSV file is not found and auto_download=False
            ValueError: If CSV is malformed
        """
        vocab_file = self.data_dir / f"{level}_vocab.csv"

        # Auto-download if file doesn't exist
        if not vocab_file.exists():
            if self.auto_download:
                # Try to download the files
                success = download_jlpt_files(level, data_dir=self.data_dir, show_progress=True)
                if not success:
                    raise FileNotFoundError(
                        f"{level.upper()} vocabulary file not found: {vocab_file}\n"
                        f"Auto-download failed. Please ensure {level}_vocab.csv exists in {self.data_dir}"
                    )
            else:
                raise FileNotFoundError(
                    f"{level.upper()} vocabulary file not found: {vocab_file}\n"
                    f"Please ensure {level}_vocab.csv exists in {self.data_dir}\n"
                    f"Or enable auto_download=True to download from GitHub"
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
                word = row.get("word", "").strip() if row.get("word") else ""
                reading = row.get("reading", "").strip() if row.get("reading") else ""

                if word and reading:
                    self.vocab_sets[level].add((word, reading))

    def _load_kanji(self, level: str) -> None:
        """
        Load kanji list for a specific JLPT level from text file.

        Automatically downloads missing files if auto_download is enabled.

        Args:
            level: JLPT level (n1, n2, n3, n4, or n5)

        Expected format: One kanji character per line

        Raises:
            FileNotFoundError: If kanji text file is not found and auto_download=False
        """
        kanji_file = self.data_dir / f"{level}_kanji.txt"

        # Auto-download if file doesn't exist (only if vocab didn't already trigger download)
        if not kanji_file.exists():
            if self.auto_download:
                # Try to download the files (download_jlpt_files handles both vocab and kanji)
                success = download_jlpt_files(level, data_dir=self.data_dir, show_progress=True)
                if not success:
                    raise FileNotFoundError(
                        f"{level.upper()} kanji file not found: {kanji_file}\n"
                        f"Auto-download failed. Please ensure {level}_kanji.txt exists in {self.data_dir}"
                    )
            else:
                raise FileNotFoundError(
                    f"{level.upper()} kanji file not found: {kanji_file}\n"
                    f"Please ensure {level}_kanji.txt exists in {self.data_dir}\n"
                    f"Or enable auto_download=True to download from GitHub"
                )

        with open(kanji_file, "r", encoding="utf-8") as f:
            for line in f:
                kanji = line.strip()
                if kanji:  # Skip empty lines
                    self.kanji_sets[level].add(kanji)

    def is_vocab_at_level(self, word: str, reading: str, level: str) -> bool:
        """
        Check if a vocabulary word is in a specific JLPT level.

        Automatically loads the level data if not already loaded (lazy loading).

        Args:
            word: Japanese word (kanji/kana)
            reading: Reading in hiragana/katakana
            level: JLPT level (n1, n2, n3, n4, or n5)

        Returns:
            bool: True if word is in the specified level's vocabulary list

        Raises:
            ValueError: If level is invalid
            FileNotFoundError: If level data files are not found

        Example:
            >>> mapper = JLPTLevelMapper(levels={"n5"})
            >>> mapper.is_vocab_at_level("単語", "たんご", "n5")
            True
            >>> mapper.is_vocab_at_level("難しい", "むずかしい", "n4")  # Auto-loads N4
            True
        """
        # Validate level
        if level not in self.VALID_LEVELS:
            raise ValueError(f"Invalid level: {level}. Valid levels: {self.VALID_LEVELS}")

        # Lazy load if not already loaded
        if level not in self.vocab_sets:
            self.vocab_sets[level] = set()
            self.kanji_sets[level] = set()
            self._load_vocab(level)
            self._load_kanji(level)

        return (word, reading) in self.vocab_sets[level]

    def is_kanji_at_level(self, character: str, level: str) -> bool:
        """
        Check if a kanji character is in a specific JLPT level.

        Automatically loads the level data if not already loaded (lazy loading).

        Args:
            character: Single kanji character
            level: JLPT level (n1, n2, n3, n4, or n5)

        Returns:
            bool: True if kanji is in the specified level's kanji list

        Raises:
            ValueError: If level is invalid
            FileNotFoundError: If level data files are not found

        Example:
            >>> mapper = JLPTLevelMapper(levels={"n5"})
            >>> mapper.is_kanji_at_level("語", "n5")
            True
            >>> mapper.is_kanji_at_level("難", "n4")  # Auto-loads N4
            True
        """
        # Validate level
        if level not in self.VALID_LEVELS:
            raise ValueError(f"Invalid level: {level}. Valid levels: {self.VALID_LEVELS}")

        # Lazy load if not already loaded
        if level not in self.kanji_sets:
            self.vocab_sets[level] = set()
            self.kanji_sets[level] = set()
            self._load_vocab(level)
            self._load_kanji(level)

        return character in self.kanji_sets[level]

    # Backward compatibility methods for N5
    def _load_n5_vocab(self) -> None:
        """Load N5 vocabulary (backward compatibility wrapper)."""
        self._load_vocab("n5")

    def _load_n5_kanji(self) -> None:
        """Load N5 kanji (backward compatibility wrapper)."""
        self._load_kanji("n5")

    def is_n5_vocab(self, word: str, reading: str) -> bool:
        """
        Check if a vocabulary word is in the N5 level.

        Backward compatibility wrapper for is_vocab_at_level.

        Args:
            word: Japanese word (kanji/kana)
            reading: Reading in hiragana/katakana

        Returns:
            bool: True if word is in N5 vocabulary list

        Example:
            >>> mapper = JLPTLevelMapper()
            >>> mapper.is_n5_vocab("単語", "たんご")
            True
        """
        if "n5" not in self.vocab_sets:
            return False
        return self.is_vocab_at_level(word, reading, "n5")

    def is_n5_kanji(self, character: str) -> bool:
        """
        Check if a kanji character is in the N5 level.

        Backward compatibility wrapper for is_kanji_at_level.

        Args:
            character: Single kanji character

        Returns:
            bool: True if kanji is in N5 kanji list

        Example:
            >>> mapper = JLPTLevelMapper()
            >>> mapper.is_n5_kanji("語")
            True
        """
        if "n5" not in self.kanji_sets:
            return False
        return self.is_kanji_at_level(character, "n5")

    def get_vocab_count(self, level: str) -> int:
        """
        Get the total count of vocabulary words for a specific level.

        Args:
            level: JLPT level (n1, n2, n3, n4, or n5)

        Returns:
            int: Number of vocabulary entries for the level

        Raises:
            ValueError: If level is not loaded
        """
        if level not in self.vocab_sets:
            raise ValueError(f"Level {level} not loaded")
        return len(self.vocab_sets[level])

    def get_kanji_count(self, level: str) -> int:
        """
        Get the total count of kanji for a specific level.

        Args:
            level: JLPT level (n1, n2, n3, n4, or n5)

        Returns:
            int: Number of kanji characters for the level

        Raises:
            ValueError: If level is not loaded
        """
        if level not in self.kanji_sets:
            raise ValueError(f"Level {level} not loaded")
        return len(self.kanji_sets[level])

    def get_n5_vocab_count(self) -> int:
        """
        Get the total count of N5 vocabulary words.

        Backward compatibility wrapper.

        Returns:
            int: Number of N5 vocabulary entries
        """
        if "n5" not in self.vocab_sets:
            return 0
        return self.get_vocab_count("n5")

    def get_n5_kanji_count(self) -> int:
        """
        Get the total count of N5 kanji.

        Backward compatibility wrapper.

        Returns:
            int: Number of N5 kanji characters
        """
        if "n5" not in self.kanji_sets:
            return 0
        return self.get_kanji_count("n5")

    def __repr__(self) -> str:
        """String representation showing loaded levels and counts."""
        level_info = ", ".join([
            f"{level}(vocab={len(self.vocab_sets[level])}, kanji={len(self.kanji_sets[level])})"
            for level in sorted(self.vocab_sets.keys(), reverse=True)
        ])
        return f"JLPTLevelMapper({level_info})"
