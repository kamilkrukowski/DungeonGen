import json
import re
from typing import Any


def _load_json(text: str) -> dict[str, Any]:
    """
    Robust JSON loading that handles various LLM response formats.

    Args:
        text: Text that may contain JSON

    Returns:
        Parsed JSON dictionary

    Raises:
        json.JSONDecodeError: If JSON cannot be parsed
    """
    # First, try direct JSON parsing
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Try to extract JSON from markdown code blocks
    json_block_pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
    match = re.search(json_block_pattern, text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try to extract JSON from backticks
    backtick_pattern = r"`(\{.*?\})`"
    match = re.search(backtick_pattern, text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try to find JSON object in the text
    json_pattern = r"\{.*\}"
    match = re.search(json_pattern, text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0).strip())
        except json.JSONDecodeError:
            pass

    # Final fallback: use json-repair
    try:
        from json_repair import repair_json

        repaired_json = repair_json(text)
        return json.loads(repaired_json)
    except (ImportError, json.JSONDecodeError) as err:
        raise json.JSONDecodeError(
            f"Could not parse JSON from text: {text[:200]}..."
        ) from err
