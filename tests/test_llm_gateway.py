import pytest

from biomcp.llm import OpenAICompatibleProvider, ProviderConfig, ProviderCapabilities, builtin_providers


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
    provider = OpenAICompatibleProvider(ProviderConfig(
        "test", "http://127.0.0.1:9000/v1",
        capabilities=ProviderCapabilities(streaming=True, structured_output=True, tool_calling=True),
    ))
    payload = provider.build_request(
        model="local-model",
        input=[{"role": "user", "content": "measure nuclei"}],
        stream=True,
        response_format={"type": "json_schema", "json_schema": {"name": "result"}},
        tools=[{"type": "function", "function": {"name": "inspect_image"}}],
        temperature=0.2,
        max_output_tokens=256,
    )
    assert payload["model"] == "local-model"
    assert payload["stream"] is True
    assert payload["response_format"]["type"] == "json_schema"
    assert payload["tools"][0]["function"]["name"] == "inspect_image"
    assert payload["temperature"] == 0.2
    assert payload["max_output_tokens"] == 256


def test_capability_boundaries_are_enforced():
    provider = OpenAICompatibleProvider(ProviderConfig(
        "ollama", "http://127.0.0.1:11434/v1", capabilities=ProviderCapabilities(streaming=True)
    ))
    with pytest.raises(RuntimeError, match="structured_output"):
        provider.build_request(model="m", input="x", response_format={"type": "json_schema"})
    with pytest.raises(RuntimeError, match="tool_calling"):
        provider.build_request(model="m", input="x", tools=[{"type": "function"}])
    with pytest.raises(RuntimeError, match="structured_output"):
        provider.chat(model="m", messages=[], response_format={"type": "json_schema"})
    with pytest.raises(RuntimeError, match="tool_calling"):
        provider.chat(model="m", messages=[], tools=[{"type": "function"}])


def test_chat_request_is_openai_compatible(monkeypatch):
    provider = OpenAICompatibleProvider(ProviderConfig(
        "test", "http://127.0.0.1:9000/v1",
        capabilities=ProviderCapabilities(structured_output=True, tool_calling=True),
    ))
    seen = {}

    def fake_request(path, payload=None, **kwargs):
        seen["path"] = path
        seen["payload"] = payload
        seen["kwargs"] = kwargs
        return {
            "id": "chat-1",
            "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
        }

    monkeypatch.setattr(provider, "request", fake_request)
    result = provider.chat(
        model="m",
        messages=[{"role": "user", "content": "hello"}],
        temperature=0.1,
        max_tokens=32,
        response_format={"type": "json_schema", "json_schema": {"name": "answer"}},
        tools=[{"type": "function", "function": {"name": "inspect_image"}}],
        retries=2,
    )
    assert result["id"] == "chat-1"
    assert result["_biomcp"]["usage"] == {"input_tokens": 3, "output_tokens": 2, "total_tokens": 5}
    assert seen["path"] == "chat/completions"
    assert seen["payload"]["messages"][0]["content"] == "hello"
    assert seen["kwargs"]["retries"] == 2
    assert seen["payload"]["max_tokens"] == 32
    assert seen["payload"]["response_format"]["type"] == "json_schema"
    assert seen["payload"]["tools"][0]["function"]["name"] == "inspect_image"


def test_complete_normalizes_responses_usage(monkeypatch):
    provider = OpenAICompatibleProvider(ProviderConfig("test", "http://127.0.0.1:9000/v1"))

    def fake_request(path, payload=None, **kwargs):
        assert path == "responses"
        assert kwargs["retries"] == 0
        return {"id": "resp-1", "usage": {"input_tokens": 11, "output_tokens": 6, "total_tokens": 17}}

    monkeypatch.setattr(provider, "request", fake_request)
    result = provider.complete(model="m", input="hello", retries=0)
    assert result["id"] == "resp-1"
    assert result["_biomcp"]["usage"] == {"input_tokens": 11, "output_tokens": 6, "total_tokens": 17}


def test_usage_metadata_normalizes_chat_and_responses_field_names():
    chat = {
        "usage": {
            "prompt_tokens": 12,
            "completion_tokens": 7,
            "total_tokens": 19,
            "prompt_tokens_details": {"cached_tokens": 4},
        }
    }
    responses = {"usage": {"input_tokens": 20, "output_tokens": 9, "total_tokens": 29}}
    assert OpenAICompatibleProvider.normalize_usage(chat).as_dict() == {
        "input_tokens": 12,
        "output_tokens": 7,
        "total_tokens": 19,
        "cached_input_tokens": 4,
    }
    assert OpenAICompatibleProvider.normalize_usage(responses).as_dict() == {
        "input_tokens": 20,
        "output_tokens": 9,
        "total_tokens": 29,
    }


