import pytest

import biomcp.mcp_client as mcp_client


def test_stdio_client_rejects_server_without_stdio_transport(monkeypatch):
    monkeypatch.setattr(
        mcp_client,
        "get_server",
        lambda name: {"name": name, "installable": True, "transport": ["streamable-http"]},
    )

    with pytest.raises(ValueError, match="does not declare stdio transport support"):
        mcp_client._server_parameters("http-only")
