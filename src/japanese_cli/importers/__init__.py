"""
Data importers for Japanese learning content.

This module provides importers for various Japanese language data sources:
- JMdict: Japanese-Multilingual Dictionary (vocabulary)
- KANJIDIC2: Kanji character dictionary
- JLPT: Level mapping and filtering
"""

from .jlpt import JLPTLevelMapper
from .jmdict import JMdictImporter, ImportStats
from .kanjidic import KanjidicImporter, KanjiImportStats
from .utils import download_file, decompress_gzip, map_pos, ensure_data_directory

__all__ = [
    "JLPTLevelMapper",
    "JMdictImporter",
    "ImportStats",
    "KanjidicImporter",
    "KanjiImportStats",
    "download_file",
    "decompress_gzip",
    "map_pos",
    "ensure_data_directory",
]
