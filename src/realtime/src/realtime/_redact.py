import logging
import re
from dataclasses import replace
from typing import Any

from typing_extensions import override
from websockets.frames import Frame, Opcode

REDACTED = "<redacted>"

_SECRET_PATTERNS = (
    re.compile(r"(apikey=)[^&\s]*"),
    re.compile(r'("access_token"\s*:\s*")[^"]*'),
)


def redact(text: str) -> str:
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub(rf"\g<1>{REDACTED}", text)
    return text


def _redact_argument(argument: object) -> object:
    if isinstance(argument, str):
        return redact(argument)
    if isinstance(argument, Frame) and argument.opcode is Opcode.TEXT:
        try:
            text = bytes(argument.data).decode()
        except UnicodeDecodeError:
            return argument
        return str(replace(argument, data=redact(text).encode()))
    return argument


class RedactingLoggerAdapter(logging.LoggerAdapter[logging.Logger]):
    @override
    def log(
        self,
        level: int,
        msg: object,
        *args: object,
        **kwargs: Any,
    ) -> None:
        if not self.isEnabledFor(level):
            return
        redacted_args = tuple(_redact_argument(argument) for argument in args)
        super().log(level, redact(str(msg)), *redacted_args, **kwargs)
