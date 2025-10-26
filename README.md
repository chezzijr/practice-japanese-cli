# Japanese Learning CLI

A powerful command-line application for learning Japanese with intelligent spaced repetition, progress tracking, and comprehensive vocabulary/kanji management. Designed specifically for Vietnamese learners with Sino-Vietnamese reading support.

## Development Status

**Current Phase**: Phase 2 - Database Layer (In Development)

**Completed**:
- ✅ Phase 1: Project setup, documentation, and basic CLI structure
- ✅ All dependencies installed (fsrs, typer, rich, pydantic, etc.)
- ✅ Working CLI with `--help`, `version`, and `init` commands

**In Progress**:
- 🔨 Database schema and connection management
- 🔨 Data models with Pydantic validation
- 🔨 FSRS integration wrapper

**Note**: This is actively under development. Features listed below represent the planned functionality. See [PLAN.md](PLAN.md) for the detailed implementation roadmap.

## Features

### Current Features
- **Flashcard System**: Add and review vocabulary and kanji with spaced repetition
  - FSRS (Free Spaced Repetition Scheduler) algorithm for optimal review timing
  - Support for vocabulary and kanji with furigana display
  - Vietnamese and English translations
  - Sino-Vietnamese readings for kanji (Han Viet)

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

### 5. Track Your Progress
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
- `reviews`: FSRS state tracking for each card
- `progress`: User progress and statistics
- `review_history`: Complete review history for analytics

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

Current test coverage:
- **76 tests** covering database layer
- **80% code coverage** on database module
- Tests include both positive (happy path) and negative (error handling) cases

Test files:
- `tests/conftest.py` - Shared fixtures and test data
- `tests/test_connection.py` - Database connection tests (8 tests)
- `tests/test_schema.py` - Schema validation tests (9 tests)
- `tests/test_migrations.py` - Migration system tests (9 tests)
- `tests/test_queries.py` - CRUD operation tests (40 tests)
- `tests/test_fsrs_integration.py` - FSRS integration tests (10 tests)

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
