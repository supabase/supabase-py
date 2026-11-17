import logging
import re
from typing import Any, override

from websockets.frames import Frame

from .message import Message

REDACTED = "<redacted>"

_SECRET_PATTERNS = (
    re.compile(r"(\bapikey=)[^&\s]*", re.IGNORECASE),
    re.compile(r"""(\baccess_token\b["']?\s*[:=]\s*["'])[^"']*"""),
)


_HEADER_FORMATS = frozenset({"> %s: %s", "< %s: %s"})
_REQUEST_LINE_FORMAT = "> GET %s HTTP/1.1"


def _redact_handshake(msg: object, args: tuple[object, ...]) -> tuple[object, ...]:
    """Drop the header values and the query string from the handshake that
    websockets logs."""
    if msg in _HEADER_FORMATS and len(args) == 2:
        return (args[0], REDACTED)
    if msg == _REQUEST_LINE_FORMAT and len(args) == 1 and isinstance(args[0], str):
        return (args[0].partition("?")[0],)
    return args


def describe(message: Message) -> str:
    """The event, topic and ref of `message`, without its payload."""
    return f"{message.event} on {message.topic} (ref={message.ref})"


def redact(text: str) -> str:
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub(rf"\g<1>{REDACTED}", text)
    return text


def _redact_argument(argument: object) -> object:
    if isinstance(argument, str):
        return redact(argument)
    if isinstance(argument, Frame):
        return f"{argument.opcode.name} frame of {len(argument.data)} bytes"
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
        kwargs["stacklevel"] = kwargs.get("stacklevel", 1) + 1
        redacted_args = tuple(
            _redact_argument(argument) for argument in _redact_handshake(msg, args)
        )
        try:
            message = logging.LogRecord(
                self.logger.name, level, "", 0, msg, redacted_args, None
            ).getMessage()
        except (TypeError, ValueError, KeyError):
            super().log(level, redact(str(msg)), *redacted_args, **kwargs)
            return
        super().log(level, redact(message), **kwargs)
