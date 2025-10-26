# Japanese Learning CLI - Implementation Plan

This document outlines the detailed implementation roadmap for the Japanese Learning CLI project, broken down into phases with specific deliverables and acceptance criteria.

## Overview

**Goal**: Build a functional Japanese learning CLI tool with flashcard system, FSRS spaced repetition, progress tracking, and N5 data import.

**Timeline**: Phased approach with incremental feature delivery

**Current Status**: Phase 6 Complete - Flashcard CLI with comprehensive UI and test coverage

## Implementation Phases

---

## Phase 1: Project Setup & Documentation ✅ COMPLETE

**Goal**: Establish project structure, documentation, and development environment.

**Deliverables**: README.md, CLAUDE.md, PLAN.md, pyproject.toml, directory structure, git initialization, basic CLI

**Key Artifacts**: Complete documentation set, working `japanese-cli` command with version/init, all 22 dependencies installed (fsrs 6.3.0, typer 0.20.0, rich 14.2.0, etc.)

---

## Phase 2: Database Layer ✅ COMPLETE

**Goal**: SQLite database with schema, connection management, migrations, and CRUD operations.

**Deliverables**: 6 tables (vocabulary, kanji, grammar_points, reviews, review_history, progress), 8 indexes, migration system, query utilities, functional init command

**Test Results**: 76 tests, 80% coverage on database module

---

## Testing Guidelines

After completing each phase, write comprehensive tests before moving to the next phase:
- **Unit Tests**: Test individual functions in isolation
- **Integration Tests**: Test components working together
- **Positive/Negative Tests**: Valid inputs and error handling
- **Edge Cases**: Boundary conditions and unusual scenarios
- **Coverage Target**: 80%+ per module

```python
def test_function_name_success():
    """Test that function works with valid input."""
    # Arrange, Act, Assert

def test_function_name_failure():
    """Test error handling."""
    with pytest.raises(ExpectedError):
        # Act
```

---

## Phase 3: Data Models ✅ COMPLETE

**Goal**: Pydantic v2 models for all entities with validation.

**Deliverables**: Vocabulary, Kanji, GrammarPoint, Review, ReviewHistory, Progress models with field/model validators, database conversion methods, JSON serialization

**Key Features**: FSRS Card integration, nested models (Example, ProgressStats), ItemType enum, Vietnamese character support

**Test Results**: 40 tests, 92% coverage

---

## Phase 4: FSRS Integration ✅ COMPLETE

**Goal**: py-fsrs library integration for spaced repetition scheduling.

**Deliverables**: FSRSManager (configurable scheduler), ReviewScheduler (high-level coordinator), rating conversion utilities, full review workflow (create → review → update → history)

**Simple API**: `scheduler.process_review(review_id, rating=3, duration_ms=5000)`

**Test Results**: 37 tests, 94% coverage

---

## Phase 5: Data Import System ✅ COMPLETE

**Goal**: Import N5 vocabulary and kanji from JMdict/KANJIDIC2.

**Deliverables**: JMdictImporter, KanjidicImporter, JLPTLevelMapper, CLI import commands, JLPT reference files (n5_vocab.csv: 81 words, n5_kanji.txt: 103 chars)

**Key Features**: Streaming XML parsing, Rich progress bars, duplicate detection, error handling with retry logic

**Working Commands**:
```bash
japanese-cli import n5              # Import both vocab and kanji
japanese-cli import n5 --vocab      # Vocabulary only
japanese-cli import n5 --kanji      # Kanji only
japanese-cli import n5 --force      # Force re-download
```

**Test Results**: 23 tests, 98% coverage on JLPT mapper

---

## Phase 6: Flashcard CLI - Add & List ✅ COMPLETE

**Goal**: Manually add flashcards and list existing ones.

**Deliverables**: UI utilities (furigana.py, display.py, prompts.py - 813 lines total), flashcard CLI (453 lines, 4 commands: add/list/show/edit)

**Key Features**: Furigana rendering (単語[たんご]), JLPT color coding, interactive prompts with Pydantic validation, review integration, Vietnamese support

**Working Commands**:
```bash
japanese-cli flashcard list --type vocab --level n5    # List N5 vocabulary
japanese-cli flashcard show 75 --type vocab            # Detailed view
japanese-cli flashcard add --type vocab                # Add interactively
japanese-cli flashcard edit 75 --type vocab            # Edit existing
```

