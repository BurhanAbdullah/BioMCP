from biomcp_servers.llm import _mcp_discovery_payload


class _FakeBroker:
    def server_metadata(self):
        return {
            "protocol_version": "2026-07-28",
            "capabilities": {"tools": {}},
            "server_info": {"name": "scientific-server", "version": "1.2.3"},
            "instructions": "Use the scientific tools carefully.",
        }

    def list_tools(self):
        return [{"name": "search_gene", "inputSchema": {"type": "object"}}]


def test_mcp_discovery_payload_preserves_negotiated_metadata_and_tools():
    payload = _mcp_discovery_payload(_FakeBroker())
    assert payload["server"]["protocol_version"] == "2026-07-28"
    assert payload["server"]["server_info"]["name"] == "scientific-server"
    assert payload["server"]["instructions"] == "Use the scientific tools carefully."
    assert payload["tools"] == [{"name": "search_gene", "inputSchema": {"type": "object"}}]
