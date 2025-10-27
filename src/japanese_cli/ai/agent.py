"""AI agent configuration with Claude provider for Japanese learning assistant."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from strands import Agent
from strands.models.anthropic import AnthropicModel

# Load environment variables from .env file in project root
# This allows developers to store API keys in .env for convenience
# The .env file should never be committed (add to .gitignore)
project_root = Path(__file__).parent.parent.parent.parent
load_dotenv(dotenv_path=project_root / ".env", override=False)

from japanese_cli.ai.tools import (
    get_vocabulary,
    get_kanji,
    get_progress_stats,
    get_due_reviews,
)


# System prompt for the Japanese learning assistant
SYSTEM_PROMPT = """You are a Japanese learning assistant integrated with a personal study database.
Your role is to help Vietnamese learners studying Japanese (currently focusing on N4/N5 level).

# Your Capabilities

You have access to tools that let you:
1. **Search and retrieve vocabulary and kanji** - Look up Japanese words, their readings, meanings, and Vietnamese translations
2. **Track learning progress** - View study statistics, mastered items, retention rates, and streak information
3. **Check due reviews** - See what flashcards and MCQ quizzes are ready for review
4. **Provide study recommendations** - Suggest what to study based on progress and goals

# Guidelines

- When referencing Japanese vocabulary or kanji, use furigana format: 単語[たんご]
- Provide explanations in both Vietnamese and English when helpful
- Be encouraging and supportive of the learning journey
- Use JLPT levels (N5, N4, N3, N2, N1) to organize recommendations, with N5 being beginner
- Leverage Sino-Vietnamese readings (Hán Việt) to help Vietnamese learners make connections
- Consider the user's current progress when making suggestions
- When explaining grammar or vocabulary, provide practical examples

# Study Advice Philosophy

- Encourage spaced repetition and consistent daily practice
- Recommend balanced study across vocabulary, kanji, grammar, and practical usage
- Celebrate achievements and milestones
- Provide realistic, achievable goals based on current level
- Remind users that language learning is a gradual process

Remember: Your goal is to be a knowledgeable, encouraging study companion that helps Vietnamese learners
master Japanese through effective use of their study database and spaced repetition system.

Always end responses with a positive, motivating message in Japanese (適切な日本語で) when appropriate!
"""


def create_agent(
    api_key: Optional[str] = None,
    model_id: str = "claude-haiku-4-5-20251001",
    temperature: float = 0.7,
    max_tokens: int = 64000,
) -> Agent:
    """
    Create and configure the Japanese learning AI agent with Claude.

    Args:
        api_key: Anthropic API key. If not provided, reads from ANTHROPIC_API_KEY env var
                or .env file in project root
        model_id: Claude model ID to use (default: claude-haiku-4-5-20251001, Haiku 4.5)
                 Can override with claude-3-5-sonnet-20241022 or other models
        temperature: Sampling temperature for responses (default: 0.7)

    Returns:
        Configured Agent instance

    Raises:
        ValueError: If API key is not provided and not found in environment

    Example:
        >>> agent = create_agent()
        >>> result = agent("What vocabulary should I study today?")
        >>> print(result.message["content"][0]["text"])
    """
    # Get API key from parameter or environment
    if api_key is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        raise ValueError(
            "Anthropic API key not found. Please either:\n"
            "1. Create a .env file with: ANTHROPIC_API_KEY=your_key, or\n"
            "2. Set the ANTHROPIC_API_KEY environment variable, or\n"
            "3. Pass api_key parameter to create_agent()\n\n"
            "Get an API key from: https://console.anthropic.com/"
        )

    # Configure Claude model
    # Note: temperature must be passed via params dict per strands library requirements
    model = AnthropicModel(
        model_id=model_id,
        client_args={"api_key": api_key},
        max_tokens=max_tokens,
        params={"temperature": temperature}
    )

    # Create agent with tools
    agent = Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            get_vocabulary,
            get_kanji,
            get_progress_stats,
            get_due_reviews,
        ],
    )

    return agent


def create_agent_with_custom_prompt(
    system_prompt: str,
    api_key: Optional[str] = None,
    model_id: str = "claude-haiku-4-5-20251001",
    temperature: float = 0.7,
) -> Agent:
    """
    Create an agent with a custom system prompt.

    Useful for specialized use cases or testing different prompts.

    Args:
        system_prompt: Custom system prompt to use
        api_key: Anthropic API key (reads from env var or .env if not provided)
        model_id: Claude model ID (default: Haiku 4.5)
        temperature: Sampling temperature

    Returns:
        Configured Agent instance

    Example:
        >>> prompt = "You are a Japanese grammar expert..."
        >>> agent = create_agent_with_custom_prompt(prompt)
    """
    if api_key is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        raise ValueError("Anthropic API key not found")

    # Note: temperature must be passed via params dict per strands library requirements
    model = AnthropicModel(
        model_id=model_id,
        client_args={"api_key": api_key},
        params={"temperature": temperature},
    )

    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=[
            get_vocabulary,
            get_kanji,
            get_progress_stats,
            get_due_reviews,
        ],
    )

    return agent
