"""
Comprehensive tests for database CRUD operations.
"""

from datetime import datetime, timedelta, timezone

import pytest

from japanese_cli.database import (
    add_grammar,
    add_kanji,
    add_review_history,
    add_vocabulary,
    create_review,
    delete_grammar,
    delete_kanji,
    delete_vocabulary,
    get_due_cards,
    get_grammar_by_id,
    get_kanji_by_character,
    get_kanji_by_id,
    get_progress,
    get_review,
    get_vocabulary_by_id,
    has_review_entry,
    increment_streak,
    init_progress,
    list_grammar,
    list_kanji,
    list_vocabulary,
    search_kanji,
    search_vocabulary,
    update_grammar,
    update_kanji,
    update_progress,
    update_review,
    update_vocabulary,
)


# ============================================================================
# Vocabulary Tests
# ============================================================================

def test_add_vocabulary_success(clean_db, sample_vocabulary):
    """Test adding vocabulary with all fields."""
    vocab_id = add_vocabulary(**sample_vocabulary, db_path=clean_db)
    assert vocab_id > 0


def test_add_vocabulary_minimal(clean_db):
    """Test adding vocabulary with only required fields."""
    vocab_id = add_vocabulary(
        word="test",
        reading="てすと",
        meanings={"en": ["test"]},
        db_path=clean_db
    )
    assert vocab_id > 0


def test_get_vocabulary_by_id_success(db_with_vocabulary):
    """Test retrieving vocabulary by ID."""
    db_path, vocab_id = db_with_vocabulary

    vocab = get_vocabulary_by_id(vocab_id, db_path=db_path)

    assert vocab is not None
    assert vocab["id"] == vocab_id
    assert vocab["word"] == "単語"
    assert vocab["reading"] == "たんご"


def test_get_vocabulary_by_id_not_found(clean_db):
    """Test that getting non-existent vocabulary returns None."""
    vocab = get_vocabulary_by_id(9999, db_path=clean_db)
    assert vocab is None


def test_list_vocabulary_all(db_with_review):
    """Test listing all vocabulary that have review entries (flashcards only)."""
    db_path, vocab_id, review_id = db_with_review

    vocab_list = list_vocabulary(db_path=db_path)

    assert len(vocab_list) >= 1
    assert any(v["id"] == vocab_id for v in vocab_list)


def test_list_vocabulary_with_jlpt_filter(clean_db):
    """Test listing vocabulary filtered by JLPT level (flashcards only)."""
    from fsrs import Card

    # Add N5 and N4 vocabulary
    vocab_id_1 = add_vocabulary(
        word="test1",
        reading="てすと1",
        meanings={"en": ["test1"]},
        jlpt_level="n5",
        db_path=clean_db
    )
    vocab_id_2 = add_vocabulary(
        word="test2",
        reading="てすと2",
        meanings={"en": ["test2"]},
        jlpt_level="n4",
        db_path=clean_db
    )

    # Create review entries for both
    card = Card()
    create_review(
        item_id=vocab_id_1,
        item_type="vocab",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=clean_db
    )
    create_review(
        item_id=vocab_id_2,
        item_type="vocab",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=clean_db
    )

    n5_vocab = list_vocabulary(jlpt_level="n5", db_path=clean_db)
    assert len(n5_vocab) == 1
    assert n5_vocab[0]["word"] == "test1"


def test_list_vocabulary_with_limit(db_with_review):
    """Test listing vocabulary with limit (flashcards only)."""
    from fsrs import Card

    db_path, _, _ = db_with_review

    # Add more vocabulary with review entries
    for i in range(5):
        vocab_id = add_vocabulary(
            word=f"word{i}",
            reading=f"reading{i}",
            meanings={"en": [f"meaning{i}"]},
            db_path=db_path
        )
        # Create review entry
        card = Card()
        create_review(
            item_id=vocab_id,
            item_type="vocab",
            fsrs_card_state=card.to_dict(),
            due_date=card.due,
            db_path=db_path
        )

    vocab_list = list_vocabulary(limit=3, db_path=db_path)
    assert len(vocab_list) == 3


