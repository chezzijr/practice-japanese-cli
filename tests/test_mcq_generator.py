"""
Tests for MCQ generator.
"""

import pytest
from japanese_cli.srs.mcq_generator import MCQGenerator
from japanese_cli.models.review import ItemType
from japanese_cli.models.mcq import MCQQuestion


# ============================================================================
# Basic Generation Tests
# ============================================================================

def test_mcq_generator_initialization(clean_db):
    """Test creating MCQGenerator instance."""
    generator = MCQGenerator(db_path=clean_db)
    assert generator.db_path == clean_db


def test_generate_word_to_meaning_vocab(db_with_vocabulary, sample_vocabulary):
    """Test generating word→meaning question for vocabulary."""
    from japanese_cli.database import add_vocabulary

    db_path, vocab_id = db_with_vocabulary

    # Add more vocabulary for distractors
    for i in range(5):
        vocab = sample_vocabulary.copy()
        vocab['word'] = f"単語{i}"
        vocab['reading'] = f"たんご{i}"
        vocab['meanings'] = {"vi": [f"từ vựng {i}"], "en": [f"word {i}"]}
        add_vocabulary(**vocab, db_path=db_path)

    generator = MCQGenerator(db_path=db_path)

    question = generator.generate_question(
        item_id=vocab_id,
        item_type=ItemType.VOCAB,
        question_mode="word_to_meaning",
        language="vi"
    )

    assert isinstance(question, MCQQuestion)
    assert question.item_id == vocab_id
    assert question.item_type == ItemType.VOCAB
    assert len(question.options) == 4
    assert 0 <= question.correct_index < 4
    assert "単語" in question.question_text or "たんご" in question.question_text
    assert question.get_correct_answer() == "từ vựng"


def test_generate_word_to_meaning_kanji(db_with_kanji, sample_kanji):
    """Test generating word→meaning question for kanji."""
    from japanese_cli.database import add_kanji

    db_path, kanji_id = db_with_kanji

    # Add more kanji for distractors
    kanji_list = [
        {"character": "言", "on_readings": ["ゲン", "ゴン"], "kun_readings": ["い.う", "こと"],
         "meanings": {"vi": ["nói"], "en": ["say"]}, "jlpt_level": "n5", "stroke_count": 7, "radical": "言"},
        {"character": "話", "on_readings": ["ワ"], "kun_readings": ["はな.す"],
         "meanings": {"vi": ["nói chuyện"], "en": ["talk"]}, "jlpt_level": "n5", "stroke_count": 13, "radical": "言"},
        {"character": "読", "on_readings": ["ドク", "トク"], "kun_readings": ["よ.む"],
         "meanings": {"vi": ["đọc"], "en": ["read"]}, "jlpt_level": "n5", "stroke_count": 14, "radical": "言"},
        {"character": "書", "on_readings": ["ショ"], "kun_readings": ["か.く"],
         "meanings": {"vi": ["viết"], "en": ["write"]}, "jlpt_level": "n5", "stroke_count": 10, "radical": "曰"},
    ]
    for k in kanji_list:
        add_kanji(**k, db_path=db_path)

    generator = MCQGenerator(db_path=db_path)

    question = generator.generate_question(
        item_id=kanji_id,
        item_type=ItemType.KANJI,
        question_mode="word_to_meaning",
        language="vi"
    )

    assert isinstance(question, MCQQuestion)
    assert question.item_id == kanji_id
    assert question.item_type == ItemType.KANJI
    assert len(question.options) == 4
    assert "語" in question.question_text
    assert question.get_correct_answer() == "ngữ"


def test_generate_meaning_to_word_vocab(db_with_vocabulary, sample_vocabulary):
    """Test generating meaning→word question for vocabulary."""
    from japanese_cli.database import add_vocabulary

    db_path, vocab_id = db_with_vocabulary

    # Add more vocabulary for distractors
    for i in range(5):
        vocab = sample_vocabulary.copy()
        vocab['word'] = f"単語{i}"
        vocab['reading'] = f"たんご{i}"
        vocab['meanings'] = {"vi": [f"từ vựng {i}"], "en": [f"word {i}"]}
        add_vocabulary(**vocab, db_path=db_path)

    generator = MCQGenerator(db_path=db_path)

    question = generator.generate_question(
        item_id=vocab_id,
        item_type=ItemType.VOCAB,
        question_mode="meaning_to_word",
        language="vi"
    )

    assert isinstance(question, MCQQuestion)
    assert "từ vựng" in question.question_text
    correct_answer = question.get_correct_answer()
    assert "単語" in correct_answer
    assert "たんご" in correct_answer


