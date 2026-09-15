from __future__ import annotations

import asyncio
from typing import Any

import pytest

from biomcp.http import ConcurrencyLimitMiddleware, create_streamable_http_app


async def _send_collector(messages: list[dict[str, Any]], message: dict[str, Any]) -> None:
    messages.append(message)


async def _empty_receive() -> dict[str, Any]:
    return {"type": "http.request", "body": b"", "more_body": False}


def test_concurrency_limit_rejects_saturated_request() -> None:
    async def scenario() -> None:
        started = asyncio.Event()
        release = asyncio.Event()
        calls = 0

        async def app(scope: dict[str, Any], receive: Any, send: Any) -> None:
            nonlocal calls
            calls += 1
            started.set()
            await release.wait()

        middleware = ConcurrencyLimitMiddleware(app, 1)
        first_send: list[dict[str, Any]] = []
        second_send: list[dict[str, Any]] = []

        first = asyncio.create_task(
            middleware(
                {"type": "http"},
                _empty_receive,
                lambda m: _send_collector(first_send, m),
            )
        )
        await started.wait()

        await middleware(
            {"type": "http"},
            _empty_receive,
            lambda m: _send_collector(second_send, m),
        )

        assert calls == 1
        assert second_send[0]["status"] == 503
        assert (b"retry-after", b"1") in second_send[0]["headers"]
        assert second_send[1]["body"].startswith(
            b"BioMCP HTTP concurrency limit reached"
        )

        release.set()
        await first

    asyncio.run(scenario())


def test_concurrency_limit_releases_after_application_error() -> None:
    async def scenario() -> None:
        calls = 0

        async def app(scope: dict[str, Any], receive: Any, send: Any) -> None:
            nonlocal calls
            calls += 1
            raise RuntimeError("boom")

        middleware = ConcurrencyLimitMiddleware(app, 1)

        with pytest.raises(RuntimeError, match="boom"):
            await middleware(
                {"type": "http"}, _empty_receive, lambda _: _send_collector([], _)
            )

        with pytest.raises(RuntimeError, match="boom"):
            await middleware(
                {"type": "http"}, _empty_receive, lambda _: _send_collector([], _)
            )

        assert calls == 2

    asyncio.run(scenario())


def test_non_http_scopes_are_not_limited() -> None:
    async def scenario() -> None:
        calls = 0

        async def app(scope: dict[str, Any], receive: Any, send: Any) -> None:
            nonlocal calls
            calls += 1

        middleware = ConcurrencyLimitMiddleware(app, 1)
        await middleware(
            {"type": "lifespan"}, _empty_receive, lambda _: _send_collector([], _)
        )

        assert calls == 1

    asyncio.run(scenario())


def test_http_factory_reads_optional_concurrency_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BIOMCP_HTTP_MAX_CONCURRENCY", "4")

    class FakeServer:
        def streamable_http_app(self, **_: Any) -> Any:
            return lambda scope, receive, send: None

    app = create_streamable_http_app(FakeServer(), allowed_hosts=["mcp.example.org"])

    assert isinstance(app, ConcurrencyLimitMiddleware)
    assert app.max_concurrent_requests == 4


def test_http_factory_rejects_invalid_concurrency_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BIOMCP_HTTP_MAX_CONCURRENCY", "0")

    class FakeServer:
        def streamable_http_app(self, **_: Any) -> Any:
            return lambda scope, receive, send: None

    with pytest.raises(ValueError, match="positive integer"):
        create_streamable_http_app(FakeServer(), allowed_hosts=["mcp.example.org"])
