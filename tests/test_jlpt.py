"""
Tests for JLPT level mapper functionality.

Tests the JLPTLevelMapper class that loads and provides lookup methods for
JLPT level reference lists.
"""

import csv
import pytest
from pathlib import Path
from japanese_cli.importers.jlpt import JLPTLevelMapper


@pytest.fixture
def temp_jlpt_dir(tmp_path):
    """Create temporary directory with sample JLPT reference files."""
    jlpt_dir = tmp_path / "jlpt_data"
    jlpt_dir.mkdir()

    # Create sample N5 vocabulary CSV
    vocab_file = jlpt_dir / "n5_vocab.csv"
    with open(vocab_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["word", "reading"])
        writer.writerow(["単語", "たんご"])
        writer.writerow(["学校", "がっこう"])
        writer.writerow(["日本", "にほん"])
        writer.writerow(["大学", "だいがく"])
        writer.writerow(["先生", "せんせい"])

    # Create sample N5 kanji text file
    kanji_file = jlpt_dir / "n5_kanji.txt"
    with open(kanji_file, "w", encoding="utf-8") as f:
        f.write("一\n")
        f.write("二\n")
        f.write("三\n")
        f.write("日\n")
        f.write("本\n")
        f.write("語\n")
        f.write("学\n")
        f.write("校\n")

    return jlpt_dir


# ============================================================================
# Initialization Tests
# ============================================================================

def test_init_with_valid_directory(temp_jlpt_dir):
    """Test that JLPTLevelMapper initializes correctly with valid directory."""
    mapper = JLPTLevelMapper(data_dir=temp_jlpt_dir)

    assert isinstance(mapper.n5_vocab, set)
    assert isinstance(mapper.n5_kanji, set)
    assert len(mapper.n5_vocab) == 5
    assert len(mapper.n5_kanji) == 8


def test_init_missing_vocab_file(tmp_path):
    """Test that initialization fails when vocab file is missing."""
    # Create directory with only kanji file
    jlpt_dir = tmp_path / "jlpt_data"
    jlpt_dir.mkdir()

    kanji_file = jlpt_dir / "n5_kanji.txt"
    with open(kanji_file, "w", encoding="utf-8") as f:
        f.write("一\n")

    with pytest.raises(FileNotFoundError, match="N5 vocabulary file not found"):
        JLPTLevelMapper(data_dir=jlpt_dir)


def test_init_missing_kanji_file(tmp_path):
    """Test that initialization fails when kanji file is missing."""
    # Create directory with only vocab file
    jlpt_dir = tmp_path / "jlpt_data"
    jlpt_dir.mkdir()

    vocab_file = jlpt_dir / "n5_vocab.csv"
    with open(vocab_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["word", "reading"])
        writer.writerow(["単語", "たんご"])

    with pytest.raises(FileNotFoundError, match="N5 kanji file not found"):
        JLPTLevelMapper(data_dir=jlpt_dir)


def test_init_malformed_vocab_csv(tmp_path):
    """Test that initialization fails with malformed vocab CSV."""
    jlpt_dir = tmp_path / "jlpt_data"
    jlpt_dir.mkdir()

    # Create vocab file with wrong headers
    vocab_file = jlpt_dir / "n5_vocab.csv"
    with open(vocab_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["invalid", "headers"])  # Wrong headers
        writer.writerow(["単語", "たんご"])

    kanji_file = jlpt_dir / "n5_kanji.txt"
    with open(kanji_file, "w", encoding="utf-8") as f:
        f.write("一\n")

    with pytest.raises(ValueError, match="Invalid CSV format"):
        JLPTLevelMapper(data_dir=jlpt_dir)


# ============================================================================
# Vocabulary Lookup Tests
# ============================================================================

def test_is_n5_vocab_positive(temp_jlpt_dir):
    """Test that is_n5_vocab returns True for N5 words."""
    mapper = JLPTLevelMapper(data_dir=temp_jlpt_dir)

    assert mapper.is_n5_vocab("単語", "たんご") is True
    assert mapper.is_n5_vocab("学校", "がっこう") is True
    assert mapper.is_n5_vocab("日本", "にほん") is True


def test_is_n5_vocab_negative(temp_jlpt_dir):
    """Test that is_n5_vocab returns False for non-N5 words."""
    mapper = JLPTLevelMapper(data_dir=temp_jlpt_dir)

    assert mapper.is_n5_vocab("未知", "みち") is False
    assert mapper.is_n5_vocab("複雑", "ふくざつ") is False
    assert mapper.is_n5_vocab("存在", "そんざい") is False


def test_is_n5_vocab_case_sensitive(temp_jlpt_dir):
    """Test that vocab lookup is case-sensitive for readings."""
    mapper = JLPTLevelMapper(data_dir=temp_jlpt_dir)

    # Correct reading
    assert mapper.is_n5_vocab("単語", "たんご") is True

    # Wrong reading (even if word is correct)
    assert mapper.is_n5_vocab("単語", "タンゴ") is False