**Test Results**: 106 tests, 97% coverage on UI modules

---

## Phase 7: Flashcard CLI - Review Session ✅ COMPLETE

**Goal**: Interactive review sessions with FSRS scheduling.

**Deliverables**: Review command with session flow, 4 UI components (question/answer/rating/summary), time tracking, session statistics

**Key Features**: Vietnamese → Japanese flow, FSRS state updates, millisecond time tracking, review history recording, early exit support (Ctrl+C)

**Working Commands**:
```bash
japanese-cli flashcard review                    # All due cards
japanese-cli flashcard review --limit 10        # Max 10 cards
japanese-cli flashcard review --level n5        # N5 only
japanese-cli flashcard review --type vocab      # Vocab only
```

**Test Results**: 19 tests, 82% overall project coverage, 98% on new UI code

---

## Phase 8: Progress Tracking ✅ COMPLETE

**Goal**: Progress dashboard and statistics.

**Deliverables**: Statistics module (srs/statistics.py - 499 lines, 9 functions), progress CLI (273 lines, 3 commands), UI components for dashboard/stats/dates (305 lines)

**Key Features**: Real-time stats from DB, JLPT level management, streak tracking, mastery tracking (21+ day stability), retention rate with color coding, ASCII bar charts

**Working Commands**:
```bash
japanese-cli progress show                      # Dashboard
japanese-cli progress set-level n4              # Update target level
japanese-cli progress set-level n4 --current    # Update current level
japanese-cli progress stats                     # All-time stats
japanese-cli progress stats --range 7d          # Last 7 days
japanese-cli progress stats --range 30d         # Last 30 days
```

**Statistics Functions**: vocab/kanji counts by level, mastered items, retention rate, average duration, daily aggregation, most reviewed items, date range filtering

---

## Phase 9: Grammar Points ✅ COMPLETE

**Goal**: Grammar point storage and management.

**Deliverables**: Grammar CLI (252 lines, 4 commands: add/list/show/edit), UI components (345 lines: prompts + display), grammar table/panel formatting

**Key Features**: Minimum 1 example required, JLPT color-coding, Vietnamese-first design, optional English, related grammar references, Pydantic validation

**Working Commands**:
```bash
japanese-cli grammar add                    # Interactive add
japanese-cli grammar list --level n5        # Filter by JLPT
japanese-cli grammar show 1                 # Detailed view
japanese-cli grammar edit 1                 # Edit existing
```

**Test Results**: 22 tests (21 passing, 1 skipped - edge case bug)

---

## Phase 10: Polish & Testing

**Goal**: Final polish, comprehensive testing, and bug fixes.

### Deliverables
- [ ] Comprehensive unit test suite
- [ ] Integration tests for CLI commands
- [ ] Error handling improvements
- [ ] User experience polish
- [ ] Documentation updates

### Tasks

#### 10.1: Testing
- Write unit tests for all modules (target 80%+ coverage)
- Write integration tests for CLI workflows
- Test edge cases and error conditions
- Performance testing with large datasets (1000+ cards)

#### 10.2: Error Handling
- Add user-friendly error messages
- Handle file system errors (data directory, permissions)
- Handle database errors (corruption, locked)
- Handle import errors (network issues, invalid XML)

#### 10.3: UX Polish
- Consistent color scheme across UI
- Help text for all commands
- Better prompts with validation
- Confirmation prompts for destructive actions

#### 10.4: Documentation
- Update README with any new features
- Add troubleshooting section
- Create CONTRIBUTING guide
- Add example screenshots/recordings

### Acceptance Criteria
- All tests pass
- No critical bugs
- User experience is smooth and intuitive
- Documentation is complete and accurate

---

## Future Enhancements (Post-MVP)

### Phase 11: Nearest Neighbor Clustering
- Implement embedding-based vocabulary clustering
- Group related words by topic/theme
- Display clusters in review sessions

### Phase 12: AI/LLM Integration
- MCP integration for Claude/GPT
- Personalized study recommendations
- Conversation practice mode
- Automatic exercise generation
- Knowledge assessment

