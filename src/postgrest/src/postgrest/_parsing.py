import json
from typing import cast

from supabase_utils.types import JSON


class InvalidResponseBodyError(ValueError):
    """The response body is not JSON, or not in the shape the query asked for."""


def parse_json(content: bytes) -> JSON:
    try:
        data: JSON = json.loads(content)
    except (ValueError, RecursionError) as error:
        raise InvalidResponseBodyError("The response body is not valid JSON") from error
    return data


def parse_rows(content: bytes) -> list[dict[str, JSON]]:
    data = parse_json(content)
    if isinstance(data, list) and all(isinstance(row, dict) for row in data):
        return cast("list[dict[str, JSON]]", data)
    raise InvalidResponseBodyError("Expected a JSON array of objects")


def parse_object(content: bytes) -> dict[str, JSON]:
    data = parse_json(content)
    if isinstance(data, dict):
        return data
    raise InvalidResponseBodyError("Expected a JSON object")
