from typing import Mapping, Sequence, TypeAlias, Union

from pydantic import TypeAdapter

JSON: TypeAlias = Union[
    None, bool, str, int, float, Sequence["JSON"], Mapping[str, "JSON"]
]

JSONParser: TypeAdapter[JSON] = TypeAdapter(JSON)
