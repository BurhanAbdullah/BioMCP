from biomcp.llm import OpenAICompatibleProvider, ProviderConfig, builtin_providers


def test_builtin_provider_profiles_do_not_store_credentials():
    providers = builtin_providers()
    assert set(providers) == {"openai-compatible", "ollama", "vllm"}
    assert providers["ollama"].api_key_env is None
    assert "API_KEY" in (providers["openai-compatible"].api_key_env or "")


def test_provider_capabilities_are_explicit():
    caps = builtin_providers()["openai-compatible"].capabilities
    assert caps.model_discovery
    assert caps.chat
    assert caps.responses
    assert caps.streaming
    assert caps.structured_output
    assert caps.tool_calling


def test_request_builder_preserves_structured_and_tool_controls():
    provider = OpenAICompatibleProvider(ProviderConfig("test", "http://127.0.0.1:9000/v1"))
    payload = provider.build_request(
        model="local-model",
        input=[{"role": "user", "content": "measure nuclei"}],
        stream=True,
        response_format={"type": "json_schema", "json_schema": {"name": "result"}},
        tools=[{"type": "function", "function": {"name": "inspect_image"}}],
    )
    assert payload["model"] == "local-model"
    assert payload["stream"] is True
    assert payload["response_format"]["type"] == "json_schema"
    assert payload["tools"][0]["function"]["name"] == "inspect_image"


def test_provider_rejects_non_http_endpoints():
    try:
        OpenAICompatibleProvider(ProviderConfig("bad", "file:///tmp/model"))
    except ValueError as exc:
        assert "HTTP(S)" in str(exc)
    else:
        raise AssertionError("non-HTTP provider endpoint was accepted")
