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
    console.print("\n[bold blue]Japanese Learning CLI - N5 Data Import[/bold blue]")
    console.print("=" * 60)

    if import_vocab:
        console.print("\n[bold]Importing N5 Vocabulary...[/bold]")
        try:
            # Create JLPT mapper
            jlpt_mapper = JLPTLevelMapper()

            # Create importer
            vocab_importer = JMdictImporter(jlpt_mapper=jlpt_mapper)

            # Download if needed (unless custom path provided)
            if jmdict_path is None and force_download:
                jmdict_path = vocab_importer.download_jmdict(force=True)

            # Import vocabulary
            stats = vocab_importer.import_n5_vocabulary(
                jmdict_path=jmdict_path,
                download_if_missing=True,
            )

            # Summary
            if stats.imported > 0:
                console.print(f"\n✅ Successfully imported {stats.imported} N5 vocabulary words!", style="bold green")
            elif stats.skipped > 0:
                console.print(f"\n✅ All N5 vocabulary already in database ({stats.skipped} words)", style="bold green")
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
        console.print("\n[bold]Importing N5 Kanji...[/bold]")
        try:
            # Create JLPT mapper (if not already created)
            jlpt_mapper = JLPTLevelMapper()

            # Create importer
            kanji_importer = KanjidicImporter(jlpt_mapper=jlpt_mapper)

            # Download if needed (unless custom path provided)
            if kanjidic_path is None and force_download:
                kanjidic_path = kanji_importer.download_kanjidic(force=True)

            # Import kanji
            stats = kanji_importer.import_n5_kanji(
                kanjidic_path=kanjidic_path,
                download_if_missing=True,
            )

            # Summary
            if stats.imported > 0:
                console.print(f"\n✅ Successfully imported {stats.imported} N5 kanji characters!", style="bold green")
            elif stats.skipped > 0:
                console.print(f"\n✅ All N5 kanji already in database ({stats.skipped} characters)", style="bold green")
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
