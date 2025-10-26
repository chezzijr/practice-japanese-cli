# Japanese Learning CLI - Project Context

This document provides comprehensive context about the Japanese Learning CLI project for Claude Code to understand the architecture, conventions, and implementation details.

## Project Overview

**Purpose**: A CLI-based Japanese learning tool designed for Vietnamese learners, featuring intelligent spaced repetition (FSRS), progress tracking, and comprehensive vocabulary/kanji/grammar management.

**Target User**: Vietnamese speakers learning Japanese (currently studying N4, started with N5 data import)

**Core Philosophy**:
- Offline-first with local SQLite storage
- Keyboard-driven CLI workflow for efficiency
- Beautiful terminal UI using Rich
- FSRS algorithm for scientifically-backed spaced repetition
- Support for Sino-Vietnamese readings to leverage Vietnamese learners' advantage

## Technology Stack

- **Language**: Python 3.10+
- **Package Manager**: uv (modern, fast Python package manager)
- **CLI Framework**: Typer (command structure) + Rich (terminal rendering)
- **Database**: SQLite3 with JSON fields for complex data
- **SRS Algorithm**: py-fsrs (official FSRS implementation from PyPI)
- **Data Sources**: JMdict (vocabulary) and KANJIDIC2 (kanji) from EDRDG
- **Data Validation**: Pydantic v2

## Project Structure

```
practice-japanese-cli/
├── README.md                  # User-facing documentation
├── CLAUDE.md                  # This file - project context for Claude Code
├── PLAN.md                    # Implementation roadmap
├── pyproject.toml             # uv project config and dependencies
├── src/
│   └── japanese_cli/
│       ├── __init__.py
│       ├── main.py            # Typer app entry point, command registration
│       │
│       ├── models/            # Pydantic models and dataclasses
│       │   ├── __init__.py
│       │   ├── vocabulary.py  # Vocabulary model with readings, meanings
│       │   ├── kanji.py       # Kanji model with on/kun readings
│       │   ├── grammar.py     # Grammar point model with examples
│       │   ├── review.py      # Review session and card state models
│       │   └── progress.py    # Progress tracking models
│       │
│       ├── database/          # Database layer
│       │   ├── __init__.py
│       │   ├── connection.py  # SQLite connection management, context managers
│       │   ├── schema.py      # CREATE TABLE statements, migrations
│       │   ├── queries.py     # Reusable query functions (CRUD operations)
│       │   └── migrations.py  # Database version management
│       │
│       ├── srs/               # Spaced repetition system
│       │   ├── __init__.py
│       │   ├── fsrs.py        # Wrapper around py-fsrs library
│       │   └── scheduler.py   # Review scheduling logic, due card queries
│       │
│       ├── importers/         # Data import from external sources
│       │   ├── __init__.py
│       │   ├── jmdict.py      # JMdict XML parser for vocabulary
│       │   ├── kanjidic.py    # KANJIDIC2 XML parser for kanji
│       │   ├── jlpt.py        # JLPT level mapping (from external lists)
│       │   └── custom.py      # CSV/JSON custom import
│       │
│       ├── cli/               # Command implementations
│       │   ├── __init__.py
│       │   ├── flashcard.py   # flashcard add/review/list/edit commands
│       │   ├── progress.py    # progress show/set-level/stats commands
│       │   ├── grammar.py     # grammar add/list/show commands
│       │   └── import_data.py # import n5/custom commands
│       │
│       └── ui/                # Rich UI components and formatters
│           ├── __init__.py
│           ├── display.py     # Rich Panel, Table, Text formatters
│           ├── furigana.py    # Furigana rendering logic
│           └── prompts.py     # Interactive input prompts
│
├── data/                      # Runtime data (gitignored except .gitkeep)
│   ├── .gitkeep
│   ├── japanese.db            # SQLite database file
│   └── dict/                  # Downloaded JMdict/KANJIDIC2 files
│       └── .gitkeep
│
└── tests/                     # Unit tests (pytest)
    ├── __init__.py
    ├── test_models.py
    ├── test_database.py
    ├── test_srs.py
    └── test_importers.py
```

## Database Schema

### Table: `vocabulary`
Stores Japanese vocabulary words with readings and meanings.

