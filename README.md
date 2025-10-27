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

### Future Features (Planned)
- **Nearest Neighbor Clustering**: Group vocabularies by topic for contextual learning
- **AI/LLM Integration**:
  - Personalized study recommendations
  - Practice conversations via MCP
  - Automatic exercise generation based on level
  - Knowledge assessment and gap analysis
- **Enhanced Database Population**: AI-assisted content import from study materials

## Why This Tool?

As a Vietnamese learner, this tool provides unique advantages:
- **Sino-Vietnamese Readings**: Leverage the similarity between Vietnamese Han Viet and Japanese on'yomi readings
- **Furigana Support**: Always see how to read kanji without guessing
- **FSRS Algorithm**: More efficient than traditional Anki SM-2, backed by research
- **Lightweight CLI**: Fast, keyboard-driven workflow for power users
- **Offline-First**: All data stored locally in SQLite

## Installation

### Prerequisites
- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Install uv
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Install Japanese Learning CLI
```bash
# Clone the repository
git clone https://github.com/yourusername/practice-japanese-cli.git
cd practice-japanese-cli

# Install dependencies with uv
uv sync

# Run the CLI
uv run japanese-cli --help
```

## Quick Start

### 1. Initialize the Application
```bash
uv run japanese-cli init
```

### 2. Import N5 Vocabulary and Kanji
```bash
# Import N5 vocabulary from JMdict
uv run japanese-cli import n5 --vocab

# Import N5 kanji from KANJIDIC2
uv run japanese-cli import n5 --kanji
```

### 3. Add Your First Flashcard
```bash
# Add a vocabulary word
uv run japanese-cli flashcard add --type vocab

# Follow the interactive prompts
```

### 4. Start Your First Review Session
```bash
# Review due cards
uv run japanese-cli flashcard review

# Review N5 level cards only
uv run japanese-cli flashcard review --level n5

# Review with a limit
uv run japanese-cli flashcard review --limit 20
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
│       ├── cli/                  # CLI command implementations
│       │   ├── flashcard.py     # Flashcard commands
│       │   ├── mcq.py           # MCQ command
│       │   ├── progress.py      # Progress tracking
│       │   ├── grammar.py       # Grammar commands
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
- JLPT vocabulary lists from various community sources

## Support

For bugs, feature requests, or questions, please open an issue on GitHub.

---

**Note**: This project is feature-complete and stable (MVP v0.1.0). The core functionality is production-ready for personal use. Future enhancements (AI integration, clustering, etc.) are documented in [PLAN.md](PLAN.md).
