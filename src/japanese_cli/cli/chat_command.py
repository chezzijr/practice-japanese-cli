"""Chat command for AI-powered Japanese learning assistant."""

import os
import sys
import typer
from rich.console import Console
from rich.prompt import Prompt

from japanese_cli.ai.chat import start_chat


app = typer.Typer(help="AI-powered chat assistant for Japanese learning")
console = Console()


@app.callback(invoke_without_command=True)
def chat(
    ctx: typer.Context,
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed tool usage and internal operations"
    ),
    model: str = typer.Option(
        "claude-haiku-4-5-20251001",
        "--model",
        "-m",
        help="Claude model to use (default: Haiku 4.5, fast and cost-effective)"
    ),
    temperature: float = typer.Option(
        0.7,
        "--temperature",
        "-t",
        help="Response temperature (0.0-1.0, higher = more creative)",
        min=0.0,
        max=1.0,
    ),
    streaming: bool = typer.Option(
        False,
        "--streaming",
        "-s",
        help="Use async streaming for responses (experimental)"
    ),
    api_key: str = typer.Option(
        None,
        "--api-key",
        help="Anthropic API key (default: from ANTHROPIC_API_KEY env var or .env file)",
        envvar="ANTHROPIC_API_KEY",
    ),
):
    """
    Start an interactive AI chat session for Japanese learning.

    The AI assistant can help you with:

    • Searching and explaining vocabulary and kanji

    • Tracking your learning progress and statistics

    • Checking what reviews are due

    • Providing personalized study recommendations

    \b
    Examples:
        # Start basic chat
        japanese-cli chat

        # Verbose mode to see tool usage
        japanese-cli chat --verbose

        # Use different temperature for more creative responses
        japanese-cli chat --temperature 0.9

        # Use a different Claude model
        japanese-cli chat --model claude-3-opus-20240229

    \b
    Requirements:
        API key can be provided via:
        1. .env file: ANTHROPIC_API_KEY=your_key
        2. Environment variable: export ANTHROPIC_API_KEY=your_key
        3. Will prompt interactively if not found

    Get an API key from: https://console.anthropic.com/
    """
    # Check if this is a subcommand call
    if ctx.invoked_subcommand is not None:
        return

    # Check for API key
    if not api_key:
        # In interactive mode (TTY), prompt for API key
        if sys.stdin.isatty():
            console.print("[yellow]API key not found. You can:[/yellow]")
            console.print("  1. Create [cyan].env[/cyan] file: [dim]echo 'ANTHROPIC_API_KEY=your_key' > .env[/dim]")
            console.print("  2. Set environment variable: [dim]export ANTHROPIC_API_KEY=your_key[/dim]")
            console.print("  3. Enter it now (will only be used for this session)\n")

            try:
                api_key = Prompt.ask(
                    "[cyan]Enter your Anthropic API key[/cyan]",
                    password=True
                )

                # Validate API key format
                if not api_key or not api_key.strip():
                    console.print("[red]No API key entered. Exiting.[/red]")
                    raise typer.Exit(code=1)

                api_key = api_key.strip()

                if not api_key.startswith('sk-ant-'):
                    console.print(f"[yellow]Warning:[/yellow] API key doesn't start with 'sk-ant-'")
                    console.print("This might not be a valid Anthropic API key, but continuing...\n")

                console.print("[green]✓[/green] API key received. Starting chat...\n")

            except (KeyboardInterrupt, EOFError):
                console.print("\n[yellow]Cancelled. No API key entered.[/yellow]")
                raise typer.Exit(code=1)

        else:
            # Non-interactive mode (piped input, scripts, CI)
            console.print("[bold red]Error:[/bold red] Anthropic API key not found.\n")
            console.print("Please set your API key using one of these methods:\n")
            console.print("1. Create .env file:")
            console.print("   [cyan]echo 'ANTHROPIC_API_KEY=your_key' > .env[/cyan]\n")
            console.print("2. Environment variable:")
            console.print("   [cyan]export ANTHROPIC_API_KEY=your_api_key_here[/cyan]\n")
            console.print("3. Command option:")
            console.print("   [cyan]japanese-cli chat --api-key your_api_key_here[/cyan]\n")
            console.print("Get an API key from: [blue]https://console.anthropic.com/[/blue]")
            raise typer.Exit(code=1)

    # Validate model name
    if not model.startswith("claude-"):
        console.print(f"[bold yellow]Warning:[/bold yellow] '{model}' doesn't look like a Claude model name.")
        console.print("Continuing anyway, but you may encounter errors.\n")

    # Start chat session
    try:
        start_chat(
            api_key=api_key,
            model_id=model,
            temperature=temperature,
            verbose=verbose,
            use_async=streaming,
        )
    except KeyboardInterrupt:
        console.print("\n[cyan]Chat session ended. さようなら！[/cyan]")
    except Exception as e:
        console.print(f"[bold red]Error starting chat:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