```sql
CREATE TABLE vocabulary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL,                    -- Kanji/kana form (e.g., "単語")
    reading TEXT NOT NULL,                 -- Hiragana/katakana (e.g., "たんご")
    meanings TEXT NOT NULL,                -- JSON: {"vi": ["từ vựng"], "en": ["word", "vocabulary"]}
    vietnamese_reading TEXT,               -- Sino-Vietnamese reading (e.g., "đơn ngữ")
    jlpt_level TEXT,                       -- n5, n4, n3, n2, n1, or NULL
    part_of_speech TEXT,                   -- noun, verb, adjective, etc.
    tags TEXT,                             -- JSON array: ["common", "beginner-friendly"]
    notes TEXT,                            -- User notes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes**:
- `idx_vocabulary_jlpt` on `jlpt_level`
- `idx_vocabulary_word` on `word`

### Table: `kanji`
Stores individual kanji characters with readings and meanings.

```sql
CREATE TABLE kanji (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character TEXT NOT NULL UNIQUE,        -- Single kanji (e.g., "語")
    on_readings TEXT NOT NULL,             -- JSON array: ["ゴ"]
    kun_readings TEXT NOT NULL,            -- JSON array: ["かた.る", "かた.らう"]
    meanings TEXT NOT NULL,                -- JSON: {"vi": ["ngữ"], "en": ["word", "language"]}
    vietnamese_reading TEXT,               -- Hán Việt (e.g., "ngữ")
    jlpt_level TEXT,                       -- n5, n4, n3, n2, n1, or NULL
    stroke_count INTEGER,
    radical TEXT,                          -- Radical character
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes**:
- `idx_kanji_jlpt` on `jlpt_level`
- `idx_kanji_character` on `character` (automatically created with UNIQUE)

### Table: `grammar_points`
Stores grammar explanations with examples.

```sql
CREATE TABLE grammar_points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,                   -- e.g., "は (wa) particle"
    structure TEXT,                        -- Grammar structure pattern
    explanation TEXT NOT NULL,             -- Vietnamese/English explanation
    jlpt_level TEXT,
    examples TEXT NOT NULL,                -- JSON array of {"jp": "...", "vi": "...", "en": "..."}
    related_grammar TEXT,                  -- JSON array of related grammar IDs
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes**:
- `idx_grammar_jlpt` on `jlpt_level`

### Table: `reviews`
Tracks FSRS state for each flashcard (vocabulary or kanji).

```sql
CREATE TABLE reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,              -- Foreign key to vocabulary.id or kanji.id
    item_type TEXT NOT NULL,               -- 'vocab' or 'kanji'
    fsrs_card_state TEXT NOT NULL,         -- JSON: FSRS Card state (difficulty, stability, etc.)
    due_date TIMESTAMP NOT NULL,           -- Next review date
    last_reviewed TIMESTAMP,               -- Last review timestamp
    review_count INTEGER DEFAULT 0,        -- Total reviews done
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(item_id, item_type)
);
```

**Indexes**:
- `idx_reviews_due` on `due_date`
- `idx_reviews_item` on `(item_id, item_type)`

### Table: `review_history`
Complete history of all reviews for analytics and progress tracking.

```sql
CREATE TABLE review_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id INTEGER NOT NULL,            -- Foreign key to reviews.id
    rating INTEGER NOT NULL,               -- FSRS rating: 1 (Again), 2 (Hard), 3 (Good), 4 (Easy)
    duration_ms INTEGER,                   -- Time spent reviewing (milliseconds)
    reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (review_id) REFERENCES reviews(id) ON DELETE CASCADE
);
```

**Indexes**:
- `idx_history_review` on `review_id`
- `idx_history_date` on `reviewed_at`

### Table: `progress`
User progress tracking and statistics.

```sql
CREATE TABLE progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT DEFAULT 'default',        -- Multi-user support (future)
    current_level TEXT DEFAULT 'n5',       -- Current studying level
    target_level TEXT DEFAULT 'n5',        -- Target JLPT level
    stats TEXT NOT NULL,                   -- JSON: detailed statistics
    milestones TEXT,                       -- JSON: achieved milestones
    streak_days INTEGER DEFAULT 0,
    last_review_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);
```

**Stats JSON structure**:
```json
{
  "total_vocab": 500,
  "total_kanji": 103,
  "mastered_vocab": 50,
  "mastered_kanji": 20,
  "total_reviews": 1000,
  "average_retention": 0.85
}
```

## FSRS Integration

### py-fsrs Library Usage (v6.3.0+)
```python
from fsrs import Scheduler, Card, Rating, ReviewLog, State
from datetime import datetime, timezone