### Phase 13: Advanced Features
- Audio pronunciation (TTS)
- Example sentence mining
- Anki export/import
- Web dashboard (optional)
- Mobile companion app (optional)

---

## Success Metrics

### MVP Success Criteria
- Can import and store N5 vocabulary and kanji
- FSRS scheduling works correctly
- Review sessions are functional and pleasant to use
- Progress tracking shows accurate statistics
- Vietnamese learners find Hán Việt support valuable

### Performance Targets
- Database queries < 100ms for typical operations
- Import 800 words in < 30 seconds
- Review session loads instantly (< 1s)
- Memory usage < 100MB during typical use

### Quality Targets
- Zero data loss bugs
- Graceful error handling (no crashes)
- Test coverage > 80%
- All user-facing text clear and helpful

---

## Development Conventions

### Git Workflow
- Commit after each completed task
- Use descriptive commit messages
- One feature per commit (when possible)
- Tag releases (v0.1.0, v0.2.0, etc.)

### Code Review Checklist
- [ ] Type hints for all functions
- [ ] Docstrings for public functions
- [ ] Error handling for edge cases
- [ ] Tests written for new code
- [ ] Rich output used (no plain print)
- [ ] Database transactions managed properly

### Documentation Updates
- Update PLAN.md after completing each phase
- Update CLAUDE.md if architecture changes
- Update README.md if user-facing changes
- Document any deviations from plan

---

## Risk Mitigation

### Technical Risks
- **FSRS complexity**: Use official library, start with defaults
- **JMdict parsing**: Test with sample files first, handle malformed XML
- **Vietnamese encoding**: Ensure UTF-8 everywhere, test with actual Vietnamese text
- **Database performance**: Add indexes, test with large datasets

### User Experience Risks
- **CLI complexity**: Provide clear help text and examples
- **Import confusion**: Show progress and clear error messages
- **Review fatigue**: Limit session size, allow breaks

---

## Current Status Summary

**Progress**: 9.3/10 phases complete (93% done) | **Tests**: 466 passing | **Coverage**: 79% overall

### Completed Phases (1-9)
All core features implemented and tested. See individual phase sections above for detailed deliverables.

### Phase 10 - In Progress (31% complete)
- ✅ Statistics module tests (100% coverage, was 9%)
- ✅ UI display tests (96% coverage, was 73%)
- ✅ Pydantic v2 migration (28 warnings → 0)
- ✅ Grammar prompt bug fix (infinite loop resolved)
- ⏳ Remaining: CLI integration tests, error handling improvements, documentation updates, performance testing, UX polish

### Test Suite Status
- **466 tests passing** (was 409, +57 new tests)
- **79% overall coverage** (was 70%, +9%)
- **0 skipped, 0 warnings** (was 1 skipped, 28 warnings)
- Key modules: statistics.py (100%), ui/display.py (96%), scheduler.py (95%), fsrs.py (92%)

### All Working Commands
```bash
# Setup & Info
japanese-cli --help                                    # Show all commands
japanese-cli version                                   # Show version
japanese-cli init                                      # Initialize database

# Data Import
japanese-cli import n5 [--vocab] [--kanji] [--force]  # Import N5 data

# Flashcards
japanese-cli flashcard list --type {vocab|kanji} [--level LEVEL] [--limit N]
japanese-cli flashcard show ID --type {vocab|kanji}
japanese-cli flashcard add --type {vocab|kanji}       # Interactive
japanese-cli flashcard edit ID --type {vocab|kanji}   # Interactive
japanese-cli flashcard review [--limit N] [--level LEVEL] [--type TYPE]

# Progress Tracking
japanese-cli progress show                             # Dashboard
japanese-cli progress set-level LEVEL [--current]     # Update JLPT level
japanese-cli progress stats [--range {7d|30d|all}]    # Statistics

# Grammar Points
japanese-cli grammar add                               # Interactive
japanese-cli grammar list [--level LEVEL] [--limit N]
japanese-cli grammar show ID
japanese-cli grammar edit ID                           # Interactive
```

### Dependencies Installed
typer 0.20.0, rich 14.2.0, fsrs 6.3.0, lxml 6.0.2, pydantic 2.12.3, requests 2.32.5, python-dateutil 2.9.0

---

**Last Updated**: 2025-10-26
