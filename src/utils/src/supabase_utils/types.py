from typing import Mapping, Sequence

from pydantic import TypeAdapter
from typing_extensions import TypeAliasType

JSONSimple = None | bool | str | int | float
JSON = TypeAliasType("JSON", "JSONSimple | Sequence[JSON] | Mapping[str, JSON]")

JSONParser: TypeAdapter[JSON] = TypeAdapter(JSON)