def test_list_vocabulary_only_shows_flashcards(clean_db):
    """Test that list_vocabulary only shows items with review entries."""
    from fsrs import Card

    # Add vocabulary WITHOUT review entry
    vocab_id_no_review = add_vocabulary(
        word="no_review",
        reading="のーれびゅー",
        meanings={"en": ["no review"]},
        db_path=clean_db
    )

    # Add vocabulary WITH review entry
    vocab_id_with_review = add_vocabulary(
        word="with_review",
        reading="うぃずれびゅー",
        meanings={"en": ["with review"]},
        db_path=clean_db
    )
    card = Card()
    create_review(
        item_id=vocab_id_with_review,
        item_type="vocab",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=clean_db
    )

    # List should only return the one with review entry
    vocab_list = list_vocabulary(db_path=clean_db)
    assert len(vocab_list) == 1
    assert vocab_list[0]["id"] == vocab_id_with_review
    assert vocab_list[0]["word"] == "with_review"


def test_search_vocabulary(db_with_vocabulary):
    """Test searching vocabulary by word/reading/meaning."""
    db_path, _ = db_with_vocabulary

    # Search by word
    results = search_vocabulary("単語", db_path=db_path)
    assert len(results) >= 1

    # Search by reading
    results = search_vocabulary("たんご", db_path=db_path)
    assert len(results) >= 1


def test_search_vocabulary_not_found(clean_db):
    """Test searching for non-existent vocabulary."""
    results = search_vocabulary("nonexistent", db_path=clean_db)
    assert len(results) == 0


def test_search_vocabulary_excludes_flashcards(db_with_vocabulary):
    """Test that search_vocabulary excludes items with review entries."""
    from fsrs import Card

    db_path, vocab_id = db_with_vocabulary

    # Initially, search should return the vocabulary
    results = search_vocabulary("単語", db_path=db_path)
    assert len(results) == 1
    assert results[0]["id"] == vocab_id

    # Create a review entry (making it a flashcard)
    card = Card()
    create_review(
        item_id=vocab_id,
        item_type="vocab",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=db_path
    )

    # Now search should return nothing (vocabulary is now a flashcard)
    results = search_vocabulary("単語", db_path=db_path)
    assert len(results) == 0


def test_search_vocabulary_by_reading_excludes_flashcards(db_with_vocabulary):
    """Test that search_vocabulary_by_reading excludes items with review entries."""
    from japanese_cli.database import search_vocabulary_by_reading
    from fsrs import Card

    db_path, vocab_id = db_with_vocabulary

    # Initially, exact match search should return the vocabulary
    results = search_vocabulary_by_reading("たんご", exact_match=True, db_path=db_path)
    assert len(results) == 1
    assert results[0]["id"] == vocab_id

    # Create a review entry (making it a flashcard)
    card = Card()
    create_review(
        item_id=vocab_id,
        item_type="vocab",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=db_path
    )

    # Now search should return nothing (vocabulary is now a flashcard)
    results = search_vocabulary_by_reading("たんご", exact_match=True, db_path=db_path)
    assert len(results) == 0


def test_search_vocabulary_by_reading_partial_excludes_flashcards(clean_db):
    """Test that partial reading search excludes flashcards."""
    from japanese_cli.database import search_vocabulary_by_reading
    from fsrs import Card

    # Add two vocabulary items with similar readings
    vocab1_id = add_vocabulary(
        word="単語",
        reading="たんご",
        meanings={"en": ["word"]},
        db_path=clean_db
    )
    vocab2_id = add_vocabulary(
        word="短期",
        reading="たんき",
        meanings={"en": ["short-term"]},
        db_path=clean_db
    )

    # Partial search should return both
    results = search_vocabulary_by_reading("たん", exact_match=False, db_path=clean_db)
    assert len(results) == 2

    # Add vocab1 as flashcard
    card = Card()
    create_review(
        item_id=vocab1_id,
        item_type="vocab",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=clean_db
    )

    # Now partial search should only return vocab2
    results = search_vocabulary_by_reading("たん", exact_match=False, db_path=clean_db)
    assert len(results) == 1
    assert results[0]["id"] == vocab2_id