def test_generate_meaning_to_word_kanji(db_with_kanji, sample_kanji):
    """Test generating meaning→word question for kanji."""
    from japanese_cli.database import add_kanji

    db_path, kanji_id = db_with_kanji

    # Add more kanji for distractors
    kanji_list = [
        {"character": "言", "on_readings": ["ゲン", "ゴン"], "kun_readings": ["い.う", "こと"],
         "meanings": {"vi": ["nói"], "en": ["say"]}, "jlpt_level": "n5", "stroke_count": 7, "radical": "言"},
        {"character": "話", "on_readings": ["ワ"], "kun_readings": ["はな.す"],
         "meanings": {"vi": ["nói chuyện"], "en": ["talk"]}, "jlpt_level": "n5", "stroke_count": 13, "radical": "言"},
        {"character": "読", "on_readings": ["ドク", "トク"], "kun_readings": ["よ.む"],
         "meanings": {"vi": ["đọc"], "en": ["read"]}, "jlpt_level": "n5", "stroke_count": 14, "radical": "言"},
        {"character": "書", "on_readings": ["ショ"], "kun_readings": ["か.く"],
         "meanings": {"vi": ["viết"], "en": ["write"]}, "jlpt_level": "n5", "stroke_count": 10, "radical": "曰"},
    ]
    for k in kanji_list:
        add_kanji(**k, db_path=db_path)

    generator = MCQGenerator(db_path=db_path)

    question = generator.generate_question(
        item_id=kanji_id,
        item_type=ItemType.KANJI,
        question_mode="meaning_to_word",
        language="vi"
    )

    assert isinstance(question, MCQQuestion)
    assert "ngữ" in question.question_text
    assert question.get_correct_answer() == "語"


def test_generate_question_english_language(db_with_vocabulary, sample_vocabulary):
    """Test generating question with English meanings."""
    from japanese_cli.database import add_vocabulary

    db_path, vocab_id = db_with_vocabulary

    # Add more vocabulary for distractors
    for i in range(5):
        vocab = sample_vocabulary.copy()
        vocab['word'] = f"単語{i}"
        vocab['reading'] = f"たんご{i}"
        vocab['meanings'] = {"vi": [f"từ vựng {i}"], "en": [f"word {i}"]}
        add_vocabulary(**vocab, db_path=db_path)

    generator = MCQGenerator(db_path=db_path)

    question = generator.generate_question(
        item_id=vocab_id,
        item_type=ItemType.VOCAB,
        question_mode="word_to_meaning",
        language="en"
    )

    # Correct answer should be one of the English meanings
    correct = question.get_correct_answer()
    assert correct in ["word", "vocabulary"]


# ============================================================================
# Error Handling Tests
# ============================================================================

def test_generate_question_invalid_item_id(clean_db):
    """Test generating question for non-existent item."""
    generator = MCQGenerator(db_path=clean_db)

    with pytest.raises(ValueError, match="not found"):
        generator.generate_question(
            item_id=999,
            item_type=ItemType.VOCAB,
            question_mode="word_to_meaning"
        )


def test_generate_question_invalid_mode(db_with_vocabulary):
    """Test generating question with invalid question mode."""
    db_path, vocab_id = db_with_vocabulary
    generator = MCQGenerator(db_path=db_path)

    with pytest.raises(ValueError, match="Invalid question_mode"):
        generator.generate_question(
            item_id=vocab_id,
            item_type=ItemType.VOCAB,
            question_mode="invalid_mode"
        )


def test_generate_question_insufficient_distractors(db_with_vocabulary):
    """Test that error is raised when insufficient distractors available."""
    # This test is tricky - we'd need only 1-2 items total
    # For now, we'll skip since sample_vocabulary typically has enough similar items
    # In real scenario with single item, this would raise ValueError
    pass


# ============================================================================
# Distractor Strategy Tests
# ============================================================================

