import pytest
from supabase_utils.http.sse import ServerSentEvent, ServerSentEventDecoder


def decode(*pieces: str) -> list[ServerSentEvent]:
    decoder = ServerSentEventDecoder()
    return [event for piece in pieces for event in decoder.feed(piece)]


def test_decoder_parses_events() -> None:
    assert decode("data: hello\n\nevent: update\ndata: a\ndata: b\nid: 7\n\n") == [
        ServerSentEvent(data="hello"),
        ServerSentEvent(event="update", data="a\nb", id="7"),
    ]


def test_decoder_handles_every_line_ending() -> None:
    assert decode("data: a\r\n\r\ndata: b\r\rdata: c\n\n") == [
        ServerSentEvent(data="a"),
        ServerSentEvent(data="b"),
        ServerSentEvent(data="c"),
    ]


@pytest.mark.parametrize(
    "pieces",
    [
        ["data: a\r", "\n\r\n"],
        ["da", "ta: a", "\r\n", "\r", "\n"],
        ["data: a\r\n\r", "\n"],
    ],
)
def test_decoder_joins_lines_split_across_pieces(pieces: list[str]) -> None:
    assert decode(*pieces) == [ServerSentEvent(data="a")]


def test_decoder_keeps_the_last_event_id_and_retry() -> None:
    assert decode("id: 1\nretry: 1500\ndata: a\n\ndata: b\n\nid\ndata: c\n\n") == [
        ServerSentEvent(data="a", id="1", retry=1.5),
        ServerSentEvent(data="b", id="1", retry=1.5),
        ServerSentEvent(data="c", id="", retry=1.5),
    ]


def test_decoder_ignores_invalid_fields() -> None:
    assert decode(
        ": a comment\nid: a\0b\nretry: soon\nunknown: x\ndata\ndata:  two spaces\n\n"
    ) == [ServerSentEvent(data="\n two spaces")]


def test_decoder_dispatches_no_event_without_data() -> None:
    assert decode("event: ping\n\ndata: a\n\n") == [ServerSentEvent(data="a")]


def test_decoder_drops_an_event_the_stream_did_not_end() -> None:
    assert decode("data: a\n\ndata: b\n") == [ServerSentEvent(data="a")]


def test_decoder_joins_a_line_split_across_many_pieces() -> None:
    pieces = ["data: ", *["x"] * 1000, "\n", "\n"]
    assert decode(*pieces) == [ServerSentEvent(data="x" * 1000)]