# Initialize scheduler (default parameters)
scheduler = Scheduler()

# Create a new card
card = Card()

# Review a card with a rating
rating = Rating.Good  # Or: Rating.Again, Rating.Hard, Rating.Good, Rating.Easy
card, review_log = scheduler.review_card(card, rating)

# The card object is now updated with new FSRS state
# review_log contains information about this review session

# Store card state as JSON in database using built-in serialization
card_state_json = card.to_dict()
# Returns: {
#     "card_id": int,
#     "state": int,  # 1=Learning, 2=Review, 3=Relearning
#     "step": int,
#     "stability": float | None,
#     "difficulty": float | None,
#     "due": "ISO datetime string",
#     "last_review": "ISO datetime string" | None
# }

# Restore card from database
card = Card.from_dict(card_state_json)

# Custom scheduler parameters (optional)
from datetime import timedelta
scheduler = Scheduler(
    desired_retention=0.9,  # 90% retention rate
    learning_steps=(timedelta(minutes=1), timedelta(minutes=10)),
    relearning_steps=(timedelta(minutes=10),),
    maximum_interval=36500,  # days
    enable_fuzzing=True
)
```

### Rating System
- `Rating.Again` (1): Forgot the card, review soon
- `Rating.Hard` (2): Difficult to recall, shorter interval
- `Rating.Good` (3): Recalled correctly, normal interval
- `Rating.Easy` (4): Very easy to recall, longer interval

## UI/UX Design

### Furigana Display
Format kanji with furigana using Rich markup:
- Format: `単語[たんご]` displayed as kanji with reading
- Use Rich Text with different colors for kanji vs. furigana

```python
from rich.text import Text

def format_with_furigana(word: str, reading: str) -> Text:
    text = Text()
    text.append(word, style="bold cyan")
    text.append(f"[{reading}]", style="dim cyan")
    return text
```

### Review Session Flow
1. Show card front (e.g., Vietnamese meaning)
2. User presses Enter to reveal answer
3. Show card back (Japanese word with furigana, readings)
4. User rates: 1 (Again), 2 (Hard), 3 (Good), 4 (Easy)
5. Update FSRS state and move to next card
6. Display progress bar and session statistics

### Rich Components
- **Panels**: For card display, statistics dashboard
- **Tables**: For listing vocabulary/kanji/grammar
- **Progress bars**: For review sessions, import progress
- **Prompts**: Using rich.prompt for interactive input

## Coding Conventions

### Python Style
- Follow PEP 8
- Use type hints for all function signatures
- Use Pydantic models for data validation
- Use `snake_case` for functions and variables
- Use `PascalCase` for classes

### Database Access
- Use context managers for database connections
- Parameterized queries (no string interpolation)
- Transaction management for related writes
- Handle errors gracefully with try/except

```python
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    conn = sqlite3.connect("data/japanese.db")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```

### CLI Command Structure
- Each command group in separate file (cli/flashcard.py, cli/progress.py, etc.)
- Use Typer app instances
- Provide helpful error messages
- Use Rich for all output (no plain print())

### Error Handling
- Use custom exceptions for domain errors
- Display user-friendly error messages using Rich Console
- Log errors for debugging (future: add logging module)

## Data Import Strategy

### JMdict Vocabulary Import
1. Download JMdict_e.gz from EDRDG
2. Parse XML using lxml
3. Filter by JLPT level (using external N5 word list)
4. Extract word, readings, meanings (English)
5. Store in database with JLPT level tag

### KANJIDIC2 Kanji Import
1. Download kanjidic2.xml.gz from EDRDG
2. Parse XML for each kanji
3. Extract on-readings, kun-readings, meanings, stroke count
4. Filter by JLPT level (using external N5 kanji list)
5. Store in database

### Vietnamese Reading Handling
- Vietnamese readings (Hán Việt) are not in JMdict/KANJIDIC2
- Initially support manual entry via CLI
- Future: integrate Hán Việt dictionary or conversion system
- For kanji, Sino-Vietnamese readings often correlate with on-yomi

### JLPT Level Mapping
- JMdict/KANJIDIC2 don't tag JLPT levels officially
- Use external sources:
  - tanos.co.uk JLPT lists (CSV format)
  - jlptsensei.com lists
  - Jonathan Waller's JLPT resources
- Cross-reference by word/kanji to assign levels

## Testing Strategy

### Overview
- Write tests after completing each phase (before moving to next phase)
- Target 80%+ code coverage per module
- Use pytest for all testing
- Both positive (happy path) and negative (error handling) test cases

### Test Structure
```
tests/
├── conftest.py              # Shared fixtures
├── test_connection.py       # Database connection tests
├── test_schema.py          # Schema validation tests
├── test_migrations.py      # Migration system tests
├── test_queries.py         # CRUD operation tests
└── test_fsrs_integration.py # FSRS integration tests
```

### Running Tests
```bash
# Run all tests with verbose output
uv run pytest -v

