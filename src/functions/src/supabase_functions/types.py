from __future__ import annotations

from typing import Any, Literal, Mapping, TypedDict, Union

from .utils import FunctionRegion

HTTPMethod = Literal["GET", "OPTIONS", "HEAD", "POST", "PUT", "PATCH", "DELETE"]
ResponseType = Literal["json", "text/plain", "blob", "arrayBuffer"]


class _BaseFunctionInvokeOptions(TypedDict, total=False):
    headers: Mapping[str, str]
    body: Any
    method: Union[HTTPMethod, str]
    region: Union[FunctionRegion, str]


class FunctionInvokeOptions(_BaseFunctionInvokeOptions, total=False):
    """Options for invoking a Supabase Edge Function."""

    responseType: Union[ResponseType, str]


class FunctionInvokeOptionsJson(_BaseFunctionInvokeOptions, total=False):
    """Options for invoking a Supabase Edge Function with JSON response parsing."""

    responseType: Literal["json"]


class FunctionInvokeOptionsNonJson(_BaseFunctionInvokeOptions, total=False):
    """Options for invoking a Supabase Edge Function with non-JSON (binary) response parsing."""

    responseType: Literal["text/plain", "blob", "arrayBuffer"]
