"""Kanji-related tools for the AI agent."""

import json
from typing import Optional

from strands import tool

from japanese_cli.database.queries import list_kanji, search_kanji


@tool
def get_kanji(
    search_term: Optional[str] = None,
    jlpt_level: Optional[str] = None,
    limit: int = 10
) -> dict:
    """
    Search or list kanji characters from the Japanese learning database.

    This tool allows you to find kanji with their readings (on-yomi, kun-yomi), meanings,
    and Vietnamese readings (Hán Việt). You can search by character/reading/meaning or filter by JLPT level.

    Args:
        search_term: Optional search term to find in character, readings, or meanings.
                    Leave empty to list all kanji.
        jlpt_level: Filter by JLPT level (n5, n4, n3, n2, n1). Optional.
        limit: Maximum number of results to return (default: 10, max: 50)

    Returns:
        Dict containing status and kanji entries with:
        - character: The kanji character
        - on_readings: On-yomi readings (Chinese-based readings) in JSON array
        - kun_readings: Kun-yomi readings (Japanese readings) in JSON array
        - meanings: Vietnamese and English meanings (JSON format)
        - vietnamese_reading: Hán Việt reading
        - jlpt_level: JLPT level
        - stroke_count: Number of strokes
        - radical: Kanji radical

    Examples:
        - get_kanji(search_term="食", limit=5)
        - get_kanji(jlpt_level="n5", limit=20)
        - get_kanji(search_term="eat", jlpt_level="n5")
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
            results = search_kanji(
                search_term=search_term,
                jlpt_level=jlpt_level
            )[:limit]
        else:
            results = list_kanji(
                jlpt_level=jlpt_level,
                limit=limit
            )

        if not results:
            search_info = f"search term '{search_term}'" if search_term else "specified criteria"
            level_info = f" in JLPT {jlpt_level.upper()}" if jlpt_level else ""
            return {
                "status": "success",
                "content": [{
                    "text": f"No kanji found for {search_info}{level_info}."
                }]
            }

        # Format results for display
        formatted_results = []
        for kanji in results:
            # Parse readings JSON
            try:
                on_readings = json.loads(kanji["on_readings"])
                kun_readings = json.loads(kanji["kun_readings"])
                on_str = ", ".join(on_readings[:3]) if on_readings else "N/A"
                kun_str = ", ".join(kun_readings[:3]) if kun_readings else "N/A"
            except (json.JSONDecodeError, KeyError):
                on_str = "N/A"
                kun_str = "N/A"

            # Parse meanings JSON
            try:
                meanings_dict = json.loads(kanji["meanings"])
                vi_meanings = meanings_dict.get("vi", [])
                en_meanings = meanings_dict.get("en", [])
                meanings_str = (
                    f"VI: {', '.join(vi_meanings[:3])}"
                    + (f" | EN: {', '.join(en_meanings[:3])}" if en_meanings else "")
                )
            except (json.JSONDecodeError, KeyError):
                meanings_str = kanji.get("meanings", "N/A")

            formatted_results.append({
                "character": kanji["character"],
                "on_readings": on_str,
                "kun_readings": kun_str,
                "meanings": meanings_str,
                "vietnamese_reading": kanji.get("vietnamese_reading") or "N/A",
                "jlpt_level": kanji.get("jlpt_level") or "N/A",
                "stroke_count": kanji.get("stroke_count") or "N/A",
                "radical": kanji.get("radical") or "N/A"
            })

        # Create summary text
        count_text = f"Found {len(results)} kanji"
        if search_term:
            count_text += f" matching '{search_term}'"
        if jlpt_level:
            count_text += f" (JLPT {jlpt_level.upper()})"

        result_text = f"{count_text}:\n\n"
        for i, entry in enumerate(formatted_results, 1):
            result_text += (
                f"{i}. {entry['character']}\n"
                f"   On-yomi: {entry['on_readings']}\n"
                f"   Kun-yomi: {entry['kun_readings']}\n"
                f"   Meanings: {entry['meanings']}\n"
                f"   Hán Việt: {entry['vietnamese_reading']}\n"
                f"   Level: {entry['jlpt_level']} | Strokes: {entry['stroke_count']} | Radical: {entry['radical']}\n\n"
            )

        return {
            "status": "success",
            "content": [{"text": result_text.strip()}]
        }

    except Exception as e:
        return {
            "status": "error",
            "content": [{
                "text": f"Error retrieving kanji: {str(e)}"
            }]
        }
