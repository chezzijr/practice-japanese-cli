"""Review and SRS-related tools for the AI agent."""

import json
from typing import Optional

from strands import tool

from japanese_cli.srs.scheduler import ReviewScheduler
from japanese_cli.srs.mcq_scheduler import MCQReviewScheduler
from japanese_cli.database.queries import get_vocabulary_by_id, get_kanji_by_id


@tool
def get_due_reviews(
    review_type: str = "both",
    jlpt_level: Optional[str] = None,
    item_type: Optional[str] = None,
    limit: int = 20
) -> dict:
    """
    Get information about due reviews (flashcards and/or MCQ quizzes).

    This tool shows what study items are currently due for review using the
    spaced repetition system (SRS). It supports both flashcard reviews and
    multiple-choice question (MCQ) reviews.

    Args:
        review_type: Type of reviews to get:
                    - "flashcard": Regular flashcard reviews only
                    - "mcq": Multiple choice question reviews only
                    - "both": Both types (default)
        jlpt_level: Filter by JLPT level (n5, n4, n3, n2, n1). Optional.
        item_type: Filter by item type:
                  - "vocab": Vocabulary only
                  - "kanji": Kanji only
                  - Leave empty for both
        limit: Maximum number of items to show per review type (default: 20, max: 100)

    Returns:
        Dict containing:
        - Count of due items by type
        - Summary of what's due
        - Breakdown by JLPT level if applicable
        - Sample items from due reviews

    Examples:
        - get_due_reviews()  # All due reviews
        - get_due_reviews(review_type="flashcard", jlpt_level="n5")
        - get_due_reviews(review_type="mcq", item_type="vocab", limit=10)
    """
    # Validate inputs
    if review_type not in ["flashcard", "mcq", "both"]:
        return {
            "status": "error",
            "content": [{
                "text": f"Invalid review_type '{review_type}'. Must be: flashcard, mcq, or both"
            }]
        }

    if jlpt_level and jlpt_level not in ["n5", "n4", "n3", "n2", "n1"]:
        return {
            "status": "error",
            "content": [{
                "text": f"Invalid JLPT level '{jlpt_level}'. Must be one of: n5, n4, n3, n2, n1"
            }]
        }

    if item_type and item_type not in ["vocab", "kanji"]:
        return {
            "status": "error",
            "content": [{
                "text": f"Invalid item_type '{item_type}'. Must be: vocab or kanji"
            }]
        }

    # Validate and cap limit
    if limit > 100:
        limit = 100
    if limit < 1:
        limit = 1

    try:
        result_text = "# Due Reviews Overview\n\n"

        # Get flashcard reviews
        flashcard_due = []
        if review_type in ["flashcard", "both"]:
            scheduler = ReviewScheduler()
            flashcard_due = scheduler.get_due_reviews(
                limit=limit,
                jlpt_level=jlpt_level,
                item_type=item_type
            )

        # Get MCQ reviews
        mcq_due = []
        if review_type in ["mcq", "both"]:
            mcq_scheduler = MCQReviewScheduler()
            mcq_due = mcq_scheduler.get_due_mcqs(
                limit=limit,
                jlpt_level=jlpt_level,
                item_type=item_type
            )

        # Summary counts
        total_due = len(flashcard_due) + len(mcq_due)

        if total_due == 0:
            level_str = f" in JLPT {jlpt_level.upper()}" if jlpt_level else ""
            type_str = f" {item_type}" if item_type else ""
            review_str = {"flashcard": "flashcard", "mcq": "MCQ", "both": ""}.get(review_type, "")
            result_text += f"🎉 No{type_str} {review_str} reviews are due{level_str}!\n\n"
            result_text += "You're all caught up! Consider:\n"
            result_text += "- Studying new material\n"
            result_text += "- Reviewing grammar points\n"
            result_text += "- Practicing with conversation\n"
            return {
                "status": "success",
                "content": [{"text": result_text}]
            }

        result_text += "## Summary\n"
        if review_type == "both":
            result_text += f"- **Flashcard Reviews Due**: {len(flashcard_due)}\n"
            result_text += f"- **MCQ Reviews Due**: {len(mcq_due)}\n"
            result_text += f"- **Total**: {total_due}\n\n"
        elif review_type == "flashcard":
            result_text += f"- **Flashcard Reviews Due**: {len(flashcard_due)}\n\n"
        else:
            result_text += f"- **MCQ Reviews Due**: {len(mcq_due)}\n\n"

        # Breakdown by type if not filtered
        if not item_type and total_due > 0:
            vocab_count = sum(
                1 for r in flashcard_due if r.item_type.value == "vocab"
            ) + sum(
                1 for r in mcq_due if r.item_type.value == "vocab"
            )
            kanji_count = sum(
                1 for r in flashcard_due if r.item_type.value == "kanji"
            ) + sum(
                1 for r in mcq_due if r.item_type.value == "kanji"
            )

            result_text += "### By Item Type\n"
            result_text += f"- Vocabulary: {vocab_count}\n"
            result_text += f"- Kanji: {kanji_count}\n\n"

        # Show sample items from flashcard reviews
        if flashcard_due:
            result_text += "## Sample Flashcard Reviews\n"
            samples = flashcard_due[:min(5, len(flashcard_due))]

            for i, review in enumerate(samples, 1):
                if review.item_type.value == "vocab":
                    item = get_vocabulary_by_id(review.item_id)
                    if item:
                        try:
                            meanings_dict = json.loads(item["meanings"])
                            vi_meanings = meanings_dict.get("vi", [])
                            meaning_str = ", ".join(vi_meanings[:2])
                        except:
                            meaning_str = "N/A"

                        result_text += (
                            f"{i}. {item['word']}[{item['reading']}] - {meaning_str}\n"
                            f"   Level: {item.get('jlpt_level', 'N/A').upper()}\n"
                        )
                elif review.item_type.value == "kanji":
                    item = get_kanji_by_id(review.item_id)
                    if item:
                        try:
                            meanings_dict = json.loads(item["meanings"])
                            vi_meanings = meanings_dict.get("vi", [])
                            meaning_str = ", ".join(vi_meanings[:2])
                        except:
                            meaning_str = "N/A"

                        result_text += (
                            f"{i}. {item['character']} - {meaning_str}\n"
                            f"   Level: {item.get('jlpt_level', 'N/A').upper()}\n"
                        )

            if len(flashcard_due) > 5:
                result_text += f"\n... and {len(flashcard_due) - 5} more\n"
            result_text += "\n"

        # Show sample items from MCQ reviews
        if mcq_due:
            result_text += "## Sample MCQ Reviews\n"
            samples = mcq_due[:min(5, len(mcq_due))]

            for i, review in enumerate(samples, 1):
                if review.item_type.value == "vocab":
                    item = get_vocabulary_by_id(review.item_id)
                    if item:
                        try:
                            meanings_dict = json.loads(item["meanings"])
                            vi_meanings = meanings_dict.get("vi", [])
                            meaning_str = ", ".join(vi_meanings[:2])
                        except:
                            meaning_str = "N/A"

                        result_text += (
                            f"{i}. {item['word']}[{item['reading']}] - {meaning_str}\n"
                            f"   Level: {item.get('jlpt_level', 'N/A').upper()}\n"
                        )
                elif review.item_type.value == "kanji":
                    item = get_kanji_by_id(review.item_id)
                    if item:
                        try:
                            meanings_dict = json.loads(item["meanings"])
                            vi_meanings = meanings_dict.get("vi", [])
                            meaning_str = ", ".join(vi_meanings[:2])
                        except:
                            meaning_str = "N/A"

                        result_text += (
                            f"{i}. {item['character']} - {meaning_str}\n"
                            f"   Level: {item.get('jlpt_level', 'N/A').upper()}\n"
                        )

            if len(mcq_due) > 5:
                result_text += f"\n... and {len(mcq_due) - 5} more\n"
            result_text += "\n"

        # Action message
        result_text += "---\n\n"
        if total_due > 0:
            result_text += "💡 **Tip**: Start reviewing with:\n"
            if flashcard_due:
                result_text += "- `japanese-cli flashcard review` for flashcard reviews\n"
            if mcq_due:
                result_text += "- `japanese-cli mcq` for multiple choice quizzes\n"

        return {
            "status": "success",
            "content": [{"text": result_text}]
        }

    except Exception as e:
        return {
            "status": "error",
            "content": [{
                "text": f"Error retrieving due reviews: {str(e)}"
            }]
        }
