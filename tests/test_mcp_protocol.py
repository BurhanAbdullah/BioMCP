
def test_imagej_stdio_protocol_calls_status_tool():
    result = asyncio.run(
        _call_tool("biomcp_servers.imagej", "imagej_status", {})
    )
    assert result == {"configured": False, "executable": None}


def test_llm_stdio_protocol_exposes_tools():
    names = asyncio.run(_list_tools("biomcp_servers.llm"))
    assert names == ["list_models", "complete", "chat", "chat_with_tools", "provider_capabilities", "mcp_capabilities", "mcp_call_tool"]


def test_llm_stdio_protocol_exposes_provider_capabilities_without_credentials(monkeypatch):
    monkeypatch.setenv("BIOMCP_LLM_BASE_URL", "http://127.0.0.1:11434/v1")
    monkeypatch.setenv("BIOMCP_LLM_API_KEY", "test-key")
    result = asyncio.run(
        _call_tool(
            "biomcp_servers.llm",