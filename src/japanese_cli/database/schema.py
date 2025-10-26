"""
Database schema definitions for Japanese Learning CLI.

Defines all table structures, indexes, and constraints for the SQLite database.
"""

# SQL for creating all database tables
CREATE_TABLES_SQL = """
-- Table: vocabulary
-- Stores Japanese vocabulary words with readings and meanings
CREATE TABLE IF NOT EXISTS vocabulary (
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

-- Table: kanji
-- Stores individual kanji characters with readings and meanings
CREATE TABLE IF NOT EXISTS kanji (
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

-- Table: grammar_points
-- Stores grammar explanations with examples
CREATE TABLE IF NOT EXISTS grammar_points (
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

-- Table: reviews
-- Tracks FSRS state for each flashcard (vocabulary or kanji)
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,              -- Foreign key to vocabulary.id or kanji.id
    item_type TEXT NOT NULL,               -- 'vocab' or 'kanji'
    fsrs_card_state TEXT NOT NULL,         -- JSON: FSRS Card state from Card.to_dict()
    due_date TIMESTAMP NOT NULL,           -- Next review date
    last_reviewed TIMESTAMP,               -- Last review timestamp
    review_count INTEGER DEFAULT 0,        -- Total reviews done
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(item_id, item_type)
);

-- Table: review_history
-- Complete history of all reviews for analytics and progress tracking
CREATE TABLE IF NOT EXISTS review_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id INTEGER NOT NULL,            -- Foreign key to reviews.id
    rating INTEGER NOT NULL,               -- FSRS rating: 1 (Again), 2 (Hard), 3 (Good), 4 (Easy)
    duration_ms INTEGER,                   -- Time spent reviewing (milliseconds)
    reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (review_id) REFERENCES reviews(id) ON DELETE CASCADE
);

-- Table: progress
-- User progress tracking and statistics
CREATE TABLE IF NOT EXISTS progress (
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

-- Table: mcq_reviews
-- Tracks FSRS state for MCQ reviews (separate from flashcard reviews)
CREATE TABLE IF NOT EXISTS mcq_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,              -- Foreign key to vocabulary.id or kanji.id
    item_type TEXT NOT NULL,               -- 'vocab' or 'kanji'
    fsrs_card_state TEXT NOT NULL,         -- JSON: FSRS Card state from Card.to_dict()
    due_date TIMESTAMP NOT NULL,           -- Next review date
    last_reviewed TIMESTAMP,               -- Last review timestamp
    review_count INTEGER DEFAULT 0,        -- Total MCQ reviews done
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(item_id, item_type)
);

-- Table: mcq_review_history
-- Complete history of all MCQ reviews for analytics
CREATE TABLE IF NOT EXISTS mcq_review_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mcq_review_id INTEGER NOT NULL,        -- Foreign key to mcq_reviews.id
    selected_option INTEGER NOT NULL,      -- Index of selected option (0-3)
    is_correct INTEGER NOT NULL,           -- 1 if correct, 0 if incorrect
    duration_ms INTEGER,                   -- Time spent on question (milliseconds)
    reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mcq_review_id) REFERENCES mcq_reviews(id) ON DELETE CASCADE
);
"""

# SQL for creating indexes (performance optimization)
CREATE_INDEXES_SQL = """
-- Indexes for vocabulary table
CREATE INDEX IF NOT EXISTS idx_vocabulary_jlpt ON vocabulary(jlpt_level);
CREATE INDEX IF NOT EXISTS idx_vocabulary_word ON vocabulary(word);

-- Indexes for kanji table
CREATE INDEX IF NOT EXISTS idx_kanji_jlpt ON kanji(jlpt_level);
-- Note: idx_kanji_character is automatically created by UNIQUE constraint

-- Indexes for grammar_points table
CREATE INDEX IF NOT EXISTS idx_grammar_jlpt ON grammar_points(jlpt_level);

-- Indexes for reviews table
CREATE INDEX IF NOT EXISTS idx_reviews_due ON reviews(due_date);
CREATE INDEX IF NOT EXISTS idx_reviews_item ON reviews(item_id, item_type);

-- Indexes for review_history table
CREATE INDEX IF NOT EXISTS idx_history_review ON review_history(review_id);
CREATE INDEX IF NOT EXISTS idx_history_date ON review_history(reviewed_at);

-- Indexes for mcq_reviews table
CREATE INDEX IF NOT EXISTS idx_mcq_reviews_due ON mcq_reviews(due_date);
CREATE INDEX IF NOT EXISTS idx_mcq_reviews_item ON mcq_reviews(item_id, item_type);

-- Indexes for mcq_review_history table
CREATE INDEX IF NOT EXISTS idx_mcq_history_review ON mcq_review_history(mcq_review_id);
CREATE INDEX IF NOT EXISTS idx_mcq_history_date ON mcq_review_history(reviewed_at);
"""


def get_schema_sql() -> str:
    """
    Get the complete SQL for creating all tables and indexes.

    Returns:
        str: SQL statements to create all tables and indexes
    """
    return CREATE_TABLES_SQL + "\n" + CREATE_INDEXES_SQL


def get_table_names() -> list[str]:
    """
    Get list of all table names in the schema.

    Returns:
        list[str]: List of table names
    """
    return [
        "vocabulary",
        "kanji",
        "grammar_points",
        "reviews",
        "review_history",
        "progress",
        "mcq_reviews",
        "mcq_review_history"
    ]