def test_update_vocabulary_success(db_with_vocabulary):
    """Test updating vocabulary fields."""
    db_path, vocab_id = db_with_vocabulary

    success = update_vocabulary(
        vocab_id,
        notes="Updated notes",
        tags=["updated"],
        db_path=db_path
    )

    assert success is True

    vocab = get_vocabulary_by_id(vocab_id, db_path=db_path)
    assert vocab["notes"] == "Updated notes"


def test_update_vocabulary_not_found(clean_db):
    """Test updating non-existent vocabulary returns False."""
    success = update_vocabulary(9999, notes="test", db_path=clean_db)
    assert success is False


def test_delete_vocabulary_success(db_with_vocabulary):
    """Test deleting vocabulary."""
    db_path, vocab_id = db_with_vocabulary

    success = delete_vocabulary(vocab_id, db_path=db_path)
    assert success is True

    vocab = get_vocabulary_by_id(vocab_id, db_path=db_path)
    assert vocab is None


def test_delete_vocabulary_not_found(clean_db):
    """Test deleting non-existent vocabulary returns False."""
    success = delete_vocabulary(9999, db_path=clean_db)
    assert success is False


# ============================================================================
# Kanji Tests
# ============================================================================

def test_add_kanji_success(clean_db, sample_kanji):
    """Test adding kanji with all fields."""
    kanji_id = add_kanji(**sample_kanji, db_path=clean_db)
    assert kanji_id > 0


def test_get_kanji_by_id_success(db_with_kanji):
    """Test retrieving kanji by ID."""
    db_path, kanji_id = db_with_kanji

    kanji = get_kanji_by_id(kanji_id, db_path=db_path)

    assert kanji is not None
    assert kanji["id"] == kanji_id
    assert kanji["character"] == "語"


def test_get_kanji_by_character_success(db_with_kanji):
    """Test retrieving kanji by character."""
    db_path, _ = db_with_kanji

    kanji = get_kanji_by_character("語", db_path=db_path)

    assert kanji is not None
    assert kanji["character"] == "語"


def test_get_kanji_by_id_not_found(clean_db):
    """Test that getting non-existent kanji returns None."""
    kanji = get_kanji_by_id(9999, db_path=clean_db)
    assert kanji is None


def test_list_kanji_with_jlpt_filter(clean_db):
    """Test listing kanji filtered by JLPT level (flashcards only)."""
    from fsrs import Card

    kanji_id_1 = add_kanji(
        character="語",
        on_readings=["ゴ"],
        kun_readings=[],
        meanings={"en": ["language"]},
        jlpt_level="n5",
        db_path=clean_db
    )
    kanji_id_2 = add_kanji(
        character="読",
        on_readings=["ドク"],
        kun_readings=["よ.む"],
        meanings={"en": ["read"]},
        jlpt_level="n4",
        db_path=clean_db
    )

    # Create review entries for both
    card = Card()
    create_review(
        item_id=kanji_id_1,
        item_type="kanji",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=clean_db
    )
    create_review(
        item_id=kanji_id_2,
        item_type="kanji",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=clean_db
    )

    n5_kanji = list_kanji(jlpt_level="n5", db_path=clean_db)
    assert len(n5_kanji) == 1
    assert n5_kanji[0]["character"] == "語"


def test_list_kanji_only_shows_flashcards(clean_db):
    """Test that list_kanji only shows items with review entries."""
    from fsrs import Card

    # Add kanji WITHOUT review entry
    kanji_id_no_review = add_kanji(
        character="無",
        on_readings=["ム"],
        kun_readings=["な.い"],
        meanings={"en": ["nothing"]},
        db_path=clean_db
    )

    # Add kanji WITH review entry
    kanji_id_with_review = add_kanji(
        character="有",
        on_readings=["ユウ", "ウ"],
        kun_readings=["あ.る"],
        meanings={"en": ["exist"]},
        db_path=clean_db
    )
    card = Card()
    create_review(
        item_id=kanji_id_with_review,
        item_type="kanji",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=clean_db
    )

    # List should only return the one with review entry
    kanji_list = list_kanji(db_path=clean_db)
    assert len(kanji_list) == 1
    assert kanji_list[0]["id"] == kanji_id_with_review
    assert kanji_list[0]["character"] == "有"


