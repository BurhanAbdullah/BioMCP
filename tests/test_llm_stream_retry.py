import json
import urllib.error

import pytest

from biomcp.llm import OpenAICompatibleProvider, ProviderCapabilities, ProviderConfig


class _Response:
    def __init__(self, lines, error=None):
        self.lines = [line.encode("utf-8") for line in lines]
        self.error = error

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def __iter__(self):
        for line in self.lines:
            yield line
        if self.error:
            raise self.error


class _Opener:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = 0

    def open(self, request, timeout):
        self.calls += 1
        return next(self.responses)


def _provider(opener, retries=2):
    provider = OpenAICompatibleProvider(
        ProviderConfig(
            "test",
            "http://127.0.0.1:9000/v1",
            capabilities=ProviderCapabilities(streaming=True),
        ),
        max_retries=retries,
    )
    provider._opener = opener
    return provider


def test_stream_retries_before_first_event():
    opener = _Opener([
        _Response([], urllib.error.URLError("temporary")),
        _Response(['data: {"delta":"A"}\n', "data: [DONE]\n"]),
    ])
    events = list(_provider(opener).stream("responses", {"model": "m", "input": "x"}))
    assert events == [{"delta": "A"}]
    assert opener.calls == 2


def test_stream_does_not_retry_after_event_was_delivered():
    opener = _Opener([
        _Response(['data: {"delta":"A"}\n'], urllib.error.URLError("connection lost")),
        _Response(['data: {"delta":"A"}\n', "data: [DONE]\n"]),
    ])
    with pytest.raises(RuntimeError, match="endpoint unavailable"):
        list(_provider(opener).stream("responses", {"model": "m", "input": "x"}))
    assert opener.calls == 1


def test_stream_keeps_provider_event_unchanged_except_normalized_usage():
    opener = _Opener([
        _Response([
            "data: " + json.dumps({"delta": "A"}) + "\n",
            "data: [DONE]\n",
        ])
    ])
    assert list(_provider(opener, retries=0).stream("responses", {"model": "m", "input": "x"})) == [{"delta": "A"}]
