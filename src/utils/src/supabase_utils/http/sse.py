import re
from dataclasses import dataclass

_LINE_END = re.compile(r"\r\n|\r|\n")


@dataclass(frozen=True)
class ServerSentEvent:
    """One event of a `text/event-stream` response."""

    event: str = "message"
    """The type of the event, `message` when the event did not name one."""

    data: str = ""
    """The data of the event, its `data` lines joined with newlines."""

    id: str | None = None
    """The last event ID the stream set, with this event or an earlier one, or
    None when it set none."""

    retry: float | None = None
    """The seconds the stream last asked a client to wait before reconnecting,
    or None when it did not ask."""


class ServerSentEventDecoder:
    """Turns the text of a `text/event-stream` response into events, as the
    HTML standard parses an event stream.

    Feed it the text as it arrives, in pieces of any size. An event is
    returned once the blank line that ends it arrived, and an event the
    stream did not end is dropped.
    """

    def __init__(self) -> None:
        self._pending: list[str] = []
        self._skip_line_feed = False
        self._event = ""
        self._data: list[str] = []
        self._id: str | None = None
        self._retry: float | None = None

    def feed(self, text: str) -> list[ServerSentEvent]:
        """The events that `text` completes."""
        if self._skip_line_feed and text.startswith("\n"):
            text = text[1:]
        self._skip_line_feed = False
        events: list[ServerSentEvent] = []
        start = 0
        for line_end in _LINE_END.finditer(text):
            self._pending.append(text[start : line_end.start()])
            line = "".join(self._pending)
            self._pending = []
            event = self._process_line(line)
            if event is not None:
                events.append(event)
            start = line_end.end()
            self._skip_line_feed = line_end.group() == "\r" and start == len(text)
        if start < len(text):
            self._pending.append(text[start:])
        return events

    def _process_line(self, line: str) -> ServerSentEvent | None:
        if not line:
            return self._dispatch()
        if line.startswith(":"):
            return None
        name, _, value = line.partition(":")
        value = value.removeprefix(" ")
        if name == "event":
            self._event = value
        elif name == "data":
            self._data.append(value)
        elif name == "id":
            if "\0" not in value:
                self._id = value
        elif name == "retry" and value.isascii() and value.isdigit():
            self._retry = int(value) / 1000
        return None

    def _dispatch(self) -> ServerSentEvent | None:
        data = self._data
        event = self._event
        self._data = []
        self._event = ""
        if not data:
            return None
        return ServerSentEvent(
            event=event or "message",
            data="\n".join(data),
            id=self._id,
            retry=self._retry,
        )
