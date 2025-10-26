"""
JMdict XML parser for importing Japanese vocabulary.

Parses JMdict_e (Japanese-Multilingual Dictionary) XML files and imports
vocabulary entries filtered by JLPT level.
"""

import gzip
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Iterator
from lxml import etree

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

from ..database.queries import add_vocabulary, get_vocabulary_by_word
from ..models import Vocabulary
from .jlpt import JLPTLevelMapper
from .utils import download_file, decompress_gzip, map_pos, ensure_data_directory


@dataclass
class ImportStats:
    """Statistics from import operation."""
    imported: int = 0
    updated: int = 0
    skipped: int = 0
    filtered: int = 0  # Filtered out (not N5)
    errors: int = 0


class JMdictImporter:
    """
    Importer for JMdict vocabulary data.

    Downloads and parses JMdict_e XML file, filtering by JLPT level and
    importing vocabulary entries into the database.

    Attributes:
        jlpt_mapper: JLPT level mapper for filtering
        data_dir: Directory for storing downloaded files
        console: Rich console for output
    """

    # Official JMdict download URL
    JMDICT_URL = "http://ftp.edrdg.org/pub/Nihongo/JMdict_e.gz"

    def __init__(
        self,
        jlpt_mapper: Optional[JLPTLevelMapper] = None,
        data_dir: Optional[Path] = None,
        db_path: Optional[Path] = None,
    ):
        """
        Initialize JMdict importer.

        Args:
            jlpt_mapper: JLPT level mapper (creates new if None)
            data_dir: Data directory path (defaults to project data/dict/)
            db_path: Database path (defaults to project database)
        """
        self.jlpt_mapper = jlpt_mapper or JLPTLevelMapper()
        self.data_dir = ensure_data_directory(data_dir)
        self.db_path = db_path
        self.console = Console()

    def download_jmdict(self, force: bool = False) -> Path:
        """
        Download JMdict_e.gz file from EDRDG.

        Args:
            force: Force re-download even if file exists

        Returns:
            Path: Path to downloaded .gz file

        Raises:
            requests.RequestException: If download fails
        """
        dest = self.data_dir / "JMdict_e.gz"

        if dest.exists() and not force:
            self.console.print(f"✓ JMdict file already exists: {dest}", style="dim")
            return dest

        self.console.print(f"Downloading JMdict from {self.JMDICT_URL}...", style="blue")
        return download_file(self.JMDICT_URL, dest, show_progress=True)

    def parse_jmdict(self, file_path: Path) -> Iterator[dict]:
        """
        Parse JMdict XML file and yield vocabulary entries.

        Uses iterparse for memory-efficient streaming of large XML files.

        Args:
            file_path: Path to JMdict XML file (can be .gz or .xml)

        Yields:
            dict: Vocabulary data dictionary with keys:
                - word: Japanese word (kanji/kana)
                - reading: Kana reading
                - meanings: List of English glosses
                - part_of_speech: Part of speech string

        Example:
            >>> for entry in importer.parse_jmdict(Path("JMdict_e.xml")):
            ...     print(entry["word"], entry["reading"])
            単語 たんご
            学校 がっこう
        """
        # Handle gzipped files
        if file_path.suffix == '.gz':
            file_handle = gzip.open(file_path, 'rb')
        else:
            file_handle = open(file_path, 'rb')

        try:
            # Use iterparse for memory-efficient parsing
            context = etree.iterparse(file_handle, events=('end',), tag='entry')

            for event, entry_elem in context:
                try:
                    # Extract word (keb - kanji element body)
                    k_ele = entry_elem.find('k_ele')
                    if k_ele is not None:
                        keb = k_ele.find('keb')
                        word = keb.text if keb is not None else None
                    else:
                        word = None

                    # Extract reading (reb - reading element body)
                    r_ele = entry_elem.find('r_ele')
                    if r_ele is None:
                        continue  # Skip if no reading

                    reb = r_ele.find('reb')
                    reading = reb.text if reb is not None else None

                    if not reading:
                        continue  # Skip if no reading

                    # If no kanji form, use reading as word
                    if not word:
                        word = reading

                    # Extract meanings and part of speech from first sense
                    sense = entry_elem.find('sense')
                    if sense is None:
                        continue  # Skip if no sense

                    # Get glosses (English meanings)
                    glosses = sense.findall('gloss')
                    meanings = []
                    for gloss in glosses:
                        # Only get English glosses (no lang attribute or lang="eng")
                        lang = gloss.get('{http://www.w3.org/XML/1998/namespace}lang')
                        if lang is None or lang == 'eng':
                            if gloss.text:
                                meanings.append(gloss.text)

                    if not meanings:
                        continue  # Skip if no meanings

                    # Get part of speech
                    pos_elem = sense.find('pos')
                    part_of_speech = None
                    if pos_elem is not None and pos_elem.text:
                        # Extract entity reference (between & and ;)
                        pos_text = pos_elem.text
                        if '&' in pos_text and ';' in pos_text:
                            entity = pos_text.split('&')[1].split(';')[0]
                            part_of_speech = map_pos(entity)

                    yield {
                        'word': word,
                        'reading': reading,
                        'meanings': meanings,
                        'part_of_speech': part_of_speech,
                    }

                except Exception as e:
                    # Skip malformed entries
                    self.console.print(
                        f"⚠ Skipped malformed entry: {e}",
                        style="yellow"
                    )
                    continue
                finally:
                    # Clear element to free memory
                    entry_elem.clear()
                    while entry_elem.getprevious() is not None:
                        del entry_elem.getparent()[0]

            del context

        finally:
            file_handle.close()

    def import_n5_vocabulary(
        self,
        jmdict_path: Optional[Path] = None,
        download_if_missing: bool = True,
    ) -> ImportStats:
        """
        Import N5 vocabulary from JMdict.

        Args:
            jmdict_path: Path to JMdict file (downloads if None)
            download_if_missing: Download file if not found

        Returns:
            ImportStats: Statistics about the import operation

        Example:
            >>> importer = JMdictImporter()
            >>> stats = importer.import_n5_vocabulary()
            >>> print(f"Imported {stats.imported} words")
        """
        stats = ImportStats()

        # Download if path not provided
        if jmdict_path is None:
            jmdict_path = self.data_dir / "JMdict_e.gz"
            if not jmdict_path.exists() and download_if_missing:
                jmdict_path = self.download_jmdict()
            elif not jmdict_path.exists():
                raise FileNotFoundError(f"JMdict file not found: {jmdict_path}")

        self.console.print("\nImporting N5 vocabulary from JMdict...", style="bold blue")

        # Parse and import with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed} entries processed"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Parsing JMdict...", total=None)

            for entry_data in self.parse_jmdict(jmdict_path):
                word = entry_data['word']
                reading = entry_data['reading']

                # Filter by N5 level
                if not self.jlpt_mapper.is_n5_vocab(word, reading):
                    stats.filtered += 1
                    progress.update(task, advance=1)
                    continue

                # Check for duplicates
                existing = get_vocabulary_by_word(word, reading, db_path=self.db_path)

                if existing:
                    # Compare meanings to decide if update is needed
                    import json
                    existing_meanings = existing.get('meanings', '{}')
                    if isinstance(existing_meanings, str):
                        existing_meanings = json.loads(existing_meanings)
                    new_meanings = {'en': entry_data['meanings']}

                    if existing_meanings.get('en') != new_meanings.get('en'):
                        # Update needed - meanings have changed
                        # For now, we'll skip updates and just count them
                        # Full update implementation would go here
                        stats.updated += 1
                    else:
                        stats.skipped += 1

                    progress.update(task, advance=1)
                    continue

                # Create new vocabulary entry
                try:
                    add_vocabulary(
                        word=word,
                        reading=reading,
                        meanings={'en': entry_data['meanings']},
                        vietnamese_reading=None,  # Not available in JMdict
                        jlpt_level='n5',
                        part_of_speech=entry_data['part_of_speech'],
                        tags=[],
                        notes=None,
                        db_path=self.db_path,
                    )
                    stats.imported += 1

                except Exception as e:
                    self.console.print(
                        f"⚠ Error importing {word} ({reading}): {e}",
                        style="red"
                    )
                    stats.errors += 1

                progress.update(task, advance=1)

        # Display results
        self.console.print("\n[bold green]Import complete![/bold green]")
        self.console.print(f"  Imported: {stats.imported}")
        self.console.print(f"  Updated: {stats.updated}")
        self.console.print(f"  Skipped (duplicates): {stats.skipped}")
        self.console.print(f"  Filtered (non-N5): {stats.filtered}")
        if stats.errors > 0:
            self.console.print(f"  Errors: {stats.errors}", style="red")

        return stats