def test_search_kanji(db_with_kanji):
    """Test searching kanji by character/readings/meaning."""
    db_path, _ = db_with_kanji

    # Search by character
    results = search_kanji("語", db_path=db_path)
    assert len(results) >= 1


def test_search_kanji_by_reading_excludes_flashcards(db_with_kanji):
    """Test that search_kanji_by_reading excludes items with review entries."""
    from japanese_cli.database import search_kanji_by_reading
    from fsrs import Card

    db_path, kanji_id = db_with_kanji

    # Initially, search should return the kanji (on-yomi)
    results = search_kanji_by_reading("ゴ", reading_type="on", db_path=db_path)
    assert len(results) == 1
    assert results[0]["id"] == kanji_id

    # Create a review entry (making it a flashcard)
    card = Card()
    create_review(
        item_id=kanji_id,
        item_type="kanji",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=db_path
    )

    # Now search should return nothing (kanji is now a flashcard)
    results = search_kanji_by_reading("ゴ", reading_type="on", db_path=db_path)
    assert len(results) == 0


def test_search_kanji_by_kun_reading_excludes_flashcards(clean_db):
    """Test that kun-yomi search excludes flashcards."""
    from japanese_cli.database import search_kanji_by_reading
    from fsrs import Card

    # Add kanji
    kanji_id = add_kanji(
        character="語",
        on_readings=["ゴ"],
        kun_readings=["かた.る", "かた.らう"],
        meanings={"en": ["word", "language"]},
        db_path=clean_db
    )

    # Initially, kun-yomi search should return the kanji
    results = search_kanji_by_reading("かた.る", reading_type="kun", db_path=clean_db)
    assert len(results) == 1
    assert results[0]["id"] == kanji_id

    # Create a review entry (making it a flashcard)
    card = Card()
    create_review(
        item_id=kanji_id,
        item_type="kanji",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=clean_db
    )

    # Now kun-yomi search should return nothing
    results = search_kanji_by_reading("かた.る", reading_type="kun", db_path=clean_db)
    assert len(results) == 0


def test_search_kanji_by_both_readings_excludes_flashcards(clean_db):
    """Test that 'both' reading type search excludes flashcards."""
    from japanese_cli.database import search_kanji_by_reading
    from fsrs import Card

    # Add two kanji
    kanji1_id = add_kanji(
        character="語",
        on_readings=["ゴ"],
        kun_readings=["かた.る"],
        meanings={"en": ["word"]},
        db_path=clean_db
    )
    kanji2_id = add_kanji(
        character="話",
        on_readings=["ワ"],
        kun_readings=["はな.す"],
        meanings={"en": ["talk"]},
        db_path=clean_db
    )

    # Both should be found with 'both' reading type search
    results = search_kanji_by_reading("ゴ", reading_type="both", db_path=clean_db)
    assert len(results) == 1
    assert results[0]["id"] == kanji1_id

    # Add kanji1 as flashcard
    card = Card()
    create_review(
        item_id=kanji1_id,
        item_type="kanji",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=clean_db
    )

    # Now search should return nothing
    results = search_kanji_by_reading("ゴ", reading_type="both", db_path=clean_db)
    assert len(results) == 0


def test_update_kanji_success(db_with_kanji):
    """Test updating kanji fields."""
    db_path, kanji_id = db_with_kanji

    success = update_kanji(
        kanji_id,
        notes="Updated kanji notes",
        db_path=db_path
    )

    assert success is True

    kanji = get_kanji_by_id(kanji_id, db_path=db_path)
    assert kanji["notes"] == "Updated kanji notes"


def test_update_kanji_not_found(clean_db):
    """Test updating non-existent kanji returns False."""
    success = update_kanji(9999, notes="test", db_path=clean_db)
    assert success is False


def test_delete_kanji_success(db_with_kanji):
    """Test deleting kanji."""
    db_path, kanji_id = db_with_kanji

    success = delete_kanji(kanji_id, db_path=db_path)
    assert success is True

    kanji = get_kanji_by_id(kanji_id, db_path=db_path)
    assert kanji is None


# ============================================================================
# Grammar Tests
# ============================================================================