# Run with coverage report
uv run pytest --cov=src/japanese_cli --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_queries.py -v

# Run specific test
uv run pytest tests/test_queries.py::test_add_vocabulary_success -v
```

### Test Fixtures (conftest.py)
- `temp_db_path` - Temporary database file path
- `clean_db` - Fresh initialized database with progress
- `sample_vocabulary` - Sample vocabulary data dictionary
- `sample_kanji` - Sample kanji data dictionary
- `sample_grammar` - Sample grammar data dictionary
- `db_with_vocabulary` - Database with sample vocabulary inserted
- `db_with_kanji` - Database with sample kanji inserted
- `db_with_review` - Database with vocabulary and review entry

### Test Categories

**Unit Tests**: Test individual functions in isolation
- Database queries (CRUD operations)
- FSRS card serialization
- Schema validation
- Migration functions

**Integration Tests**: Test components working together
- Review workflow (create → review → update → history)
- Database initialization process
- FSRS scheduler with database persistence

**Positive Tests**: Verify correct behavior
- Adding vocabulary/kanji/grammar
- Retrieving data by ID
- Listing with filters
- Searching by terms

**Negative Tests**: Verify error handling
- Non-existent IDs return None
- Duplicate entries raise IntegrityError
- Foreign key constraints enforced
- Invalid inputs handled gracefully

**Edge Cases**: Test boundary conditions
- Empty databases
- Large result sets (pagination)
- Missing optional fields
- Concurrent access (transactions)

### Current Test Coverage (Phase 2)
- **76 tests total**, all passing
- **80% code coverage** on database module
- Test files:
  - `test_connection.py` - 8 tests
  - `test_schema.py` - 9 tests
  - `test_migrations.py` - 9 tests
  - `test_queries.py` - 40 tests
  - `test_fsrs_integration.py` - 10 tests

### Testing Best Practices
1. **Isolation**: Each test uses a fresh temporary database
2. **Descriptive names**: `test_function_name_expected_behavior`
3. **Arrange-Act-Assert**: Clear test structure
4. **One assertion focus**: Test one thing per test when possible
5. **Fixtures for reuse**: Common test data in conftest.py
6. **Fast tests**: All tests complete in < 1 second total

## Future Enhancements

### Nearest Neighbor Clustering
- Use embeddings (sentence-transformers) to group similar vocabulary
- Display related words together in review sessions
- Help learners build thematic vocabulary clusters

### AI/LLM Integration (MCP)
- Use Claude/GPT via MCP for:
  - Personalized study recommendations
  - Conversation practice
  - Exercise generation based on JLPT level
  - Knowledge assessment (what user knows vs. needs to learn)
  - Auto-populate database from user's study materials

### Enhanced Progress Tracking
- Heatmap calendar of review activity
- Retention rate graphs by JLPT level
- Predicted time to mastery for each level
- Comparison with typical learning curves

## Important Implementation Notes

1. **Database Location**: Store `japanese.db` in `data/` directory, create if not exists
2. **FSRS Parameters**: Use default parameters initially, allow customization later
3. **Date Handling**: Store all timestamps in UTC, display in local time
4. **Vietnamese Input**: Ensure terminal supports Vietnamese characters (UTF-8)
5. **Large Imports**: Show progress bars for N5 import (800+ words, 103 kanji)
6. **Testing Data**: Provide sample vocabulary/kanji for quick testing without full import

## Key Dependencies

```toml
[project]
requires-python = ">=3.10"
dependencies = [
    "typer[all]>=0.9.0",      # CLI framework with rich support
    "rich>=13.0.0",           # Terminal formatting
    "fsrs>=4.0.0",            # FSRS algorithm
    "requests>=2.31.0",       # HTTP downloads
    "lxml>=4.9.0",            # XML parsing
    "python-dateutil>=2.8.0", # Date utilities
    "pydantic>=2.0.0",        # Data validation
]
```

## Common Commands Reference

```bash
# Initialize database (first run)
japanese-cli init

