# Japanese Learning CLI

A powerful command-line application for learning Japanese with intelligent spaced repetition, progress tracking, and comprehensive vocabulary/kanji management. Designed specifically for Vietnamese learners with Sino-Vietnamese reading support.

## Development Status

**Current Phase**: Phase 10 - Polish & Testing (85% Complete) ✅

**Completed Phases** (9.85/10):
- ✅ Phase 1-9: Full MVP implementation complete
- ✅ Database layer with migrations and CRUD operations
- ✅ Pydantic v2 models with comprehensive validation
- ✅ FSRS spaced repetition system integration
- ✅ Data import from JMdict/KANJIDIC2 (N5 level)
- ✅ Complete flashcard system (add, list, edit, review)
- ✅ Progress tracking with statistics and analytics
- ✅ Grammar point management
- ✅ **Comprehensive CLI testing suite**

**Phase 10 Progress** (7/9 core tasks completed):
- ✅ Statistics module: 9% → 100% coverage (+41 tests)
- ✅ UI display: 73% → 96% coverage (+15 tests)
- ✅ Fixed all Pydantic warnings (28 → 0)
- ✅ Fixed grammar prompt infinite loop bug
- ✅ **CLI integration tests: +67 tests for main, grammar, progress commands**
- ✅ **main.py: 0% → 98% coverage**
- ✅ **progress.py: 14% → 99% coverage**
- ✅ **grammar.py: 19% → 98% coverage (all tests passing)**
- ⏳ Remaining: import/flashcard CLI tests, error handling improvements

**Quality Metrics**:
- **538 tests** passing (0 failing, 0 skipped, 0 warnings)
- **86% code coverage** ✅ (exceeded target!)
- All core features functional and tested

**Note**: The application is production-ready for personal use. See [PLAN.md](PLAN.md) for detailed implementation status.

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
uv run japanese-cli flashcard mcq

# MCQ for N5 vocabulary only
uv run japanese-cli flashcard mcq --type vocab --level n5 --limit 10

# Mixed question types (word-to-meaning and meaning-to-word)
uv run japanese-cli flashcard mcq --question-type mixed

# Review both vocab and kanji with English meanings
uv run japanese-cli flashcard mcq --type both --language en
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
│       ├── main.py          # CLI entry point
│       ├── models/          # Data models
│       ├── database/        # Database management
│       ├── srs/             # FSRS integration
│       ├── importers/       # Data import logic
│       ├── cli/             # Command implementations
│       └── ui/              # Rich UI components
├── data/
│   ├── japanese.db          # SQLite database
│   └── dict/                # Downloaded dictionaries
└── tests/
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

Current test coverage (Phase 10 - 86% goal achieved ✅):
- **538 tests** covering all modules (+67 new CLI tests)
- **86% overall code coverage** ✅ (exceeded target!)
- 538 passing, 0 failing, 0 skipped, 0 warnings

Coverage highlights:
- **srs/statistics.py**: 100% (41 tests) - Analytics and progress tracking
- **cli/progress.py**: 99% (23 tests) - Progress dashboard commands
- **cli/grammar.py**: 98% (33 tests) - Grammar commands
- **main.py**: 98% (16 tests) - Application entry point
- **ui/display.py**: 96% (44 tests) - Rich UI components
- **srs/scheduler.py**: 95% (37 tests) - FSRS review scheduling
- **models**: 89-98% (51 tests) - Pydantic data validation
- **database/queries.py**: 85% (40 tests) - CRUD operations

Test files:
- `tests/test_statistics.py` - Statistics module tests (41 tests)
- `tests/test_ui_display.py` - UI display tests (44 tests)
- `tests/test_ui_prompts.py` - Interactive prompts (45 tests)
- `tests/test_srs.py` - FSRS integration (37 tests)
- `tests/test_models.py` - Model validation (51 tests)
- `tests/test_queries.py` - CRUD operations (40 tests)
- **`tests/test_main.py`** - Main CLI tests (16 tests) **NEW**
- **`tests/test_progress_cli.py`** - Progress commands (23 tests) **NEW**
- **`tests/test_grammar_cli.py`** - Grammar commands (28 tests) **NEW**
- Plus 11 more test files covering all modules

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

**Note**: This is an active learning project. The database structure and features may change as development continues. Always backup your data before updating!
