"""
KANJIDIC2 XML parser for importing Japanese kanji.

Parses KANJIDIC2 XML files and imports kanji characters filtered by JLPT level.
"""

import gzip
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Iterator
from lxml import etree

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

from ..database.queries import add_kanji, get_kanji_by_character
from ..models import Kanji
from .jlpt import JLPTLevelMapper
from .utils import download_file, decompress_gzip, ensure_data_directory


@dataclass
class KanjiImportStats:
    """Statistics from kanji import operation."""
    imported: int = 0
    updated: int = 0
    skipped: int = 0
    filtered: int = 0  # Filtered out (not N5)
    errors: int = 0


class KanjidicImporter:
    """
    Importer for KANJIDIC2 kanji data.

    Downloads and parses KANJIDIC2 XML file, filtering by JLPT level and
    importing kanji entries into the database.

    Attributes:
        jlpt_mapper: JLPT level mapper for filtering
        data_dir: Directory for storing downloaded files
        console: Rich console for output
    """

    # Official KANJIDIC2 download URL
    KANJIDIC_URL = "https://www.edrdg.org/kanjidic/kanjidic2.xml.gz"

    def __init__(
        self,
        jlpt_mapper: Optional[JLPTLevelMapper] = None,
        data_dir: Optional[Path] = None,
        db_path: Optional[Path] = None,
    ):
        """
        Initialize KANJIDIC2 importer.

        Args:
            jlpt_mapper: JLPT level mapper (creates new if None)
            data_dir: Data directory path (defaults to project data/dict/)
            db_path: Database path (defaults to project database)
        """
        self.jlpt_mapper = jlpt_mapper or JLPTLevelMapper()
        self.data_dir = ensure_data_directory(data_dir)
        self.db_path = db_path
        self.console = Console()

    def download_kanjidic(self, force: bool = False) -> Path:
        """
        Download kanjidic2.xml.gz file from EDRDG.

        Args:
            force: Force re-download even if file exists

        Returns:
            Path: Path to downloaded .gz file

        Raises:
            requests.RequestException: If download fails
        """
        dest = self.data_dir / "kanjidic2.xml.gz"

        if dest.exists() and not force:
            self.console.print(f"✓ KANJIDIC2 file already exists: {dest}", style="dim")
            return dest

        self.console.print(f"Downloading KANJIDIC2 from {self.KANJIDIC_URL}...", style="blue")
        return download_file(self.KANJIDIC_URL, dest, show_progress=True)

    def parse_kanjidic(self, file_path: Path) -> Iterator[dict]:
        """
        Parse KANJIDIC2 XML file and yield kanji entries.

        Uses iterparse for memory-efficient streaming.

        Args:
            file_path: Path to KANJIDIC2 XML file (can be .gz or .xml)

        Yields:
            dict: Kanji data dictionary with keys:
                - character: Kanji character
                - on_readings: List of on-yomi readings
                - kun_readings: List of kun-yomi readings
                - meanings: List of English meanings
                - stroke_count: Number of strokes
                - radical: Radical character (if available)

        Example:
            >>> for entry in importer.parse_kanjidic(Path("kanjidic2.xml")):
            ...     print(entry["character"], entry["meanings"])
            一 ['one']
            二 ['two']
        """
        # Handle gzipped files
        if file_path.suffix == '.gz':
            file_handle = gzip.open(file_path, 'rb')
        else:
            file_handle = open(file_path, 'rb')

        try:
            # Use iterparse for memory-efficient parsing
            context = etree.iterparse(file_handle, events=('end',), tag='character')

            for event, char_elem in context:
                try:
                    # Extract literal (the kanji character)
                    literal = char_elem.find('literal')
                    if literal is None or not literal.text:
                        continue

                    character = literal.text

                    # Extract stroke count
                    misc = char_elem.find('misc')
                    stroke_count = None
                    if misc is not None:
                        stroke_elem = misc.find('stroke_count')
                        if stroke_elem is not None and stroke_elem.text:
                            try:
                                stroke_count = int(stroke_elem.text)
                            except ValueError:
                                pass

                    # Extract radical
                    radical_elem = char_elem.find('radical')
                    radical = None
                    if radical_elem is not None:
                        rad_value = radical_elem.find('rad_value')
                        if rad_value is not None and rad_value.text:
                            # Store radical number as string for now
                            radical = rad_value.text

                    # Extract readings and meanings
                    reading_meaning = char_elem.find('reading_meaning')
                    if reading_meaning is None:
                        continue

                    rmgroup = reading_meaning.find('rmgroup')
                    if rmgroup is None:
                        continue

                    # Get on-yomi readings (katakana)
                    on_readings = []
                    kun_readings = []
                    for reading in rmgroup.findall('reading'):
                        r_type = reading.get('r_type')
                        if r_type == 'ja_on' and reading.text:
                            on_readings.append(reading.text)
                        elif r_type == 'ja_kun' and reading.text:
                            kun_readings.append(reading.text)

                    # Get meanings (English)
                    meanings = []
                    for meaning in rmgroup.findall('meaning'):
                        # Only get English meanings (no m_lang attribute)
                        if not meaning.get('m_lang') and meaning.text:
                            meanings.append(meaning.text)

                    if not meanings:
                        continue  # Skip if no English meanings

                    yield {
                        'character': character,
                        'on_readings': on_readings,
                        'kun_readings': kun_readings,
                        'meanings': meanings,
                        'stroke_count': stroke_count,
                        'radical': radical,
                    }

                except Exception as e:
                    # Skip malformed entries
                    self.console.print(
                        f"⚠ Skipped malformed kanji entry: {e}",
                        style="yellow"
                    )
                    continue
                finally:
                    # Clear element to free memory
                    char_elem.clear()
                    while char_elem.getprevious() is not None:
                        del char_elem.getparent()[0]

            del context

        finally:
            file_handle.close()

    def import_n5_kanji(
        self,
        kanjidic_path: Optional[Path] = None,
        download_if_missing: bool = True,
    ) -> KanjiImportStats:
        """
        Import N5 kanji from KANJIDIC2.

        Args:
            kanjidic_path: Path to KANJIDIC2 file (downloads if None)
            download_if_missing: Download file if not found

        Returns:
            KanjiImportStats: Statistics about the import operation

        Example:
            >>> importer = KanjidicImporter()
            >>> stats = importer.import_n5_kanji()
            >>> print(f"Imported {stats.imported} kanji")
        """
        stats = KanjiImportStats()

        # Download if path not provided
        if kanjidic_path is None:
            kanjidic_path = self.data_dir / "kanjidic2.xml.gz"
            if not kanjidic_path.exists() and download_if_missing:
                kanjidic_path = self.download_kanjidic()
            elif not kanjidic_path.exists():
                raise FileNotFoundError(f"KANJIDIC2 file not found: {kanjidic_path}")

        self.console.print("\nImporting N5 kanji from KANJIDIC2...", style="bold blue")

        # Parse and import with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed} characters processed"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Parsing KANJIDIC2...", total=None)

            for kanji_data in self.parse_kanjidic(kanjidic_path):
                character = kanji_data['character']

                # Filter by N5 level
                if not self.jlpt_mapper.is_n5_kanji(character):
                    stats.filtered += 1
                    progress.update(task, advance=1)
                    continue

                # Check for duplicates
                existing = get_kanji_by_character(character, db_path=self.db_path)

                if existing:
                    # Compare data to decide if update is needed
                    # For now, skip existing kanji
                    stats.skipped += 1
                    progress.update(task, advance=1)
                    continue

                # Create new kanji entry
                try:
                    add_kanji(
                        character=character,
                        on_readings=kanji_data['on_readings'],
                        kun_readings=kanji_data['kun_readings'],
                        meanings={'en': kanji_data['meanings']},
                        vietnamese_reading=None,  # Not available in KANJIDIC2
                        jlpt_level='n5',
                        stroke_count=kanji_data['stroke_count'],
                        radical=kanji_data['radical'],
                        notes=None,
                        db_path=self.db_path,
                    )
                    stats.imported += 1

                except Exception as e:
                    self.console.print(
                        f"⚠ Error importing {character}: {e}",
                        style="red"
                    )
                    stats.errors += 1

                progress.update(task, advance=1)

        # Display results
        self.console.print("\n[bold green]Kanji import complete![/bold green]")
        self.console.print(f"  Imported: {stats.imported}")
        self.console.print(f"  Updated: {stats.updated}")
        self.console.print(f"  Skipped (duplicates): {stats.skipped}")
        self.console.print(f"  Filtered (non-N5): {stats.filtered}")
        if stats.errors > 0:
            self.console.print(f"  Errors: {stats.errors}", style="red")

        return stats
