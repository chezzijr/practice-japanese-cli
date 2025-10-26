"""
Integration tests for data importers.

Tests the JMdict and KANJIDIC2 importers with sample XML files.
"""

import pytest
from pathlib import Path
from japanese_cli.importers import JMdictImporter, KanjidicImporter, JLPTLevelMapper
from japanese_cli.database.queries import list_vocabulary, list_kanji


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
    vocab_list = list_vocabulary(db_path=clean_db)
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
    kanji_list = list_kanji(db_path=clean_db)
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