# Add vocabulary manually
japanese-cli flashcard add --type vocab

# Add kanji manually
japanese-cli flashcard add --type kanji

# Import N5 data (both vocab and kanji)
japanese-cli import n5 --vocab --kanji

# Review due cards
japanese-cli flashcard review

# Review specific level
japanese-cli flashcard review --level n5 --limit 20

# View progress
japanese-cli progress show

# View detailed stats
japanese-cli progress stats --range 30d
```

## Development Workflow

1. Make changes in `src/japanese_cli/`
2. Test locally: `uv run japanese-cli <command>`
3. Run tests: `uv run pytest`
4. Commit with descriptive messages
5. Update PLAN.md to track implementation progress

## Questions to Consider

When implementing features, consider:
- How will this scale with thousands of vocabulary words?
- Is the UX intuitive for CLI users?
- Are error messages clear and actionable?
- Does this work well for Vietnamese learners specifically?
- How will this feature integrate with future AI capabilities?

---

## Current Implementation Status

**Progress**: 9.3/10 phases complete (93%) | **Tests**: 466 passing | **Coverage**: 79% overall | **Last Updated**: 2025-10-26

### Implementation Progress Table

| Phase | Status | Description | Key Stats |
|-------|--------|-------------|-----------|
| 1 | ✅ | Project Setup & Documentation | All docs, dependencies, structure complete |
| 2 | ✅ | Database Layer | 6 tables, 8 indexes, migrations, CRUD - 76 tests, 80% coverage |
| 3 | ✅ | Data Models | Pydantic v2 models with validation - 40 tests, 92% coverage |
| 4 | ✅ | FSRS Integration | Scheduler, review workflow - 37 tests, 94% coverage |
| 5 | ✅ | Data Import System | JMdict/KANJIDIC2 parsers - 23 tests, 98% coverage |
| 6 | ✅ | Flashcard CLI - Add/List | UI utilities, CRUD commands - 106 tests, 97% coverage |
| 7 | ✅ | Flashcard CLI - Review | Interactive sessions, FSRS - 19 tests, 82% overall |
| 8 | ✅ | Progress Tracking | Dashboard, stats, analytics - Manual testing verified |
| 9 | ✅ | Grammar Points | Grammar management - 22 tests |
| 10 | 🔨 | Polish & Testing | 4/13 tasks done: Stats tests (100%), UI tests (96%), Pydantic v2 migration, bug fixes |

### Phase 10 Remaining Tasks
- CLI integration tests (grammar, progress, import)
- Error handling improvements (database, network, file system)
- Documentation updates (README Phase 10 status, troubleshooting section)
- Performance testing with large datasets
- UX polish (help text, color consistency)

### Test Suite Overview
- **Total**: 466 tests passing, 0 skipped, 0 warnings
- **Coverage**: 79% overall (up from 70%)
- **Top Modules**: statistics.py (100%), ui/display.py (96%), scheduler.py (95%), fsrs.py (92%)

### Available CLI Commands

See PLAN.md "Current Status Summary" section for complete command reference. Key command groups:
- **Setup**: `init`, `--help`, `version`
- **Import**: `import n5 [--vocab] [--kanji] [--force]`
- **Flashcards**: `flashcard {list|show|add|edit|review}` with filters
- **Progress**: `progress {show|set-level|stats}` with date ranges
- **Grammar**: `grammar {add|list|show|edit}` with JLPT filtering

### Key Modules and APIs

**Models** (src/japanese_cli/models/):
```python
from japanese_cli.models import Vocabulary, Kanji, GrammarPoint, Review, Progress, ItemType
```

**SRS Scheduler** (src/japanese_cli/srs/):
```python
from japanese_cli.srs import ReviewScheduler
scheduler = ReviewScheduler()
scheduler.process_review(review_id, rating=3, duration_ms=5000)
```

**Database** (src/japanese_cli/database/):
- 6 tables: vocabulary, kanji, grammar_points, reviews, review_history, progress
- CRUD operations via queries.py
- Migration system with PRAGMA user_version

**Statistics** (src/japanese_cli/srs/statistics.py):
- 9 functions for vocab/kanji counts, mastered items, retention rate, time tracking, daily aggregation

For detailed implementation notes on each phase, see PLAN.md.
