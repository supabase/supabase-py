from collections.abc import Mapping, Sequence

from pydantic import TypeAdapter

JSONSimple = None | bool | str | int | float
type JSON = JSONSimple | Sequence[JSON] | Mapping[str, JSON]

JSONParser: TypeAdapter[JSON] = TypeAdapter(JSON)
