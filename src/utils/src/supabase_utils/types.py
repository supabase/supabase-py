from typing import Mapping, Sequence, TypeAlias, Union

from pydantic import TypeAdapter
from typing_extensions import TypeAliasType

JSON: TypeAlias = TypeAliasType(
    "JSON", "Union[None, bool, str, int, float, Sequence[JSON], Mapping[str, JSON]]"
)

JSONParser: TypeAdapter[JSON] = TypeAdapter(JSON)
