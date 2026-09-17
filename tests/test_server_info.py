import pytest

from biomcp.server_info import discover_server_metadata


def test_metadata_rejects_non_installable_server_before_launch():
    with pytest.raises(ValueError, match="not installable"):
        discover_server_metadata("bionuclei")


def test_metadata_performs_real_mcp_stdio_handshake():
    metadata = discover_server_metadata("llm")
    assert isinstance(metadata["protocol_version"], str)
    assert isinstance(metadata["server_info"], dict)
    assert isinstance(metadata["capabilities"], dict)
