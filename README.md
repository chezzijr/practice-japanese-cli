# Japanese Learning CLI

A powerful command-line application for learning Japanese with intelligent spaced repetition, progress tracking, and comprehensive vocabulary/kanji management. Designed specifically for Vietnamese learners with Sino-Vietnamese reading support.

## Development Status

**Current Phase**: Phase 10 - Polish & Testing ✅ **COMPLETE**

**All Phases Complete** (10/10):
- ✅ Phase 1-10: Full MVP implementation complete
- ✅ Database layer with migrations and CRUD operations
- ✅ Pydantic v2 models with comprehensive validation
- ✅ FSRS spaced repetition system integration
- ✅ Data import from JMdict/KANJIDIC2 (N5 level)
- ✅ Complete flashcard system (add, list, edit, review)
- ✅ MCQ (Multiple Choice Question) review system
- ✅ Progress tracking with statistics and analytics
- ✅ Grammar point management
- ✅ **Comprehensive CLI testing suite**
- ✅ **All Pydantic warnings fixed**
- ✅ **Full CLI integration test coverage**

**Quality Metrics**:
- **716 tests** passing (0 failing, 0 skipped, 0 warnings)
- **88% code coverage** ✅ (exceeded target!)
- All core features functional and tested
- Production-ready for personal use

**Note**: The MVP is feature-complete and stable. See [PLAN.md](PLAN.md) for detailed implementation status.

## Features

### Current Features
- **Flashcard System**: Add and review vocabulary and kanji with spaced repetition
  - FSRS (Free Spaced Repetition Scheduler) algorithm for optimal review timing
  - Support for vocabulary and kanji with furigana display
  - Vietnamese and English translations
  - Sino-Vietnamese readings for kanji (Han Viet)

- **MCQ (Multiple Choice) Review**: Alternative review mode with intelligent questions
  - Dynamic question generation with 4 distractor strategies
  - Independent FSRS scheduling from flashcard reviews
  - Question types: word-to-meaning, meaning-to-word, or mixed
  - Statistics tracking: accuracy rates, vocab vs kanji performance, selection bias detection

- **Progress Tracking**: Monitor your learning journey
  - JLPT level tracking (N5, N4, N3, N2, N1)
  - Learning statistics and review history
  - Study streaks and milestones

- **Data Import**: Bulk import from official sources
  - JMdict/KANJIDIC2 integration for N5 level
  - Custom CSV/JSON import support

- **Grammar Points**: Store and reference grammar
  - Grammar explanations with examples
  - JLPT level organization
  - Cross-reference with vocabulary

- **AI Chat Assistant**: Natural language interface powered by Claude AI
  - Interactive chat for vocabulary and kanji lookup
  - Progress tracking and study recommendations
  - Due review analysis and study planning
  - Vietnamese learner support with Hán Việt awareness
  - Multiple Claude models supported (Haiku 4.5 default for speed/cost)
  - Powered by Strands Agents SDK with 4 specialized tools

### Future Features (Planned)
- **Nearest Neighbor Clustering**: Group vocabularies by topic for contextual learning
- **Advanced AI Features** (basic AI chat is now available!):
  - Personalized study recommendations with ML
  - Interactive Japanese conversation practice
  - Automatic exercise generation based on level
  - Knowledge assessment and gap analysis
  - AI-assisted content import from study materials
  - Integration with external Japanese learning resources

## Why This Tool?

As a Vietnamese learner, this tool provides unique advantages:
- **Sino-Vietnamese Readings**: Leverage the similarity between Vietnamese Han Viet and Japanese on'yomi readings
- **Furigana Support**: Always see how to read kanji without guessing
- **FSRS Algorithm**: More efficient than traditional Anki SM-2, backed by research
- **Lightweight CLI**: Fast, keyboard-driven workflow for power users
- **Offline-First**: All data stored locally in SQLite

## Installation

### Option 1: Download Standalone Binary (Recommended)

**No Python installation required!** Just download and run.