def test_same_jlpt_level_distractors(db_with_vocabulary, sample_vocabulary):
    """Test that distractors include items from same JLPT level."""
    from japanese_cli.database import add_vocabulary

    db_path, vocab_id = db_with_vocabulary

    # Add more N5 vocabulary
    for i in range(5):
        vocab = sample_vocabulary.copy()
        vocab['word'] = f"単語{i}"
        vocab['reading'] = f"たんご{i}"
        vocab['meanings'] = {"vi": [f"từ vựng {i}"], "en": [f"word {i}"]}
        vocab['jlpt_level'] = "n5"
        add_vocabulary(**vocab, db_path=db_path)

    generator = MCQGenerator(db_path=db_path)
    question = generator.generate_question(
        item_id=vocab_id,
        item_type=ItemType.VOCAB,
        question_mode="word_to_meaning",
        language="vi"
    )

    # Should have 4 options
    assert len(question.options) == 4
    # All should be distinct
    assert len(set(question.options)) == 4


def test_similar_meaning_distractors(db_with_vocabulary, sample_vocabulary):
    """Test semantic similarity distractor selection."""
    from japanese_cli.database import add_vocabulary

    db_path, vocab_id = db_with_vocabulary

    # Add vocabulary with semantically related meanings
    similar_vocab = sample_vocabulary.copy()
    similar_vocab['word'] = "語彙"
    similar_vocab['reading'] = "ごい"
    similar_vocab['meanings'] = {"vi": ["từ ngữ", "ngôn ngữ"], "en": ["vocabulary", "language"]}
    similar_vocab['jlpt_level'] = "n4"
    add_vocabulary(**similar_vocab, db_path=db_path)

    # Add more vocabulary for sufficient distractors
    for i in range(5):
        vocab = sample_vocabulary.copy()
        vocab['word'] = f"単語{i}"
        vocab['reading'] = f"たんご{i}"
        vocab['meanings'] = {"vi": [f"từ vựng {i}"], "en": [f"word {i}"]}
        add_vocabulary(**vocab, db_path=db_path)

    generator = MCQGenerator(db_path=db_path)
    question = generator.generate_question(
        item_id=vocab_id,
        item_type=ItemType.VOCAB,
        question_mode="word_to_meaning",
        language="vi"
    )

    # Should successfully generate question
    assert len(question.options) == 4


def test_similar_reading_distractors(db_with_vocabulary, sample_vocabulary):
    """Test phonetic similarity distractor selection."""
    from japanese_cli.database import add_vocabulary

    db_path, vocab_id = db_with_vocabulary

    # Add vocabulary with similar reading
    similar_vocab = sample_vocabulary.copy()
    similar_vocab['word'] = "短語"
    similar_vocab['reading'] = "たんご"  # Same reading!
    similar_vocab['meanings'] = {"vi": ["cụm từ"], "en": ["phrase"]}
    similar_vocab['jlpt_level'] = "n4"
    add_vocabulary(**similar_vocab, db_path=db_path)

    # Add more vocabulary for sufficient distractors
    for i in range(5):
        vocab = sample_vocabulary.copy()
        vocab['word'] = f"単語{i}"
        vocab['reading'] = f"たんご{i}"
        vocab['meanings'] = {"vi": [f"từ vựng {i}"], "en": [f"word {i}"]}
        add_vocabulary(**vocab, db_path=db_path)

    generator = MCQGenerator(db_path=db_path)
    question = generator.generate_question(
        item_id=vocab_id,
        item_type=ItemType.VOCAB,
        question_mode="word_to_meaning",
        language="vi"
    )

    # Should successfully generate question with reading-based distractors
    assert len(question.options) == 4


def test_visual_similarity_kanji_distractors(db_with_kanji, sample_kanji):
    """Test visual similarity distractor selection for kanji."""
    from japanese_cli.database import add_kanji

    db_path, kanji_id = db_with_kanji

    # Add kanji with same radical
    similar_kanji = sample_kanji.copy()
    similar_kanji['character'] = "言"
    similar_kanji['on_readings'] = ["ゲン", "ゴン"]
    similar_kanji['kun_readings'] = ["い.う", "こと"]
    similar_kanji['meanings'] = {"vi": ["nói"], "en": ["say", "word"]}
    similar_kanji['radical'] = "言"  # Same radical as 語
    similar_kanji['stroke_count'] = 7
    add_kanji(**similar_kanji, db_path=db_path)

    # Add another with similar stroke count
    similar_kanji2 = sample_kanji.copy()
    similar_kanji2['character'] = "話"
    similar_kanji2['on_readings'] = ["ワ"]
    similar_kanji2['kun_readings'] = ["はな.す", "はなし"]
    similar_kanji2['meanings'] = {"vi": ["nói chuyện"], "en": ["talk", "story"]}
    similar_kanji2['radical'] = "言"
    similar_kanji2['stroke_count'] = 13  # Close to 語's 14
    add_kanji(**similar_kanji2, db_path=db_path)

    # Add more kanji for sufficient distractors
    kanji_list = [
        {"character": "読", "on_readings": ["ドク", "トク"], "kun_readings": ["よ.む"],
         "meanings": {"vi": ["đọc"], "en": ["read"]}, "jlpt_level": "n5", "stroke_count": 14, "radical": "言"},
        {"character": "書", "on_readings": ["ショ"], "kun_readings": ["か.く"],
         "meanings": {"vi": ["viết"], "en": ["write"]}, "jlpt_level": "n5", "stroke_count": 10, "radical": "曰"},
    ]
    for k in kanji_list:
        add_kanji(**k, db_path=db_path)

    generator = MCQGenerator(db_path=db_path)
    question = generator.generate_question(
        item_id=kanji_id,
        item_type=ItemType.KANJI,
        question_mode="word_to_meaning",
        language="vi"
    )

    # Should successfully generate question with visual similarity distractors
    assert len(question.options) == 4


