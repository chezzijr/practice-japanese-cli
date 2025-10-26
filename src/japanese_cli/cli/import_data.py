"""
CLI commands for importing Japanese learning data.

Provides commands for importing vocabulary and kanji from various sources
filtered by JLPT level.
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from ..importers import JMdictImporter, KanjidicImporter, JLPTLevelMapper


# Create Typer app for import commands
app = typer.Typer(
    name="import",
    help="Import vocabulary and kanji data from external sources",
    no_args_is_help=True,
)

console = Console()


def _import_level(
    level: str,
    vocab: bool,
    kanji: bool,
    all: bool,
    force_download: bool,
    jmdict_path: Optional[Path],
    kanjidic_path: Optional[Path],
):
    """
    Helper function to import vocabulary and kanji for a specific JLPT level.

    Args:
        level: JLPT level (n1, n2, n3, n4, or n5)
        vocab: Import vocabulary only
        kanji: Import kanji only
        all: Import both vocabulary and kanji
        force_download: Force re-download data files
        jmdict_path: Custom JMdict file path
        kanjidic_path: Custom KANJIDIC2 file path
    """
    # Determine what to import
    if not vocab and not kanji and not all:
        # Default: import both
        import_vocab = True
        import_kanji = True
    elif all:
        import_vocab = True
        import_kanji = True
    else:
        import_vocab = vocab
        import_kanji = kanji

    # Display welcome message
    console.print(f"\n[bold blue]Japanese Learning CLI - {level.upper()} Data Import[/bold blue]")
    console.print("=" * 60)

    if import_vocab:
        console.print(f"\n[bold]Importing {level.upper()} Vocabulary...[/bold]")
        try:
            # Create JLPT mapper with the specific level
            jlpt_mapper = JLPTLevelMapper(levels={level})

            # Create importer
            vocab_importer = JMdictImporter(jlpt_mapper=jlpt_mapper)

            # Download if needed (unless custom path provided)
            if jmdict_path is None and force_download:
                jmdict_path = vocab_importer.download_jmdict(force=True)

            # Import vocabulary for the specified level
            stats = vocab_importer.import_vocabulary(
                level=level,
                jmdict_path=jmdict_path,
                download_if_missing=True,
            )

            # Summary
            if stats.imported > 0:
                console.print(f"\n✅ Successfully imported {stats.imported} {level.upper()} vocabulary words!", style="bold green")
            elif stats.skipped > 0:
                console.print(f"\n✅ All {level.upper()} vocabulary already in database ({stats.skipped} words)", style="bold green")
            else:
                console.print(f"\n⚠️ No vocabulary was imported", style="yellow")

        except FileNotFoundError as e:
            console.print(f"\n❌ Error: {e}", style="bold red")
            console.print("Please ensure JMdict file is available or allow automatic download.", style="dim")
            raise typer.Exit(code=1)
        except Exception as e:
            console.print(f"\n❌ Error importing vocabulary: {e}", style="bold red")
            raise typer.Exit(code=1)

    if import_kanji:
        console.print(f"\n[bold]Importing {level.upper()} Kanji...[/bold]")
        try:
            # Create JLPT mapper with the specific level
            jlpt_mapper = JLPTLevelMapper(levels={level})

            # Create importer
            kanji_importer = KanjidicImporter(jlpt_mapper=jlpt_mapper)

            # Download if needed (unless custom path provided)
            if kanjidic_path is None and force_download:
                kanjidic_path = kanji_importer.download_kanjidic(force=True)

            # Import kanji for the specified level
            stats = kanji_importer.import_kanji(
                level=level,
                kanjidic_path=kanjidic_path,
                download_if_missing=True,
            )

            # Summary
            if stats.imported > 0:
                console.print(f"\n✅ Successfully imported {stats.imported} {level.upper()} kanji characters!", style="bold green")
            elif stats.skipped > 0:
                console.print(f"\n✅ All {level.upper()} kanji already in database ({stats.skipped} characters)", style="bold green")
            else:
                console.print(f"\n⚠️ No kanji was imported", style="yellow")

        except FileNotFoundError as e:
            console.print(f"\n❌ Error: {e}", style="bold red")
            console.print("Please ensure KANJIDIC2 file is available or allow automatic download.", style="dim")
            raise typer.Exit(code=1)
        except Exception as e:
            console.print(f"\n❌ Error importing kanji: {e}", style="bold red")
            raise typer.Exit(code=1)

    # Final summary
    console.print("\n" + "=" * 60)
    console.print("[bold green]Import process complete![/bold green]")
    console.print("\nNext steps:")
    console.print("  • Use [bold cyan]japanese-cli flashcard list[/bold cyan] to view imported data")
    console.print("  • Use [bold cyan]japanese-cli flashcard review[/bold cyan] to start studying")
    console.print("  • Use [bold cyan]japanese-cli progress show[/bold cyan] to see your progress\n")


@app.command(name="n5")
def import_n5(
    vocab: bool = typer.Option(False, "--vocab", help="Import N5 vocabulary only"),
    kanji: bool = typer.Option(False, "--kanji", help="Import N5 kanji only"),
    all: bool = typer.Option(False, "--all", help="Import both vocabulary and kanji"),
    force_download: bool = typer.Option(False, "--force", help="Force re-download data files"),
    jmdict_path: Optional[Path] = typer.Option(None, help="Custom JMdict file path"),
    kanjidic_path: Optional[Path] = typer.Option(None, help="Custom KANJIDIC2 file path"),
):
    """
    Import N5 level vocabulary and/or kanji.

    By default (no options), imports both vocabulary and kanji.

    Examples:
        japanese-cli import n5              # Import both vocab and kanji
        japanese-cli import n5 --vocab      # Import vocabulary only
        japanese-cli import n5 --kanji      # Import kanji only
        japanese-cli import n5 --all        # Import both (explicit)
    """
    _import_level("n5", vocab, kanji, all, force_download, jmdict_path, kanjidic_path)


@app.command(name="n4")
def import_n4(
    vocab: bool = typer.Option(False, "--vocab", help="Import N4 vocabulary only"),
    kanji: bool = typer.Option(False, "--kanji", help="Import N4 kanji only"),
    all: bool = typer.Option(False, "--all", help="Import both vocabulary and kanji"),
    force_download: bool = typer.Option(False, "--force", help="Force re-download data files"),
    jmdict_path: Optional[Path] = typer.Option(None, help="Custom JMdict file path"),
    kanjidic_path: Optional[Path] = typer.Option(None, help="Custom KANJIDIC2 file path"),
):
    """
    Import N4 level vocabulary and/or kanji.

    By default (no options), imports both vocabulary and kanji.

    Examples:
        japanese-cli import n4              # Import both vocab and kanji
        japanese-cli import n4 --vocab      # Import vocabulary only
        japanese-cli import n4 --kanji      # Import kanji only
    """
    _import_level("n4", vocab, kanji, all, force_download, jmdict_path, kanjidic_path)


@app.command(name="n3")
def import_n3(
    vocab: bool = typer.Option(False, "--vocab", help="Import N3 vocabulary only"),
    kanji: bool = typer.Option(False, "--kanji", help="Import N3 kanji only"),
    all: bool = typer.Option(False, "--all", help="Import both vocabulary and kanji"),
    force_download: bool = typer.Option(False, "--force", help="Force re-download data files"),
    jmdict_path: Optional[Path] = typer.Option(None, help="Custom JMdict file path"),
    kanjidic_path: Optional[Path] = typer.Option(None, help="Custom KANJIDIC2 file path"),
):
    """
    Import N3 level vocabulary and/or kanji.

    By default (no options), imports both vocabulary and kanji.

    Examples:
        japanese-cli import n3              # Import both vocab and kanji
        japanese-cli import n3 --vocab      # Import vocabulary only
        japanese-cli import n3 --kanji      # Import kanji only
    """
    _import_level("n3", vocab, kanji, all, force_download, jmdict_path, kanjidic_path)


@app.command(name="n2")
def import_n2(
    vocab: bool = typer.Option(False, "--vocab", help="Import N2 vocabulary only"),
    kanji: bool = typer.Option(False, "--kanji", help="Import N2 kanji only"),
    all: bool = typer.Option(False, "--all", help="Import both vocabulary and kanji"),
    force_download: bool = typer.Option(False, "--force", help="Force re-download data files"),
    jmdict_path: Optional[Path] = typer.Option(None, help="Custom JMdict file path"),
    kanjidic_path: Optional[Path] = typer.Option(None, help="Custom KANJIDIC2 file path"),
):
    """
    Import N2 level vocabulary and/or kanji.

    By default (no options), imports both vocabulary and kanji.

    Examples:
        japanese-cli import n2              # Import both vocab and kanji
        japanese-cli import n2 --vocab      # Import vocabulary only
        japanese-cli import n2 --kanji      # Import kanji only
    """
    _import_level("n2", vocab, kanji, all, force_download, jmdict_path, kanjidic_path)


@app.command(name="n1")
def import_n1(
    vocab: bool = typer.Option(False, "--vocab", help="Import N1 vocabulary only"),
    kanji: bool = typer.Option(False, "--kanji", help="Import N1 kanji only"),
    all: bool = typer.Option(False, "--all", help="Import both vocabulary and kanji"),
    force_download: bool = typer.Option(False, "--force", help="Force re-download data files"),
    jmdict_path: Optional[Path] = typer.Option(None, help="Custom JMdict file path"),
    kanjidic_path: Optional[Path] = typer.Option(None, help="Custom KANJIDIC2 file path"),
):
    """
    Import N1 level vocabulary and/or kanji.

    By default (no options), imports both vocabulary and kanji.

    Examples:
        japanese-cli import n1              # Import both vocab and kanji
        japanese-cli import n1 --vocab      # Import vocabulary only
        japanese-cli import n1 --kanji      # Import kanji only
    """
    _import_level("n1", vocab, kanji, all, force_download, jmdict_path, kanjidic_path)
