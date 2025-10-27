"""Vocabulary-related tools for the AI agent."""

import json
from typing import Optional

from strands import tool

from japanese_cli.database.queries import list_vocabulary, search_vocabulary


@tool
def get_vocabulary(
    search_term: Optional[str] = None,
    jlpt_level: Optional[str] = None,
    limit: int = 10
) -> dict:
    """
    Search or list vocabulary entries from the Japanese learning database.

    This tool allows you to find Japanese vocabulary with their readings, meanings,
    and Vietnamese readings. You can search by word/reading/meaning or filter by JLPT level.

    Args:
        search_term: Optional search term to find in word, reading, or meanings.
                    Leave empty to list all vocabulary.
        jlpt_level: Filter by JLPT level (n5, n4, n3, n2, n1). Optional.
        limit: Maximum number of results to return (default: 10, max: 50)

    Returns:
        Dict containing status and vocabulary entries with:
        - word: Japanese word (kanji/kana form)
        - reading: Hiragana/katakana reading
        - meanings: Vietnamese and English meanings (JSON format)
        - vietnamese_reading: Sino-Vietnamese reading if available
        - jlpt_level: JLPT level
        - part_of_speech: Word type (noun, verb, etc.)
        - tags: Additional tags

    Examples:
        - get_vocabulary(search_term="食べる", limit=5)
        - get_vocabulary(jlpt_level="n5", limit=20)
        - get_vocabulary(search_term="eat", jlpt_level="n5")
    """
    # Validate limit
    if limit > 50:
        limit = 50
    if limit < 1:
        limit = 1

    # Validate JLPT level if provided
    if jlpt_level and jlpt_level not in ["n5", "n4", "n3", "n2", "n1"]:
        return {
            "status": "error",
            "content": [{
                "text": f"Invalid JLPT level '{jlpt_level}'. Must be one of: n5, n4, n3, n2, n1"
            }]
        }

    try:
        # Search or list based on search_term
        if search_term:
            results = search_vocabulary(
                search_term=search_term,
                jlpt_level=jlpt_level
            )[:limit]
        else:
            results = list_vocabulary(
                jlpt_level=jlpt_level,
                limit=limit
            )

        if not results:
            search_info = f"search term '{search_term}'" if search_term else "specified criteria"
            level_info = f" in JLPT {jlpt_level.upper()}" if jlpt_level else ""
            return {
                "status": "success",
                "content": [{
                    "text": f"No vocabulary found for {search_info}{level_info}."
                }]
            }

        # Format results for display
        formatted_results = []
        for vocab in results:
            # Parse meanings JSON
            try:
                meanings_dict = json.loads(vocab["meanings"])
                vi_meanings = meanings_dict.get("vi", [])
                en_meanings = meanings_dict.get("en", [])
                meanings_str = (
                    f"VI: {', '.join(vi_meanings[:3])}"
                    + (f" | EN: {', '.join(en_meanings[:3])}" if en_meanings else "")
                )
            except (json.JSONDecodeError, KeyError):
                meanings_str = vocab.get("meanings", "N/A")

            formatted_results.append({
                "word": vocab["word"],
                "reading": vocab["reading"],
                "meanings": meanings_str,
                "vietnamese_reading": vocab.get("vietnamese_reading") or "N/A",
                "jlpt_level": vocab.get("jlpt_level") or "N/A",
                "part_of_speech": vocab.get("part_of_speech") or "N/A"
            })

        # Create summary text
        count_text = f"Found {len(results)} vocabulary entr{'y' if len(results) == 1 else 'ies'}"
        if search_term:
            count_text += f" matching '{search_term}'"
        if jlpt_level:
            count_text += f" (JLPT {jlpt_level.upper()})"

        result_text = f"{count_text}:\n\n"
        for i, entry in enumerate(formatted_results, 1):
            result_text += (
                f"{i}. {entry['word']}[{entry['reading']}]\n"
                f"   Meanings: {entry['meanings']}\n"
                f"   Hán Việt: {entry['vietnamese_reading']}\n"
                f"   Level: {entry['jlpt_level']} | POS: {entry['part_of_speech']}\n\n"
            )

        return {
            "status": "success",
            "content": [{"text": result_text.strip()}]
        }

    except Exception as e:
        return {
            "status": "error",
            "content": [{
                "text": f"Error retrieving vocabulary: {str(e)}"
            }]
        }