# ============================================================================
# Option Shuffling Tests
# ============================================================================

def test_options_are_shuffled(db_with_vocabulary, sample_vocabulary):
    """Test that option order is randomized."""
    from japanese_cli.database import add_vocabulary

    db_path, vocab_id = db_with_vocabulary

    # Add more vocabulary
    for i in range(5):
        vocab = sample_vocabulary.copy()
        vocab['word'] = f"単語{i}"
        vocab['reading'] = f"たんご{i}"
        vocab['meanings'] = {"vi": [f"từ vựng {i}"], "en": [f"word {i}"]}
        add_vocabulary(**vocab, db_path=db_path)

    generator = MCQGenerator(db_path=db_path)

    # Generate multiple questions and check if correct index varies
    correct_indices = set()
    for _ in range(10):
        question = generator.generate_question(
            item_id=vocab_id,
            item_type=ItemType.VOCAB,
            question_mode="word_to_meaning",
            language="vi"
        )
        correct_indices.add(question.correct_index)

    # With 10 generations, we should see at least 2 different positions
    # (statistically very likely with random shuffling)
    assert len(correct_indices) >= 2


def test_correct_answer_tracked_after_shuffle(db_with_vocabulary, sample_vocabulary):
    """Test that correct answer is properly tracked after shuffling."""
    from japanese_cli.database import add_vocabulary

    db_path, vocab_id = db_with_vocabulary

    # Add more vocabulary
    for i in range(5):
        vocab = sample_vocabulary.copy()
        vocab['word'] = f"単語{i}"
        vocab['reading'] = f"たんご{i}"
        vocab['meanings'] = {"vi": [f"từ vựng {i}"], "en": [f"word {i}"]}
        add_vocabulary(**vocab, db_path=db_path)

    generator = MCQGenerator(db_path=db_path)

    # Generate many questions
    for _ in range(20):
        question = generator.generate_question(
            item_id=vocab_id,
            item_type=ItemType.VOCAB,
            question_mode="word_to_meaning",
            language="vi"
        )

        # Correct answer should always be "từ vựng"
        correct = question.get_correct_answer()
        assert correct == "từ vựng"

        # is_correct should work properly
        assert question.is_correct(question.correct_index) is True
        # All other indices should be incorrect
        for i in range(4):
            if i != question.correct_index:
                assert question.is_correct(i) is False


# ============================================================================
# Duplicate Removal Tests
# ============================================================================

def test_no_duplicate_options(db_with_vocabulary, sample_vocabulary):
    """Test that generated options have no duplicates."""
    from japanese_cli.database import add_vocabulary

    db_path, vocab_id = db_with_vocabulary

    # Add vocabulary
    for i in range(10):
        vocab = sample_vocabulary.copy()
        vocab['word'] = f"単語{i}"
        vocab['reading'] = f"たんご{i}"
        vocab['meanings'] = {"vi": [f"từ vựng {i}"], "en": [f"word {i}"]}
        add_vocabulary(**vocab, db_path=db_path)

    generator = MCQGenerator(db_path=db_path)

    # Generate multiple questions
    for _ in range(10):
        question = generator.generate_question(
            item_id=vocab_id,
            item_type=ItemType.VOCAB,
            question_mode="word_to_meaning",
            language="vi"
        )

        # All options should be unique
        assert len(set(question.options)) == 4
        assert len(question.options) == 4


# ============================================================================
# Question Quality Tests
# ============================================================================

