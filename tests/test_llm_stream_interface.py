import pytest

from biomcp.llm import OpenAICompatibleProvider, ProviderCapabilities, ProviderConfig


class _Response:
    def __init__(self, lines):
        self._lines = [line.encode("utf-8") for line in lines]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def __iter__(self):
        return iter(self._lines)


class _Opener:
    def __init__(self, response):
        self.response = response
        self.request = None
        self.timeout = None

    def open(self, request, timeout):
        self.request = request
        self.timeout = timeout
        return self.response


def _provider(opener, *, streaming=True):
    provider = OpenAICompatibleProvider(
        ProviderConfig(
            "test",
            "http://127.0.0.1:9000/v1",
            capabilities=ProviderCapabilities(streaming=streaming),
        ),
        timeout_seconds=17,
    )
    provider._opener = opener
    return provider


def test_chat_stream_uses_stream_transport_and_yields_events():
    opener = _Opener(
        _Response([
            "data: {\"delta\":\"A\"}\n",
            "data: {\"delta\":\"B\"}\n",
            "data: [DONE]\n",
        ])
    )
    provider = _provider(opener)

    events = list(provider.chat(model="m", messages=[{"role": "user", "content": "hi"}], stream=True))

    assert events == [{"delta": "A"}, {"delta": "B"}]
    assert opener.request.full_url == "http://127.0.0.1:9000/v1/chat/completions"
    assert opener.request.get_header("Accept") == "text/event-stream"
    assert opener.request.get_header("Content-type") == "application/json"
    assert opener.timeout == 17


def test_complete_stream_requires_streaming_capability():
    provider = _provider(_Opener(_Response([])), streaming=False)

    with pytest.raises(RuntimeError, match="streaming"):
        provider.complete(model="m", input="hi", stream=True)


def test_stream_rejects_malformed_json_event():
    provider = _provider(_Opener(_Response(["data: {not-json}\n"])))

    with pytest.raises(RuntimeError, match="invalid JSON"):
        list(provider.stream("responses", {"model": "m", "input": "hi"}, retries=0))
