"""
Shared utility functions for data importers.

Provides common functionality for downloading files, decompressing archives,
and mapping data formats.
"""

import gzip
import shutil
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
    BarColumn,
    TextColumn,
)


# Part of speech entity mapping from JMdict to readable strings
POS_MAPPING = {
    "n": "noun",
    "v": "verb",
    "adj": "adjective",
    "adv": "adverb",
    "pron": "pronoun",
    "conj": "conjunction",
    "int": "interjection",
    "pref": "prefix",
    "suf": "suffix",
    "exp": "expression",
    "num": "numeric",
    "ctr": "counter",
}


def download_file(
    url: str,
    dest: Path,
    show_progress: bool = True,
    max_retries: int = 3,
    timeout: int = 30,
) -> Path:
    """
    Download a file from URL with progress bar and retry logic.

    Args:
        url: URL to download from
        dest: Destination file path
        show_progress: Whether to show Rich progress bar (default: True)
        max_retries: Maximum number of retry attempts (default: 3)
        timeout: Request timeout in seconds (default: 30)

    Returns:
        Path: Path to downloaded file

    Raises:
        requests.RequestException: If download fails after all retries
        IOError: If file cannot be written

    Example:
        >>> download_file(
        ...     "http://example.com/dict.gz",
        ...     Path("data/dict.gz")
        ... )
        Path('data/dict.gz')
    """
    console = Console()
    dest = Path(dest)

    # Ensure parent directory exists
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Parse URL to get filename if not specified
    if not dest.name:
        parsed_url = urlparse(url)
        filename = Path(parsed_url.path).name
        dest = dest / filename

    # Retry logic with exponential backoff
    for attempt in range(max_retries):
        try:
            # Send HEAD request to get file size
            head_response = requests.head(url, timeout=timeout, allow_redirects=True)
            head_response.raise_for_status()
            total_size = int(head_response.headers.get('content-length', 0))

            # Download with streaming
            with requests.get(url, stream=True, timeout=timeout) as response:
                response.raise_for_status()

                if show_progress and total_size > 0:
                    # Create Rich progress bar
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[bold blue]{task.fields[filename]}"),
                        BarColumn(),
                        DownloadColumn(),
                        TransferSpeedColumn(),
                        TimeRemainingColumn(),
                        console=console,
                    ) as progress:
                        task = progress.add_task(
                            "download",
                            total=total_size,
                            filename=dest.name
                        )

                        with open(dest, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    progress.update(task, advance=len(chunk))
                else:
                    # Download without progress bar
                    with open(dest, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)

            console.print(f"✓ Downloaded: {dest}", style="green")
            return dest

        except requests.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                console.print(
                    f"⚠ Download failed (attempt {attempt + 1}/{max_retries}), "
                    f"retrying in {wait_time}s...",
                    style="yellow"
                )
                time.sleep(wait_time)
            else:
                console.print(f"✗ Download failed after {max_retries} attempts", style="red")
                raise

    # Should never reach here, but satisfy type checker
    raise requests.RequestException(f"Failed to download {url}")


def decompress_gzip(source: Path, dest: Optional[Path] = None, remove_source: bool = False) -> Path:
    """
    Decompress a gzip file.

    Args:
        source: Path to .gz file
        dest: Destination path (defaults to source without .gz extension)
        remove_source: Whether to remove source file after decompression

    Returns:
        Path: Path to decompressed file

    Raises:
        FileNotFoundError: If source file doesn't exist
        IOError: If decompression fails

    Example:
        >>> decompress_gzip(Path("data/dict.xml.gz"))
        Path('data/dict.xml')
    """
    console = Console()
    source = Path(source)

    if not source.exists():
        raise FileNotFoundError(f"Source file not found: {source}")

    # Determine destination path
    if dest is None:
        if source.suffix == '.gz':
            dest = source.with_suffix('')
        else:
            dest = source.parent / f"{source.stem}_decompressed"

    dest = Path(dest)

    # Decompress
    console.print(f"Decompressing {source.name}...", style="blue")

    with gzip.open(source, 'rb') as f_in:
        with open(dest, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    console.print(f"✓ Decompressed: {dest}", style="green")

    # Optionally remove source
    if remove_source:
        source.unlink()
        console.print(f"✓ Removed source: {source}", style="dim")

    return dest


def map_pos(pos_entity: str) -> str:
    """
    Map JMdict part-of-speech entity to readable string.

    Args:
        pos_entity: Entity reference (e.g., "n", "v", "adj")

    Returns:
        str: Human-readable part of speech (e.g., "noun", "verb")

    Example:
        >>> map_pos("n")
        'noun'
        >>> map_pos("v")
        'verb'
        >>> map_pos("unknown")
        'unknown'
    """
    return POS_MAPPING.get(pos_entity, pos_entity)


def ensure_data_directory(data_dir: Optional[Path] = None) -> Path:
    """
    Ensure data directory exists and return its path.

    Uses smart path resolution that checks for project directory first,
    then falls back to user data directory.

    Args:
        data_dir: Custom data directory path (defaults to auto-detected path)

    Returns:
        Path: Path to data directory

    Example:
        >>> ensure_data_directory()
        Path('~/.local/share/japanese-cli/dict')  # or project data/dict in dev mode
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

    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    return data_dir


def download_jlpt_files(
    level: str,
    data_dir: Optional[Path] = None,
    force: bool = False,
    show_progress: bool = True,
) -> bool:
    """
    Download JLPT vocabulary and kanji reference files for a specific level.

    Downloads from GitHub repository if files don't exist locally.
    Files are downloaded to the user data directory (~/.local/share/japanese-cli/dict/).

    Args:
        level: JLPT level (n1, n2, n3, n4, or n5)
        data_dir: Target directory (defaults to user data directory)
        force: Force re-download even if files exist
        show_progress: Whether to show download progress

    Returns:
        bool: True if files are available (downloaded or already exist), False otherwise

    Raises:
        ValueError: If level is invalid
        requests.RequestException: If download fails

    Example:
        >>> download_jlpt_files("n5")
        True
        >>> download_jlpt_files("n3", force=True)  # Re-download N3 files
        True
    """
    console = Console()

    # Validate level
    valid_levels = {"n1", "n2", "n3", "n4", "n5"}
    if level not in valid_levels:
        raise ValueError(f"Invalid level: {level}. Valid levels: {valid_levels}")

    # Determine data directory (always use user data directory for downloads)
    if data_dir is None:
        data_dir = Path.home() / ".local" / "share" / "japanese-cli" / "dict"

    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    # Define file paths
    vocab_file = data_dir / f"{level}_vocab.csv"
    kanji_file = data_dir / f"{level}_kanji.txt"

    # Check if files already exist (unless force=True)
    if not force and vocab_file.exists() and kanji_file.exists():
        console.print(f"✓ {level.upper()} files already exist", style="dim green")
        return True

    # GitHub raw content URLs
    base_url = "https://raw.githubusercontent.com/chezzijr/practice-japanese-cli/main/data/dict"
    vocab_url = f"{base_url}/{level}_vocab.csv"
    kanji_url = f"{base_url}/{level}_kanji.txt"

    try:
        console.print(f"\n[bold blue]Downloading {level.upper()} reference files...[/bold blue]")

        # Download vocabulary file
        if force or not vocab_file.exists():
            console.print(f"  Downloading {level}_vocab.csv...")
            download_file(vocab_url, vocab_file, show_progress=show_progress)

        # Download kanji file
        if force or not kanji_file.exists():
            console.print(f"  Downloading {level}_kanji.txt...")
            download_file(kanji_url, kanji_file, show_progress=show_progress)

        console.print(f"✓ {level.upper()} files downloaded successfully\n", style="bold green")
        return True

    except requests.RequestException as e:
        console.print(
            f"[bold red]Failed to download {level.upper()} files from GitHub[/bold red]\n"
            f"Error: {str(e)}\n"
            f"Please check your internet connection or download files manually from:\n"
            f"  {vocab_url}\n"
            f"  {kanji_url}",
            style="red"
        )
        return False
