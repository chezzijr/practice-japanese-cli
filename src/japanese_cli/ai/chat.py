"""Interactive chat interface for the AI agent."""

import asyncio
import sys
from io import StringIO
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text
from rich.prompt import Prompt
from rich.live import Live
from rich.spinner import Spinner

from japanese_cli.ai.agent import create_agent


class ChatSession:
    """Interactive chat session with the Japanese learning AI assistant."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_id: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.7,
        verbose: bool = False,
    ):
        """
        Initialize a chat session.

        Args:
            api_key: Anthropic API key
            model_id: Claude model to use
            temperature: Response temperature
            verbose: Show detailed tool usage information
        """
        self.console = Console()
        self.verbose = verbose

        # Create agent
        try:
            self.agent = create_agent(
                api_key=api_key,
                model_id=model_id,
                temperature=temperature,
            )
        except ValueError as e:
            self.console.print(f"[bold red]Error:[/bold red] {str(e)}")
            raise

    def display_welcome(self):
        """Display welcome message."""
        welcome_text = """
# 日本語学習アシスタント (Japanese Learning Assistant) 🇯🇵

Welcome! I'm your AI-powered Japanese learning companion.

## What I Can Help With:

* **📚 Vocabulary & Kanji** - Search and explain Japanese words and characters
* **📊 Progress Tracking** - View your learning statistics and achievements
* **📝 Review Planning** - Check what's due for flashcard or MCQ review
* **🎯 Study Recommendations** - Get personalized study advice

## Example Questions:

* "Show me N5 vocabulary about food"
* "What kanji should I study today?"
* "How is my progress?"
* "What reviews are due?"
* "Explain the difference between は and が"

Type your question or command below. Type `quit`, `exit`, or press Ctrl+C to leave.