def test_normalized_response_preserves_provider_payload_and_adds_biomcp_metadata():
    response = {"id": "chat-1", "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5}}
    normalized = OpenAICompatibleProvider.normalize_response(response)
    assert normalized["id"] == "chat-1"
    assert normalized["usage"] == response["usage"]
    assert normalized["_biomcp"]["usage"] == {"input_tokens": 3, "output_tokens": 2, "total_tokens": 5}
    assert "_biomcp" not in response


def test_invalid_usage_metadata_is_rejected():
    with pytest.raises(ValueError, match="invalid token usage"):
        OpenAICompatibleProvider.normalize_usage({"usage": {"prompt_tokens": -1}})


def test_stream_normalizes_final_usage_event():
    event = {
        "id": "chatcmpl-1",
        "usage": {"prompt_tokens": 8, "completion_tokens": 4, "total_tokens": 12},
    }
    normalized = OpenAICompatibleProvider.normalize_stream_event(event)
    assert normalized["usage"] == event["usage"]
    assert normalized["_biomcp"]["usage"] == {
        "input_tokens": 8,
        "output_tokens": 4,
        "total_tokens": 12,
    }
    assert "_biomcp" not in event


class _FakeResponse:
    def __init__(self, lines):
        self._lines = [line.encode("utf-8") for line in lines]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def __iter__(self):
        return iter(self._lines)


class _FakeOpener:
    def __init__(self, response):
        self.response = response

    def open(self, request, timeout):
        self.request = request
        self.timeout = timeout
        return self.response


def test_stream_parses_sse_and_enforces_protocol():
    provider = OpenAICompatibleProvider(
        ProviderConfig("test", "http://127.0.0.1:9000/v1", capabilities=ProviderCapabilities(streaming=True)),
        max_response_bytes=1024,
    )
    provider._opener = _FakeOpener(_FakeResponse([
        ": keepalive\n",
        "data: {\"delta\":\"A\"}\n",
        "data: {\"delta\":\"B\"}\n",
        "data: [DONE]\n",
    ]))
    events = list(provider.stream("responses", {"model": "m", "input": "hello"}, retries=0))
    assert events == [{"delta": "A"}, {"delta": "B"}]
    assert provider._opener.timeout == 120


def test_stream_includes_normalized_usage_on_usage_event():
    provider = OpenAICompatibleProvider(
        ProviderConfig("test", "http://127.0.0.1:9000/v1", capabilities=ProviderCapabilities(streaming=True)),
        max_response_bytes=1024,
    )
    provider._opener = _FakeOpener(_FakeResponse([
        "data: {\"delta\":\"A\"}\n",
        "data: {\"usage\":{\"prompt_tokens\":5,\"completion_tokens\":2,\"total_tokens\":7}}\n",
        "data: [DONE]\n",
    ]))
    events = list(provider.stream("chat/completions", {"model": "m", "messages": []}, retries=0))
    assert events[0] == {"delta": "A"}
    assert events[1]["usage"] == {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7}
    assert events[1]["_biomcp"]["usage"] == {"input_tokens": 5, "output_tokens": 2, "total_tokens": 7}


def test_response_size_limit_applies_to_streams():
    provider = OpenAICompatibleProvider(
        ProviderConfig("test", "http://127.0.0.1:9000/v1", capabilities=ProviderCapabilities(streaming=True)),
        max_response_bytes=20,
    )
    provider._opener = _FakeOpener(_FakeResponse(["data: {\"large\":\"payload\"}\n"]))
    with pytest.raises(RuntimeError, match="stream exceeds"):
        list(provider.stream("responses", {"model": "m", "input": "x"}, retries=0))


def test_provider_rejects_non_http_endpoints():
    with pytest.raises(ValueError, match="HTTP\(S\)"):
        OpenAICompatibleProvider(ProviderConfig("bad", "file:///tmp/model"))


def test_provider_environment_supports_local_runtime(monkeypatch):
    monkeypatch.setenv("BIOMCP_LLM_BASE_URL", "http://127.0.0.1:11434/v1")
    monkeypatch.setenv("BIOMCP_LLM_MODEL", "local-model")
    provider = OpenAICompatibleProvider.from_environment("ollama")
    assert provider.config.name == "ollama"
    assert provider.config.base_url == "http://127.0.0.1:11434/v1"
    assert provider._api_key is None


def test_provider_environment_rejects_embedded_credentials(monkeypatch):
    monkeypatch.setenv("BIOMCP_LLM_BASE_URL", "https://user:secret@example.com/v1")
    with pytest.raises(ValueError, match="without embedded credentials"):
        OpenAICompatibleProvider.from_environment()


def test_provider_environment_configures_bounded_retries(monkeypatch):
    monkeypatch.setenv("BIOMCP_LLM_MAX_RETRIES", "3")
    provider = OpenAICompatibleProvider.from_environment()
    assert provider.max_retries == 3


def test_provider_rejects_invalid_retry_configuration(monkeypatch):
    monkeypatch.setenv("BIOMCP_LLM_MAX_RETRIES", "4")
    with pytest.raises(ValueError, match="max_retries must be 0..3"):
        OpenAICompatibleProvider.from_environment()


def test_per_call_retry_override_is_bounded():
    provider = OpenAICompatibleProvider(ProviderConfig("test", "http://127.0.0.1:9000/v1"), max_retries=3)
    with pytest.raises(ValueError, match="retries must be 0..3"):
        provider.request("models", retries=4)
