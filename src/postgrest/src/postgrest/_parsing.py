import json
from typing import cast

from supabase_utils.types import JSON


class UnexpectedResponseShapeError(ValueError):
    """The response body is valid JSON, but not in the shape the query asked for."""


def parse_json(content: bytes) -> JSON:
    data: JSON = json.loads(content)
    return data


def parse_rows(content: bytes) -> list[dict[str, JSON]]:
    data = parse_json(content)
    if isinstance(data, list) and all(isinstance(row, dict) for row in data):
        return cast("list[dict[str, JSON]]", data)
    raise UnexpectedResponseShapeError("Expected a JSON array of objects")


def parse_object(content: bytes) -> dict[str, JSON]:
    data = parse_json(content)
    if isinstance(data, dict):
        return data
    raise UnexpectedResponseShapeError("Expected a JSON object")
