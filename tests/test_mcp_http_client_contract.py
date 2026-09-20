from __future__ import annotations

import socket
import threading
import time

import pytest
import uvicorn

import biomcp.mcp_client as mcp_client
from biomcp_servers.bioimage import create_http_app


@pytest.fixture
def live_http_server(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("BIOMCP_HTTP_ALLOWED_HOSTS", "127.0.0.1:*")
    monkeypatch.delenv("BIOMCP_HTTP_ALLOWED_ORIGINS", raising=False)
    app = create_http_app()

    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]

    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=port,
        log_level="error",
        lifespan="on",
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not server.started and thread.is_alive() and time.monotonic() < deadline:
        time.sleep(0.01)
    assert server.started, "local MCP HTTP server did not start"

    entry = {
        "name": "fixture-http",
        "status": "validated",
        "external": True,
        "installable": False,
        "transport": ["streamable-http"],
        "endpoint": f"http://127.0.0.1:{port}/mcp",
        "tools": ["inspect_image", "intensity_summary", "threshold_image"],
    }
    monkeypatch.setattr(mcp_client, "get_server", lambda name: entry)
    try:
        yield entry
    finally:
        server.should_exit = True
        thread.join(timeout=5)


def test_transport_aware_client_discovers_tools_over_real_http(live_http_server):
    tools = mcp_client.discover_tools("fixture-http", transport="streamable-http")
    assert [tool["name"] for tool in tools] == [
        "inspect_image",
        "intensity_summary",
        "threshold_image",
    ]


def test_registry_default_client_discovers_tools_over_real_http(live_http_server):
    tools = mcp_client.discover_tools("fixture-http")
    assert [tool["name"] for tool in tools] == [
        "inspect_image",
        "intensity_summary",
        "threshold_image",
    ]


def test_transport_aware_client_calls_tool_over_real_http(live_http_server, tmp_path):
    import numpy as np
    import tifffile

    image = tmp_path / "http-contract.tif"
    tifffile.imwrite(image, np.array([[0, 1], [2, 3]], dtype=np.uint8))
    result = mcp_client.call_tool(
        "fixture-http",
        "inspect_image",
        {"path": str(image)},
        transport="streamable-http",
    )
    assert result["is_error"] is False
    assert result["provenance"] == {
        "server": "fixture-http",
        "tool": "inspect_image",
        "transport": "streamable-http",
        "registry_status": "validated",
    }
    assert result["structured_content"]["shape"] == [2, 2]
    assert result["structured_content"]["dtype"] == "uint8"
    assert result["structured_content"]["ndim"] == 2


def test_registry_default_client_calls_tool_over_real_http(live_http_server, tmp_path):
    import numpy as np
    import tifffile

    image = tmp_path / "http-default-contract.tif"
    tifffile.imwrite(image, np.array([[0, 1], [2, 3]], dtype=np.uint8))
    result = mcp_client.call_tool(
        "fixture-http",
        "inspect_image",
        {"path": str(image)},
    )
    assert result["is_error"] is False
    assert result["provenance"]["server"] == "fixture-http"
    assert result["provenance"]["tool"] == "inspect_image"
    assert result["provenance"]["transport"] == "streamable-http"
    assert result["provenance"]["registry_status"] == "validated"
    assert result["structured_content"]["shape"] == [2, 2]
    assert result["structured_content"]["dtype"] == "uint8"
    assert result["structured_content"]["ndim"] == 2