def test_add_grammar_success(clean_db, sample_grammar):
    """Test adding grammar point."""
    grammar_id = add_grammar(**sample_grammar, db_path=clean_db)
    assert grammar_id > 0


def test_get_grammar_by_id_success(clean_db, sample_grammar):
    """Test retrieving grammar by ID."""
    grammar_id = add_grammar(**sample_grammar, db_path=clean_db)

    grammar = get_grammar_by_id(grammar_id, db_path=clean_db)

    assert grammar is not None
    assert grammar["id"] == grammar_id
    assert grammar["title"] == "は (wa) particle"


def test_get_grammar_by_id_not_found(clean_db):
    """Test that getting non-existent grammar returns None."""
    grammar = get_grammar_by_id(9999, db_path=clean_db)
    assert grammar is None


def test_list_grammar_with_filter(clean_db):
    """Test listing grammar filtered by JLPT level."""
    add_grammar(
        title="test1",
        explanation="exp1",
        examples=[],
        jlpt_level="n5",
        db_path=clean_db
    )
    add_grammar(
        title="test2",
        explanation="exp2",
        examples=[],
        jlpt_level="n4",
        db_path=clean_db
    )

    n5_grammar = list_grammar(jlpt_level="n5", db_path=clean_db)
    assert len(n5_grammar) == 1


def test_update_grammar_success(clean_db, sample_grammar):
    """Test updating grammar point."""
    grammar_id = add_grammar(**sample_grammar, db_path=clean_db)

    success = update_grammar(
        grammar_id,
        notes="Updated grammar notes",
        db_path=clean_db
    )

    assert success is True


def test_delete_grammar_success(clean_db, sample_grammar):
    """Test deleting grammar point."""
    grammar_id = add_grammar(**sample_grammar, db_path=clean_db)

    success = delete_grammar(grammar_id, db_path=clean_db)
    assert success is True

    grammar = get_grammar_by_id(grammar_id, db_path=clean_db)
    assert grammar is None


# ============================================================================
# Review Tests
# ============================================================================

def test_create_review_success(db_with_vocabulary):
    """Test creating a review entry."""
    from fsrs import Card

    db_path, vocab_id = db_with_vocabulary

    card = Card()
    review_id = create_review(
        item_id=vocab_id,
        item_type="vocab",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=db_path
    )

    assert review_id > 0


def test_get_review_success(db_with_review):
    """Test retrieving a review entry."""
    db_path, vocab_id, review_id = db_with_review

    review = get_review(vocab_id, "vocab", db_path=db_path)

    assert review is not None
    assert review["item_id"] == vocab_id
    assert review["item_type"] == "vocab"
    assert review["review_count"] == 0


def test_get_review_not_found(clean_db):
    """Test that getting non-existent review returns None."""
    review = get_review(9999, "vocab", db_path=clean_db)
    assert review is None


def test_has_review_entry(db_with_review, clean_db):
    """Test checking if an item has a review entry."""
    db_path, vocab_id, review_id = db_with_review

    # Item with review entry should return True
    assert has_review_entry(vocab_id, "vocab", db_path=db_path) is True

    # Item without review entry should return False
    assert has_review_entry(9999, "vocab", db_path=db_path) is False

    # Add a kanji without review
    kanji_id = add_kanji(
        character="語",
        on_readings=["ゴ"],
        kun_readings=[],
        meanings={"en": ["language"]},
        db_path=db_path
    )
    assert has_review_entry(kanji_id, "kanji", db_path=db_path) is False


def test_update_review_increments_count(db_with_review):
    """Test that updating review increments review_count."""
    from fsrs import Card, Rating, Scheduler

    db_path, vocab_id, review_id = db_with_review

    # Perform a review
    scheduler = Scheduler()
    card = Card()
    card, _ = scheduler.review_card(card, Rating.Good)

    success = update_review(
        review_id,
        card.to_dict(),
        card.due,
        db_path=db_path
    )

    assert success is True

    review = get_review(vocab_id, "vocab", db_path=db_path)
    assert review["review_count"] == 1
    assert review["last_reviewed"] is not None