1. **Download the binary** for your platform from [GitHub Releases](https://github.com/chezzijr/practice-japanese-cli/releases/latest):
   - **Linux (x64)**: `japanese-cli-linux-x64`
   - **macOS (Universal)**: `japanese-cli-macos-universal`
   - **Windows (x64)**: `japanese-cli-windows-x64.exe`

2. **Make executable** (Linux/macOS only):
   ```bash
   chmod +x japanese-cli-*
   ```

3. **Add to PATH** (optional but recommended):

   **Linux/macOS:**
   ```bash
   # Move to a directory in your PATH
   sudo mv japanese-cli-* /usr/local/bin/japanese-cli

   # Or add current directory to PATH
   export PATH="$PATH:$(pwd)"
   ```

   **Windows:**
   - Move the `.exe` to a folder like `C:\Program Files\japanese-cli\`
   - Add that folder to your System PATH via Environment Variables

4. **Verify installation**:
   ```bash
   japanese-cli version
   ```

### Option 2: Install from Source (Development)

**Prerequisites:**
- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager

**Install uv:**
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Install Japanese Learning CLI:**
```bash
# Clone the repository
git clone https://github.com/chezzijr/practice-japanese-cli.git
cd practice-japanese-cli

# Install dependencies with uv
uv sync

# Run the CLI
uv run japanese-cli --help
```

## Quick Start

> **Note:** If you installed from source, prefix all commands with `uv run` (e.g., `uv run japanese-cli init`)

### 1. Initialize the Application
```bash
japanese-cli init
```

### 2. Import N5 Vocabulary and Kanji
```bash
# Import N5 vocabulary from JMdict
japanese-cli import n5 --vocab

# Import N5 kanji from KANJIDIC2
japanese-cli import n5 --kanji
```

### 3. Add Your First Flashcard
```bash
# Add a vocabulary word
japanese-cli flashcard add --type vocab

# Follow the interactive prompts
```

### 4. Start Your First Review Session
```bash
# Review due cards
japanese-cli flashcard review

# Review N5 level cards only
japanese-cli flashcard review --level n5

# Review with a limit
japanese-cli flashcard review --limit 20
```

### 5. Try MCQ (Multiple Choice) Review
```bash
# Basic MCQ review
uv run japanese-cli mcq

# MCQ for N5 vocabulary only
uv run japanese-cli mcq --type vocab --level n5 --limit 10

# Mixed question types (word-to-meaning and meaning-to-word)
uv run japanese-cli mcq --question-type mixed

# Review both vocab and kanji with English meanings
uv run japanese-cli mcq --type both --language en
```

### 6. Track Your Progress
```bash
# View your progress dashboard
uv run japanese-cli progress show

# Set your target JLPT level
uv run japanese-cli progress set-level n4

# View detailed statistics
uv run japanese-cli progress stats --range 30d
```

### 7. Chat with AI Assistant
```bash
# Start an interactive AI chat session
uv run japanese-cli chat

# Chat with verbose mode (see tool usage)
uv run japanese-cli chat --verbose

# Use different Claude model
uv run japanese-cli chat --model claude-3-5-sonnet-20241022
```

## AI Chat Assistant

The Japanese Learning CLI includes an **AI-powered chat assistant** that provides a natural language interface to your study database. Ask questions, get recommendations, and plan your studies conversationally.

### Features

The AI assistant can help you with:
- **Vocabulary & Kanji Lookup**: "Show me N5 vocabulary about food"
- **Progress Tracking**: "How's my progress?" or "What's my study streak?"
- **Study Planning**: "What should I study today?"
- **Due Reviews**: "How many reviews are due?" or "Show my due kanji reviews"

The assistant uses **Claude AI** (Haiku 4.5 by default) with 4 specialized tools that query your local database:
1. `get_vocabulary` - Search and filter vocabulary entries
2. `get_kanji` - Search and filter kanji characters
3. `get_progress_stats` - Retrieve learning statistics and metrics
4. `get_due_reviews` - Check flashcard and MCQ reviews due for study

### Setup (One-Time)

#### 1. Get Your Anthropic API Key

Visit [console.anthropic.com](https://console.anthropic.com/) to:
1. Sign up or log in
2. Navigate to API Keys section
3. Create a new API key (starts with `sk-ant-api03-...`)
4. Copy the key

#### 2. Configure API Key (Choose One)

**Option A: Environment File (.env) - Recommended**
```bash
# Copy the example file
cp .env.example .env

# Add your API key to .env
echo "ANTHROPIC_API_KEY=sk-ant-api03-your-key-here" > .env
```

**Option B: Environment Variable**
```bash
# For current session
export ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# Or add to your shell profile (~/.bashrc, ~/.zshrc)
echo 'export ANTHROPIC_API_KEY=sk-ant-api03-your-key-here' >> ~/.bashrc
```

**Option C: Interactive Prompt**

Don't configure anything - the CLI will prompt you to enter the API key when you run `japanese-cli chat`

### Usage

#### Basic Chat
```bash
uv run japanese-cli chat
```

You'll see a welcome panel explaining the assistant's capabilities. Type your questions naturally!

#### Example Conversations

**Finding Vocabulary:**
```
You: Show me N5 vocabulary about eating
Assistant: [Uses get_vocabulary tool]
Found vocabulary entries:
1. 食べる[たべる] - to eat (Verb, N5)
```

**Checking Progress:**
```
You: How's my progress?
Assistant: [Uses get_progress_stats tool]
You're currently studying N5 with a 5-day study streak!
You have 564 vocabulary words and 103 kanji.
Keep up the great work! 頑張ってください！
```

**Study Planning:**
```
You: What should I study today?
Assistant: [Uses get_due_reviews tool]
You have 9 reviews due today:
- 4 flashcard reviews
- 5 MCQ quizzes

I recommend starting with the flashcard reviews!
```

#### Advanced Options

```bash
# Verbose mode - see tool usage details
uv run japanese-cli chat --verbose

# More creative responses
uv run japanese-cli chat --temperature 0.9

# Use Sonnet for more complex explanations
uv run japanese-cli chat --model claude-3-5-sonnet-20241022

# Use Opus for most capable analysis
uv run japanese-cli chat --model claude-3-opus-20240229
```

#### Model Comparison

| Model | Speed | Cost/Session | Best For |
|-------|-------|--------------|----------|
| **Haiku 4.5** (default) | ⚡ Fast | ~$0.005-0.02 | Quick queries, vocab lookup |
| Sonnet 3.5 | Medium | ~$0.05-0.20 | Complex explanations |
| Opus 3 | Slower | ~$0.25-1.00 | Advanced analysis |

**Default model**: Claude Haiku 4.5 provides excellent quality with ~10x lower cost than Sonnet and ~3x faster responses.

### Cost Information

Using the Claude API incurs costs based on usage:

**Haiku 4.5 Pricing** (as of 2025):
- Input: $0.25 per million tokens
- Output: $1.25 per million tokens

**Typical chat session costs**:
- Short queries (3-5 exchanges): ~$0.005-0.01
- Medium sessions (10-15 exchanges): ~$0.01-0.02
- Long sessions (20+ exchanges): ~$0.02-0.05

For most users, a full month of regular usage costs less than $1-2 with Haiku 4.5.

### Exiting Chat

Type any of these commands to exit:
- `quit`
- `exit`
- `/q`
- Press `Ctrl+C`


## Technical Details

### Architecture
- **CLI Framework**: Typer for command structure, Rich for beautiful terminal output
- **Database**: SQLite3 with proper schema and migrations
- **SRS Algorithm**: [py-fsrs](https://github.com/open-spaced-repetition/py-fsrs) - official FSRS implementation
- **Data Sources**: JMdict (vocabulary) and KANJIDIC2 (kanji) from EDRDG

### Database Schema
- `vocabulary`: Word storage with readings, meanings, and JLPT levels
- `kanji`: Kanji characters with on/kun readings and Vietnamese readings
- `grammar_points`: Grammar explanations and examples
- `reviews`: FSRS state tracking for flashcard reviews
- `review_history`: Complete flashcard review history for analytics
- `mcq_reviews`: FSRS state tracking for MCQ reviews (independent scheduling)
- `mcq_review_history`: MCQ review history with selected options and correctness
- `progress`: User progress and statistics

### FSRS Algorithm
This application uses FSRS (Free Spaced Repetition Scheduler), a modern alternative to the SM-2 algorithm used by Anki. FSRS:
- Optimizes review intervals based on memory research
- Tracks card difficulty and stability dynamically
- Adapts to individual learning patterns
- Provides more accurate scheduling than traditional SRS

### MCQ System Architecture

The Multiple Choice Question (MCQ) system provides an alternative review mode with intelligent distractor generation.

#### Question Types
1. **Word→Meaning**: Show Japanese word/kanji, select correct Vietnamese/English meaning
2. **Meaning→Word**: Show Vietnamese/English meaning, select correct Japanese word/kanji

#### Distractor Selection Strategies

The `MCQGenerator` uses 4 intelligent strategies to create challenging but fair questions:

1. **Same JLPT Level** - Matches difficulty level for fair challenge
   - Queries items with matching `jlpt_level`
   - Randomly selects up to 10 candidates

2. **Similar Meanings** - Semantic similarity via keyword matching
   - Extracts keywords (first 2 words) from meanings
   - Uses SQL LIKE queries to find semantically related items

3. **Similar Readings** - Phonetic similarity
   - For vocabulary: Prefix matching (first 2 characters of reading)
   - For kanji: On-reading matching

4. **Visually Similar** (kanji only) - Character similarity
   - Same radical matching
   - Similar stroke count (±2 strokes)

All strategies are combined, shuffled, and limited to 3 distractors + 1 correct answer for each question.

#### Key Design Decisions

**Separate FSRS Tracking**: MCQ reviews have independent scheduling from flashcard reviews
- *Rationale*: Different review modes have different difficulty levels
- Allows practicing the same item via both flashcards and MCQ

**Dynamic Generation**: Questions generated on-the-fly, not stored in database
- *Rationale*: Saves storage, ensures variety, enables future AI enhancement
- Distractors can vary each review session

**Binary FSRS Ratings**: Correct answer = Rating.Good (3), Incorrect = Rating.Again (1)
- *Rationale*: MCQ has objective correctness, no subjective "hard/easy"
- Simpler than 4-option rating for multiple choice context

## Project Structure
```
practice-japanese-cli/
├── README.md
├── CLAUDE.md
├── PLAN.md
├── pyproject.toml
├── src/
│   └── japanese_cli/
│       ├── main.py               # CLI entry point
│       ├── models/               # Pydantic data models
│       │   ├── vocabulary.py
│       │   ├── kanji.py
│       │   ├── grammar.py
│       │   ├── review.py
│       │   ├── mcq.py           # MCQ models
│       │   └── progress.py
│       ├── database/             # Database layer
│       │   ├── connection.py
│       │   ├── schema.py
│       │   ├── queries.py
│       │   ├── mcq_queries.py   # MCQ database operations
│       │   └── migrations.py
│       ├── srs/                  # Spaced repetition system
│       │   ├── fsrs.py
│       │   ├── scheduler.py     # Flashcard FSRS scheduling
│       │   ├── mcq_scheduler.py # MCQ FSRS scheduling
│       │   ├── mcq_generator.py # MCQ question generation
│       │   └── statistics.py    # Analytics functions
│       ├── importers/            # Data import from JMdict/KANJIDIC2
│       │   ├── jmdict.py
│       │   ├── kanjidic.py
│       │   ├── jlpt.py
│       │   └── utils.py
│       ├── ai/                   # AI chat assistant (Strands Agents + Claude)
│       │   ├── agent.py         # Agent configuration and creation
│       │   ├── chat.py          # Interactive chat loop with Rich UI
│       │   └── tools/           # Custom tools for database interaction
│       │       ├── vocabulary.py # get_vocabulary tool
│       │       ├── kanji.py     # get_kanji tool
│       │       ├── progress.py  # get_progress_stats tool
│       │       └── reviews.py   # get_due_reviews tool
│       ├── cli/                  # CLI command implementations
│       │   ├── flashcard.py     # Flashcard commands
│       │   ├── mcq.py           # MCQ command
│       │   ├── progress.py      # Progress tracking
│       │   ├── grammar.py       # Grammar commands
│       │   ├── chat_command.py  # AI chat command
│       │   └── import_data.py   # Data import commands
│       └── ui/                   # Rich terminal UI
│           ├── display.py       # Display components
│           ├── prompts.py       # Interactive prompts
│           ├── furigana.py      # Furigana rendering
│           └── japanese_utils.py # Japanese text utilities
├── data/
│   ├── japanese.db               # SQLite database
│   └── dict/                     # Downloaded dictionaries
└── tests/                        # Comprehensive test suite (716 tests)
```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/practice-japanese-cli.git
cd practice-japanese-cli

# Install dependencies including dev tools
uv pip install -e ".[dev]"
```

### Running Tests

The project uses pytest for testing with comprehensive coverage.

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with coverage report
uv run pytest --cov=src/japanese_cli --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_queries.py

# Run specific test
uv run pytest tests/test_queries.py::test_add_vocabulary_success -v
```

### Test Coverage

Current test coverage (Phase 10 - 88% goal achieved ✅):
- **716 tests** covering all modules (comprehensive coverage)
- **88% overall code coverage** ✅ (exceeded target!)
- 716 passing, 0 failing, 0 skipped, 0 warnings

Coverage highlights:
- **ui/furigana.py**: 100% - Furigana rendering
- **srs/mcq_generator.py**: 99% - MCQ distractor generation
- **ui/japanese_utils.py**: 98% - Japanese text utilities
- **models/mcq.py**: 97% - MCQ models
- **models/vocabulary.py**: 96% - Vocabulary models
- **srs/statistics.py**: 96% - Analytics and progress tracking
- **srs/mcq_scheduler.py**: 95% - MCQ FSRS scheduling
- **srs/scheduler.py**: 95% - Flashcard FSRS scheduling
- **ui/display.py**: 93% - Rich UI components
- **models**: 87-97% - Pydantic data validation
- **database**: 85-93% - CRUD operations and queries

Test files:
- `tests/test_statistics.py` - Statistics module (comprehensive analytics tests)
- `tests/test_ui_display.py` - UI display components
- `tests/test_ui_prompts.py` - Interactive prompts
- `tests/test_srs.py` - FSRS integration
- `tests/test_models.py` - Model validation
- `tests/test_queries.py` - Database CRUD operations
- `tests/test_main.py` - Main CLI entry point
- `tests/test_progress_cli.py` - Progress dashboard commands
- `tests/test_grammar_cli.py` - Grammar commands
- `tests/test_flashcard_cli.py` - Flashcard commands
- **MCQ System Tests**:
  - `tests/test_mcq_cli.py` - MCQ command interface
  - `tests/test_mcq_generator.py` - Question and distractor generation
  - `tests/test_mcq_integration_workflow.py` - End-to-end MCQ workflows
  - `tests/test_mcq_models.py` - MCQ data models
  - `tests/test_mcq_queries.py` - MCQ database operations
  - `tests/test_mcq_scheduler.py` - MCQ FSRS scheduling
  - `tests/test_mcq_ui.py` - MCQ UI components
- **Additional Test Files**:
  - `tests/test_importers_integration.py` - Data import system
  - `tests/test_japanese_utils.py` - Japanese text processing
  - `tests/test_jlpt.py` - JLPT level mapping
  - Plus 15 more test files covering all modules

### Project Structure

The codebase follows a modular structure:
- `src/japanese_cli/main.py` - CLI entry point
- `src/japanese_cli/database/` - Database layer (schema, queries, migrations)
- `src/japanese_cli/models/` - Pydantic data models
- `src/japanese_cli/srs/` - FSRS integration
- `src/japanese_cli/cli/` - Command implementations
- `src/japanese_cli/ui/` - Rich UI components

### Code Quality

- Follow PEP 8 style guidelines
- Use type hints for all functions
- Write tests for new features (target 80%+ coverage)
- Use descriptive variable and function names
- Document complex logic with comments

## Dependencies

Core dependencies:
- `typer` - CLI framework with rich integration
- `rich` - Beautiful terminal formatting
- `fsrs` - Official FSRS spaced repetition library
- `requests` - HTTP client for downloading dictionaries
- `lxml` - XML parsing for JMdict/KANJIDIC2
- `python-dateutil` - Date handling
- `pydantic` - Data validation
- `wanakana-python` - Japanese text processing (hiragana/katakana conversion)

AI Chat Assistant dependencies:
- `strands-agents[anthropic]` - Agent framework with Claude integration
- `strands-agents-tools` - Tool management and MCP support
- `anthropic` - Claude AI SDK (included with strands-agents[anthropic])

## Contributing

Contributions are welcome! This is a personal learning project, but if you find it useful and want to improve it:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - feel free to use and modify for your own learning!

## Acknowledgments

- [JMdict/KANJIDIC2](https://www.edrdg.org/wiki/index.php/JMdict-EDICT_Dictionary_Project) - Electronic Dictionary Research and Development Group
- [FSRS](https://github.com/open-spaced-repetition/fsrs4anki) - Free Spaced Repetition Scheduler
- [Strands Agents](https://github.com/strands-ai/strands-agents) - Model-agnostic agent framework
- [Anthropic Claude](https://www.anthropic.com/claude) - AI language model for chat assistant
- JLPT vocabulary lists from various community sources

## Support

For bugs, feature requests, or questions, please open an issue on GitHub.

---

**Note**: This project is feature-complete and stable (MVP v0.1.0). The core functionality, including the AI chat assistant powered by Claude, is production-ready for personal use. Future enhancements (clustering, advanced AI features, etc.) are documented in [PLAN.md](PLAN.md).