頑張ってください！(Good luck with your studies!)
        """
        self.console.print(Panel(Markdown(welcome_text), border_style="cyan"))
        self.console.print()

    def display_user_message(self, message: str):
        """Display user's input message."""
        user_text = Text(f"You: ", style="bold cyan")
        user_text.append(message, style="cyan")
        self.console.print(user_text)
        self.console.print()

    def display_tool_usage(self, message: dict):
        """Display information about tool calls (verbose mode)."""
        if not self.verbose:
            return

        for content in message.get("content", []):
            if "toolUse" in content:
                tool_use = content["toolUse"]
                tool_name = tool_use.get("name", "unknown")
                tool_input = tool_use.get("input", {})

                tool_info = Text(f"🔧 Using tool: ", style="dim yellow")
                tool_info.append(tool_name, style="bold yellow")
                tool_info.append(f" with {tool_input}", style="dim yellow")
                self.console.print(tool_info)

    def display_assistant_message(self, text: str):
        """Display assistant's response."""
        # Format as markdown for better rendering
        md = Markdown(text)
        panel = Panel(
            md,
            title="[bold green]Assistant[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
        self.console.print(panel)
        self.console.print()

    def display_error(self, error: str):
        """Display error message."""
        self.console.print(f"[bold red]Error:[/bold red] {error}")
        self.console.print()

    async def stream_response_async(self, user_input: str):
        """
        Stream the agent's response asynchronously.

        Args:
            user_input: User's message/question
        """
        response_text = ""

        # Save original stdout to restore later
        original_stdout = sys.stdout
        stdout_buffer = StringIO()

        try:
            # Show thinking indicator while streaming
            with Live(
                Spinner("dots", text="Thinking...", style="cyan"),
                console=self.console,
                transient=True,
            ):
                # Temporarily redirect stdout to suppress duplicate output from strands library
                # The strands library may print streamed chunks directly to stdout
                sys.stdout = stdout_buffer

                try:
                    # Stream the response
                    async for event in self.agent.stream_async(user_input):
                        if "data" in event:
                            response_text += event["data"]
                        elif "result" in event:
                            # Check tool usage in verbose mode
                            if self.verbose and hasattr(self.agent, "messages"):
                                # Restore stdout temporarily for tool usage display
                                sys.stdout = original_stdout
                                for msg in self.agent.messages[-3:]:
                                    self.display_tool_usage(msg)
                                sys.stdout = stdout_buffer
                finally:
                    # Always restore stdout
                    sys.stdout = original_stdout

            # Display the complete response with proper formatting
            # This ensures we show a nicely formatted version in a Rich panel once
            if response_text:
                self.display_assistant_message(response_text)
            else:
                self.display_error("No response received from agent")

        except Exception as e:
            # Ensure stdout is restored even on error
            sys.stdout = original_stdout
            self.display_error(f"Error during response: {str(e)}")

    def get_sync_response(self, user_input: str):
        """
        Get a synchronous response from the agent.

        Args:
            user_input: User's message/question
        """
        # Save original stdout to restore later
        original_stdout = sys.stdout
        stdout_buffer = StringIO()

        try:
            # Show thinking indicator
            with self.console.status("[cyan]Thinking...", spinner="dots"):
                # Temporarily redirect stdout to suppress duplicate output from strands library
                # The strands Agent.__call__ may print responses directly to stdout
                sys.stdout = stdout_buffer
                try:
                    result = self.agent(user_input)
                finally:
                    # Always restore stdout after agent call
                    sys.stdout = original_stdout

            # Check tool usage in verbose mode (stdout already restored)
            if self.verbose and hasattr(self.agent, "messages"):
                for msg in self.agent.messages[-3:]:
                    self.display_tool_usage(msg)

            # Extract and display response with proper formatting
            # This ensures we show a nicely formatted version in a Rich panel once
            if result.message and "content" in result.message:
                for content in result.message["content"]:
                    if "text" in content:
                        self.display_assistant_message(content["text"])
                        return

            self.display_error("No text response received")

        except Exception as e:
            # Ensure stdout is restored even on error
            sys.stdout = original_stdout
            self.display_error(f"Error during response: {str(e)}")

    def run(self, use_async: bool = False):
        """
        Run the interactive chat loop.

        Args:
            use_async: Use async streaming (experimental, default: False)
        """
        self.display_welcome()

        while True:
            try:
                # Get user input
                user_input = Prompt.ask("[bold cyan]You[/bold cyan]").strip()

                # Check for exit commands
                if user_input.lower() in ["quit", "exit", "/q", "/quit", "/exit"]:
                    self.console.print(
                        "[bold cyan]さようなら！(Goodbye!) Keep up the great work! 👋[/bold cyan]"
                    )
                    break

                # Skip empty input
                if not user_input:
                    continue

                self.console.print()

                # Get and display response
                if use_async:
                    asyncio.run(self.stream_response_async(user_input))
                else:
                    self.get_sync_response(user_input)

            except KeyboardInterrupt:
                self.console.print(
                    "\n\n[bold cyan]Chat interrupted. さようなら！(Goodbye!) 👋[/bold cyan]"
                )
                break
            except Exception as e:
                self.display_error(f"Unexpected error: {str(e)}")
                self.console.print("[dim]You can continue chatting or type 'quit' to exit.[/dim]")


def start_chat(
    api_key: Optional[str] = None,
    model_id: str = "claude-3-5-sonnet-20241022",
    temperature: float = 0.7,
    verbose: bool = False,
    use_async: bool = False,
):
    """
    Start an interactive chat session.

    Args:
        api_key: Anthropic API key
        model_id: Claude model to use
        temperature: Response temperature
        verbose: Show detailed tool usage
        use_async: Use async streaming (experimental)

    Example:
        >>> from japanese_cli.ai.chat import start_chat
        >>> start_chat(verbose=True)
    """
    try:
        session = ChatSession(
            api_key=api_key,
            model_id=model_id,
            temperature=temperature,
            verbose=verbose,
        )
        session.run(use_async=use_async)
    except ValueError:
        # API key error already displayed in __init__
        pass
    except Exception as e:
        console = Console()
        console.print(f"[bold red]Failed to start chat:[/bold red] {str(e)}")