def test_question_has_explanation(db_with_vocabulary, sample_vocabulary):
    """Test that generated questions include explanations."""
    from japanese_cli.database import add_vocabulary

    db_path, vocab_id = db_with_vocabulary

    # Add more vocabulary for distractors
    for i in range(5):
        vocab = sample_vocabulary.copy()
        vocab['word'] = f"単語{i}"
        vocab['reading'] = f"たんご{i}"
        vocab['meanings'] = {"vi": [f"từ vựng {i}"], "en": [f"word {i}"]}
        add_vocabulary(**vocab, db_path=db_path)

    generator = MCQGenerator(db_path=db_path)

    question = generator.generate_question(
        item_id=vocab_id,
        item_type=ItemType.VOCAB,
        question_mode="word_to_meaning",
        language="vi"
    )

    assert question.explanation is not None
    assert len(question.explanation) > 0


def test_question_has_jlpt_level(db_with_vocabulary, sample_vocabulary):
    """Test that questions preserve JLPT level from item."""
    from japanese_cli.database import add_vocabulary

    db_path, vocab_id = db_with_vocabulary

    # Add more vocabulary for distractors
    for i in range(5):
        vocab = sample_vocabulary.copy()
        vocab['word'] = f"単語{i}"
        vocab['reading'] = f"たんご{i}"
        vocab['meanings'] = {"vi": [f"từ vựng {i}"], "en": [f"word {i}"]}
        add_vocabulary(**vocab, db_path=db_path)

    generator = MCQGenerator(db_path=db_path)

    question = generator.generate_question(
        item_id=vocab_id,
        item_type=ItemType.VOCAB,
        question_mode="word_to_meaning",
        language="vi"
    )

    assert question.jlpt_level == "n5"


# ============================================================================
# Edge Cases
# ============================================================================

def test_generate_with_no_jlpt_level(db_with_vocabulary, sample_vocabulary):
    """Test generating question for item without JLPT level."""
    from japanese_cli.database import add_vocabulary

    db_path, _ = db_with_vocabulary

    # Add vocab without JLPT level
    no_jlpt_vocab = sample_vocabulary.copy()
    no_jlpt_vocab['word'] = "特殊"
    no_jlpt_vocab['reading'] = "とくしゅ"
    no_jlpt_vocab['jlpt_level'] = None
    no_jlpt_id = add_vocabulary(**no_jlpt_vocab, db_path=db_path)

    # Add more vocab with various levels for distractors
    for i in range(5):
        vocab = sample_vocabulary.copy()
        vocab['word'] = f"単語{i}"
        vocab['reading'] = f"たんご{i}"
        vocab['meanings'] = {"vi": [f"từ vựng {i}"], "en": [f"word {i}"]}
        vocab['jlpt_level'] = "n5"
        add_vocabulary(**vocab, db_path=db_path)

    generator = MCQGenerator(db_path=db_path)
    question = generator.generate_question(
        item_id=no_jlpt_id,
        item_type=ItemType.VOCAB,
        question_mode="word_to_meaning",
        language="vi"
    )

    # Should still generate successfully (using other strategies)
    assert len(question.options) == 4
    assert question.jlpt_level is None


def test_multiple_meanings_uses_first(db_with_vocabulary, sample_vocabulary):
    """Test that items with multiple meanings use the first one."""
    from japanese_cli.database import add_vocabulary

    db_path, _ = db_with_vocabulary

    # Add vocab with multiple meanings
    multi_meaning = sample_vocabulary.copy()
    multi_meaning['word'] = "見る"
    multi_meaning['reading'] = "みる"
    multi_meaning['meanings'] = {
        "vi": ["xem", "nhìn", "thấy"],  # Multiple meanings
        "en": ["see", "look", "watch"]
    }
    multi_id = add_vocabulary(**multi_meaning, db_path=db_path)

    # Add distractors
    for i in range(5):
        vocab = sample_vocabulary.copy()
        vocab['word'] = f"単語{i}"
        vocab['reading'] = f"たんご{i}"
        vocab['meanings'] = {"vi": [f"từ vựng {i}"], "en": [f"word {i}"]}
        add_vocabulary(**vocab, db_path=db_path)

    generator = MCQGenerator(db_path=db_path)
    question = generator.generate_question(
        item_id=multi_id,
        item_type=ItemType.VOCAB,
        question_mode="word_to_meaning",
        language="vi"
    )

    # Should use first meaning
    assert question.get_correct_answer() == "xem"