def test_get_due_cards_returns_due_items(clean_db):
    """Test that get_due_cards returns only due cards."""
    from fsrs import Card

    # Add vocabulary
    vocab_id = add_vocabulary(
        word="due",
        reading="reading",
        meanings={"en": ["test"]},
        db_path=clean_db
    )

    # Create review with due date in the past
    card = Card()
    card.due = datetime.now(timezone.utc) - timedelta(hours=1)

    create_review(
        item_id=vocab_id,
        item_type="vocab",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=clean_db
    )

    # Get due cards
    due_cards = get_due_cards(db_path=clean_db)

    assert len(due_cards) == 1
    assert due_cards[0]["item_id"] == vocab_id


def test_get_due_cards_excludes_future_items(clean_db):
    """Test that get_due_cards excludes cards due in the future."""
    from fsrs import Card

    vocab_id = add_vocabulary(
        word="future",
        reading="reading",
        meanings={"en": ["test"]},
        db_path=clean_db
    )

    # Create review with due date in the future
    card = Card()
    card.due = datetime.now(timezone.utc) + timedelta(days=1)

    create_review(
        item_id=vocab_id,
        item_type="vocab",
        fsrs_card_state=card.to_dict(),
        due_date=card.due,
        db_path=clean_db
    )

    due_cards = get_due_cards(db_path=clean_db)
    assert len(due_cards) == 0


def test_get_due_cards_with_item_type_filter(clean_db):
    """Test filtering due cards by item type."""
    from fsrs import Card

    # Add both vocab and kanji
    vocab_id = add_vocabulary(
        word="vocab",
        reading="reading",
        meanings={"en": ["test"]},
        db_path=clean_db
    )
    kanji_id = add_kanji(
        character="漢",
        on_readings=["カン"],
        kun_readings=[],
        meanings={"en": ["kanji"]},
        db_path=clean_db
    )

    # Create reviews for both (both due)
    card = Card()
    card.due = datetime.now(timezone.utc) - timedelta(hours=1)

    create_review(vocab_id, "vocab", card.to_dict(), card.due, clean_db)
    create_review(kanji_id, "kanji", card.to_dict(), card.due, clean_db)

    # Test filtering
    vocab_only = get_due_cards(item_type="vocab", db_path=clean_db)
    kanji_only = get_due_cards(item_type="kanji", db_path=clean_db)

    assert len(vocab_only) == 1
    assert len(kanji_only) == 1
    assert vocab_only[0]["item_type"] == "vocab"
    assert kanji_only[0]["item_type"] == "kanji"


def test_add_review_history(db_with_review):
    """Test adding review history entry."""
    db_path, _, review_id = db_with_review

    history_id = add_review_history(
        review_id=review_id,
        rating=3,
        duration_ms=5000,
        db_path=db_path
    )

    assert history_id > 0


# ============================================================================
# Progress Tests
# ============================================================================

def test_get_progress_default_user(clean_db):
    """Test getting progress for default user."""
    # Progress should be initialized during clean_db setup
    progress = get_progress(db_path=clean_db)

    assert progress is not None
    assert progress["user_id"] == "default"
    assert progress["current_level"] == "n5"


def test_init_progress_creates_entry(temp_db_path):
    """Test initializing progress creates a new entry."""
    from japanese_cli.database import initialize_database

    initialize_database(temp_db_path)

    progress_id = init_progress(user_id="test_user", db_path=temp_db_path)

    assert progress_id > 0

    progress = get_progress("test_user", db_path=temp_db_path)
    assert progress["user_id"] == "test_user"


def test_update_progress_stats(clean_db):
    """Test updating progress statistics."""
    new_stats = {
        "total_vocab": 100,
        "total_kanji": 50,
        "mastered_vocab": 10,
        "mastered_kanji": 5
    }

    success = update_progress(new_stats, db_path=clean_db)
    assert success is True

    progress = get_progress(db_path=clean_db)
    import json
    stats = json.loads(progress["stats"])
    assert stats["total_vocab"] == 100


def test_increment_streak(clean_db):
    """Test incrementing study streak."""
    success = increment_streak(db_path=clean_db)
    assert success is True

    progress = get_progress(db_path=clean_db)
    assert progress["streak_days"] == 1
    assert progress["last_review_date"] is not None
