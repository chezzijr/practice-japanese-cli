"""
Integration tests for data importers.

Tests the JMdict and KANJIDIC2 importers with sample XML files.
"""

import pytest
from pathlib import Path
from japanese_cli.importers import JMdictImporter, KanjidicImporter, JLPTLevelMapper
from japanese_cli.database.queries import list_all_vocabulary, list_all_kanji


@pytest.fixture
def sample_xml_dir():
    """Path to sample XML files directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def jlpt_data_dir():
    """Path to JLPT reference files."""
    return Path(__file__).parent.parent / "data" / "dict"


def test_jmdict_importer_with_sample_xml(clean_db, sample_xml_dir, jlpt_data_dir):
    """Test that JMdictImporter can parse sample XML and import N5 vocab."""
    sample_jmdict = sample_xml_dir / "sample_jmdict.xml"
    assert sample_jmdict.exists(), f"Sample JMdict not found at {sample_jmdict}"

    # Create importer with test database
    mapper = JLPTLevelMapper(data_dir=jlpt_data_dir)
    importer = JMdictImporter(jlpt_mapper=mapper, db_path=clean_db)

    # Import from sample XML (don't download)
    stats = importer.import_n5_vocabulary(
        jmdict_path=sample_jmdict,
        download_if_missing=False
    )

    # Verify statistics
    # Sample has 6 entries: 大学, 学校, 先生, 歩く, 青い are N5 (5 total)
    # 複雑 is not N5, should be filtered
    assert stats.imported >= 1, "Should import at least 1 N5 word"
    assert stats.filtered >= 1, "Should filter at least 1 non-N5 word"

    # Verify data was inserted into database
    vocab_list = list_all_vocabulary(db_path=clean_db)
    assert len(vocab_list) >= 1, "Should have vocabulary in database"


def test_kanjidic_importer_with_sample_xml(clean_db, sample_xml_dir, jlpt_data_dir):
    """Test that KanjidicImporter can parse sample XML and import N5 kanji."""
    sample_kanjidic = sample_xml_dir / "sample_kanjidic.xml"
    assert sample_kanjidic.exists(), f"Sample KANJIDIC2 not found at {sample_kanjidic}"

    # Create importer with test database
    mapper = JLPTLevelMapper(data_dir=jlpt_data_dir)
    importer = KanjidicImporter(jlpt_mapper=mapper, db_path=clean_db)

    # Import from sample XML (don't download)
    stats = importer.import_n5_kanji(
        kanjidic_path=sample_kanjidic,
        download_if_missing=False
    )

    # Verify statistics
    # Sample has 5 characters: 一, 二, 語, 学 are N5 (4 total)
    # 鬱 is not N5, should be filtered
    assert stats.imported >= 1, "Should import at least 1 N5 kanji"
    assert stats.filtered >= 1, "Should filter at least 1 non-N5 kanji"

    # Verify data was inserted into database
    kanji_list = list_all_kanji(db_path=clean_db)
    assert len(kanji_list) >= 1, "Should have kanji in database"


def test_jmdict_importer_duplicate_handling(clean_db, sample_xml_dir, jlpt_data_dir):
    """Test that JMdictImporter handles duplicates correctly."""
    sample_jmdict = sample_xml_dir / "sample_jmdict.xml"

    mapper = JLPTLevelMapper(data_dir=jlpt_data_dir)
    importer = JMdictImporter(jlpt_mapper=mapper, db_path=clean_db)

    # First import
    stats1 = importer.import_n5_vocabulary(
        jmdict_path=sample_jmdict,
        download_if_missing=False
    )
    imported_count = stats1.imported

    # Second import (should skip duplicates)
    stats2 = importer.import_n5_vocabulary(
        jmdict_path=sample_jmdict,
        download_if_missing=False
    )

    # Second import should skip all previously imported words
    assert stats2.imported == 0, "Should not import duplicates"
    assert stats2.skipped >= imported_count, "Should skip previously imported words"


def test_kanjidic_importer_duplicate_handling(clean_db, sample_xml_dir, jlpt_data_dir):
    """Test that KanjidicImporter handles duplicates correctly."""
    sample_kanjidic = sample_xml_dir / "sample_kanjidic.xml"

    mapper = JLPTLevelMapper(data_dir=jlpt_data_dir)
    importer = KanjidicImporter(jlpt_mapper=mapper, db_path=clean_db)

    # First import
    stats1 = importer.import_n5_kanji(
        kanjidic_path=sample_kanjidic,
        download_if_missing=False
    )
    imported_count = stats1.imported

    # Second import (should skip duplicates)
    stats2 = importer.import_n5_kanji(
        kanjidic_path=sample_kanjidic,
        download_if_missing=False
    )

    # Second import should skip all previously imported kanji
    assert stats2.imported == 0, "Should not import duplicates"
    assert stats2.skipped >= imported_count, "Should skip previously imported kanji"


def test_jmdict_parser_yields_correct_structure(sample_xml_dir, jlpt_data_dir):
    """Test that JMdict parser yields correctly structured data."""
    sample_jmdict = sample_xml_dir / "sample_jmdict.xml"

    mapper = JLPTLevelMapper(data_dir=jlpt_data_dir)
    importer = JMdictImporter(jlpt_mapper=mapper)

    entries = list(importer.parse_jmdict(sample_jmdict))

    assert len(entries) > 0, "Should parse at least one entry"

    # Check structure of first entry
    entry = entries[0]
    assert 'word' in entry
    assert 'reading' in entry
    assert 'meanings' in entry
    assert isinstance(entry['meanings'], list)
    assert len(entry['meanings']) > 0


def test_kanjidic_parser_yields_correct_structure(sample_xml_dir, jlpt_data_dir):
    """Test that KANJIDIC2 parser yields correctly structured data."""
    sample_kanjidic = sample_xml_dir / "sample_kanjidic.xml"

    mapper = JLPTLevelMapper(data_dir=jlpt_data_dir)
    importer = KanjidicImporter(jlpt_mapper=mapper)

    entries = list(importer.parse_kanjidic(sample_kanjidic))

    assert len(entries) > 0, "Should parse at least one entry"

    # Check structure of first entry
    entry = entries[0]
    assert 'character' in entry
    assert 'on_readings' in entry
    assert 'kun_readings' in entry
    assert 'meanings' in entry
    assert isinstance(entry['meanings'], list)
    assert len(entry['meanings']) > 0


# ============================================================================
# Multi-level Import Tests (N1-N5)
# ============================================================================

@pytest.mark.parametrize("level", ["n1", "n2", "n3", "n4", "n5"])
def test_jmdict_import_vocabulary_all_levels(clean_db, sample_xml_dir, jlpt_data_dir, level):
    """Test that import_vocabulary works for all JLPT levels."""
    sample_jmdict = sample_xml_dir / "sample_jmdict.xml"

    # Create mapper with specific level
    mapper = JLPTLevelMapper(data_dir=jlpt_data_dir, levels={level})
    importer = JMdictImporter(jlpt_mapper=mapper, db_path=clean_db)

    # Import vocabulary for this level
    stats = importer.import_vocabulary(
        level=level,
        jmdict_path=sample_jmdict,
        download_if_missing=False
    )

    # Should process entries (may import 0 if no sample matches this level)
    assert stats.imported + stats.filtered + stats.skipped > 0

    # Verify any imported vocab has correct JLPT level
    vocab_list = list_all_vocabulary(jlpt_level=level, db_path=clean_db)
    for vocab in vocab_list:
        assert vocab['jlpt_level'] == level


@pytest.mark.parametrize("level", ["n1", "n2", "n3", "n4", "n5"])
def test_kanjidic_import_kanji_all_levels(clean_db, sample_xml_dir, jlpt_data_dir, level):
    """Test that import_kanji works for all JLPT levels."""
    sample_kanjidic = sample_xml_dir / "sample_kanjidic.xml"

    # Create mapper with specific level
    mapper = JLPTLevelMapper(data_dir=jlpt_data_dir, levels={level})
    importer = KanjidicImporter(jlpt_mapper=mapper, db_path=clean_db)

    # Import kanji for this level
    stats = importer.import_kanji(
        level=level,
        kanjidic_path=sample_kanjidic,
        download_if_missing=False
    )

    # Should process entries (may import 0 if no sample matches this level)
    assert stats.imported + stats.filtered + stats.skipped > 0

    # Verify any imported kanji has correct JLPT level
    kanji_list = list_all_kanji(jlpt_level=level, db_path=clean_db)
    for kanji in kanji_list:
        assert kanji['jlpt_level'] == level


def test_jmdict_import_invalid_level(clean_db, sample_xml_dir, jlpt_data_dir):
    """Test that import_vocabulary raises error for invalid level."""
    sample_jmdict = sample_xml_dir / "sample_jmdict.xml"

    mapper = JLPTLevelMapper(data_dir=jlpt_data_dir)
    importer = JMdictImporter(jlpt_mapper=mapper, db_path=clean_db)

    # Should raise ValueError for invalid level
    with pytest.raises(ValueError, match="Invalid JLPT level"):
        importer.import_vocabulary(
            level="n6",  # Invalid
            jmdict_path=sample_jmdict,
            download_if_missing=False
        )


def test_kanjidic_import_invalid_level(clean_db, sample_xml_dir, jlpt_data_dir):
    """Test that import_kanji raises error for invalid level."""
    sample_kanjidic = sample_xml_dir / "sample_kanjidic.xml"

    mapper = JLPTLevelMapper(data_dir=jlpt_data_dir)
    importer = KanjidicImporter(jlpt_mapper=mapper, db_path=clean_db)

    # Should raise ValueError for invalid level
    with pytest.raises(ValueError, match="Invalid JLPT level"):
        importer.import_kanji(
            level="invalid",
            kanjidic_path=sample_kanjidic,
            download_if_missing=False
        )


def test_jlpt_mapper_lazy_loading(jlpt_data_dir):
    """Test that JLPTLevelMapper lazy-loads levels as needed."""
    # Start with only N5 loaded
    mapper = JLPTLevelMapper(data_dir=jlpt_data_dir, levels={"n5"})

    # N5 should be loaded
    assert "n5" in mapper.vocab_sets
    assert "n5" in mapper.kanji_sets
    assert len(mapper.vocab_sets["n5"]) > 0
    assert len(mapper.kanji_sets["n5"]) > 0

    # N4 should not be loaded yet
    assert "n4" not in mapper.vocab_sets
    assert "n4" not in mapper.kanji_sets

    # Access N4 - should trigger lazy loading
    is_n4 = mapper.is_vocab_at_level("難しい", "むずかしい", "n4")

    # N4 should now be loaded
    assert "n4" in mapper.vocab_sets
    assert "n4" in mapper.kanji_sets
    assert len(mapper.vocab_sets["n4"]) > 0
    assert len(mapper.kanji_sets["n4"]) > 0


def test_backward_compatibility_methods(clean_db, sample_xml_dir, jlpt_data_dir):
    """Test that old N5-specific methods still work (backward compatibility)."""
    sample_jmdict = sample_xml_dir / "sample_jmdict.xml"
    sample_kanjidic = sample_xml_dir / "sample_kanjidic.xml"

    # Test JMdictImporter.import_n5_vocabulary
    mapper = JLPTLevelMapper(data_dir=jlpt_data_dir)
    vocab_importer = JMdictImporter(jlpt_mapper=mapper, db_path=clean_db)

    stats = vocab_importer.import_n5_vocabulary(
        jmdict_path=sample_jmdict,
        download_if_missing=False
    )

    assert stats.imported + stats.filtered + stats.skipped > 0

    # Test KanjidicImporter.import_n5_kanji
    kanji_importer = KanjidicImporter(jlpt_mapper=mapper, db_path=clean_db)

    stats = kanji_importer.import_n5_kanji(
        kanjidic_path=sample_kanjidic,
        download_if_missing=False
    )

    assert stats.imported + stats.filtered + stats.skipped > 0

    # All imported items should be N5
    vocab_list = list_all_vocabulary(db_path=clean_db)
    for vocab in vocab_list:
        assert vocab['jlpt_level'] == 'n5'

    kanji_list = list_all_kanji(db_path=clean_db)
    for kanji in kanji_list:
        assert kanji['jlpt_level'] == 'n5'


def test_multiple_levels_in_same_database(clean_db, sample_xml_dir, jlpt_data_dir):
    """Test that multiple JLPT levels can coexist in the same database."""
    sample_jmdict = sample_xml_dir / "sample_jmdict.xml"
    sample_kanjidic = sample_xml_dir / "sample_kanjidic.xml"

    # Import N5 vocabulary
    mapper_n5 = JLPTLevelMapper(data_dir=jlpt_data_dir, levels={"n5"})
    importer_n5 = JMdictImporter(jlpt_mapper=mapper_n5, db_path=clean_db)
    stats_n5 = importer_n5.import_vocabulary(
        level="n5",
        jmdict_path=sample_jmdict,
        download_if_missing=False
    )

    # Import N4 vocabulary (different level)
    mapper_n4 = JLPTLevelMapper(data_dir=jlpt_data_dir, levels={"n4"})
    importer_n4 = JMdictImporter(jlpt_mapper=mapper_n4, db_path=clean_db)
    stats_n4 = importer_n4.import_vocabulary(
        level="n4",
        jmdict_path=sample_jmdict,
        download_if_missing=False
    )

    # Verify both levels exist in database
    n5_vocab = list_all_vocabulary(jlpt_level="n5", db_path=clean_db)
    n4_vocab = list_all_vocabulary(jlpt_level="n4", db_path=clean_db)

    # Should have separate entries for each level
    for vocab in n5_vocab:
        assert vocab['jlpt_level'] == 'n5'
    for vocab in n4_vocab:
        assert vocab['jlpt_level'] == 'n4'
