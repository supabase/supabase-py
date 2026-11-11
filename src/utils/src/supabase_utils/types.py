from collections.abc import Mapping, Sequence
from typing import Literal

from pydantic import TypeAdapter

HTTPRequestMethod = Literal["GET", "POST", "PATCH", "PUT", "DELETE", "HEAD"]

JSONSimple = None | bool | str | int | float
type JSON = JSONSimple | Sequence[JSON] | Mapping[str, JSON]

JSONParser: TypeAdapter[JSON] = TypeAdapter(JSON)