def test_is_n5_vocab_requires_both_word_and_reading(temp_jlpt_dir):
    """Test that both word and reading must match."""
    mapper = JLPTLevelMapper(data_dir=temp_jlpt_dir)

    # Correct combination
    assert mapper.is_n5_vocab("単語", "たんご") is True

    # Correct word, wrong reading
    assert mapper.is_n5_vocab("単語", "がっこう") is False

    # Wrong word, correct reading
    assert mapper.is_n5_vocab("学校", "たんご") is False


# ============================================================================
# Kanji Lookup Tests
# ============================================================================

def test_is_n5_kanji_positive(temp_jlpt_dir):
    """Test that is_n5_kanji returns True for N5 kanji."""
    mapper = JLPTLevelMapper(data_dir=temp_jlpt_dir)

    assert mapper.is_n5_kanji("一") is True
    assert mapper.is_n5_kanji("二") is True
    assert mapper.is_n5_kanji("日") is True
    assert mapper.is_n5_kanji("本") is True
    assert mapper.is_n5_kanji("語") is True


def test_is_n5_kanji_negative(temp_jlpt_dir):
    """Test that is_n5_kanji returns False for non-N5 kanji."""
    mapper = JLPTLevelMapper(data_dir=temp_jlpt_dir)

    assert mapper.is_n5_kanji("鬱") is False
    assert mapper.is_n5_kanji("薔") is False
    assert mapper.is_n5_kanji("憂") is False


def test_is_n5_kanji_with_hiragana(temp_jlpt_dir):
    """Test that hiragana characters are not considered N5 kanji."""
    mapper = JLPTLevelMapper(data_dir=temp_jlpt_dir)

    assert mapper.is_n5_kanji("あ") is False
    assert mapper.is_n5_kanji("ん") is False


# ============================================================================
# Count Methods Tests
# ============================================================================

def test_get_n5_vocab_count(temp_jlpt_dir):
    """Test that get_n5_vocab_count returns correct count."""
    mapper = JLPTLevelMapper(data_dir=temp_jlpt_dir)
    assert mapper.get_n5_vocab_count() == 5


def test_get_n5_kanji_count(temp_jlpt_dir):
    """Test that get_n5_kanji_count returns correct count."""
    mapper = JLPTLevelMapper(data_dir=temp_jlpt_dir)
    assert mapper.get_n5_kanji_count() == 8


# ============================================================================
# Edge Cases and Data Handling Tests
# ============================================================================

def test_empty_lines_in_kanji_file_ignored(tmp_path):
    """Test that empty lines in kanji file are ignored."""
    jlpt_dir = tmp_path / "jlpt_data"
    jlpt_dir.mkdir()

    vocab_file = jlpt_dir / "n5_vocab.csv"
    with open(vocab_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["word", "reading"])
        writer.writerow(["単語", "たんご"])

    kanji_file = jlpt_dir / "n5_kanji.txt"
    with open(kanji_file, "w", encoding="utf-8") as f:
        f.write("一\n")
        f.write("\n")  # Empty line
        f.write("二\n")
        f.write("  \n")  # Whitespace only
        f.write("三\n")

    mapper = JLPTLevelMapper(data_dir=jlpt_dir)
    assert mapper.get_n5_kanji_count() == 3


def test_whitespace_stripped_from_csv(tmp_path):
    """Test that whitespace is stripped from CSV entries."""
    jlpt_dir = tmp_path / "jlpt_data"
    jlpt_dir.mkdir()

    vocab_file = jlpt_dir / "n5_vocab.csv"
    with open(vocab_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["word", "reading"])
        writer.writerow([" 単語 ", " たんご "])  # With whitespace

    kanji_file = jlpt_dir / "n5_kanji.txt"
    with open(kanji_file, "w", encoding="utf-8") as f:
        f.write("一\n")

    mapper = JLPTLevelMapper(data_dir=jlpt_dir)

    # Should match even without whitespace in lookup
    assert mapper.is_n5_vocab("単語", "たんご") is True


def test_repr(temp_jlpt_dir):
    """Test that __repr__ returns informative string."""
    mapper = JLPTLevelMapper(data_dir=temp_jlpt_dir)
    repr_str = repr(mapper)

    assert "JLPTLevelMapper" in repr_str
    assert "n5_vocab=5" in repr_str
    assert "n5_kanji=8" in repr_str


# ============================================================================
# Integration with Real Data Files
# ============================================================================

def test_with_real_data_files():
    """Test with actual N5 reference files in data/dict/."""
    # This test uses the real data files created in data/dict/
    data_dir = Path(__file__).parent.parent / "data" / "dict"

    # Skip if files don't exist (e.g., in CI without data files)
    if not (data_dir / "n5_vocab.csv").exists():
        pytest.skip("Real N5 data files not found")

    mapper = JLPTLevelMapper(data_dir=data_dir)

    # Should have loaded vocabulary and kanji
    assert mapper.get_n5_vocab_count() > 0
    assert mapper.get_n5_kanji_count() == 79  # Actual count in n5_kanji.txt file

    # Test some known N5 words
    assert mapper.is_n5_vocab("大学", "だいがく") is True

    # Test some known N5 kanji
    assert mapper.is_n5_kanji("一") is True
    assert mapper.is_n5_kanji("語") is True
    assert mapper.is_n5_kanji("学") is True
