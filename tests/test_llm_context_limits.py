import os

import pytest

from biomcp.llm_limits import LLMContextLimits, limits_from_environment, validate_context


def test_context_limits_accept_normal_conversation():
    limits = LLMContextLimits(max_messages=2, max_context_bytes=1024)
    messages = [{"role": "system", "content": "scientific"}, {"role": "user", "content": "hello"}]
    result = validate_context(messages, limits)
    assert result == messages
    assert result is not messages


def test_context_limits_reject_message_count():
    limits = LLMContextLimits(max_messages=1, max_context_bytes=1024)
    with pytest.raises(ValueError, match="message limit"):
        validate_context([{"role": "user", "content": "a"}, {"role": "user", "content": "b"}], limits)


def test_context_limits_reject_serialized_size():
    limits = LLMContextLimits(max_messages=4, max_context_bytes=1024)
    with pytest.raises(ValueError, match="context size"):
        validate_context([{"role": "user", "content": "x" * 1100}], limits)


def test_context_limits_reject_non_object_messages():
    limits = LLMContextLimits(max_messages=4, max_context_bytes=1024)
    with pytest.raises(ValueError, match="messages must be objects"):
        validate_context(["not-a-message"], limits)  # type: ignore[list-item]


def test_context_limits_reject_non_serializable_content():
    limits = LLMContextLimits(max_messages=4, max_context_bytes=4096)
    with pytest.raises(ValueError, match="non-serializable"):
        validate_context([{"role": "user", "content": object()}], limits)


def test_context_limits_environment_is_bounded(monkeypatch):
    monkeypatch.setenv("BIOMCP_LLM_MAX_CONTEXT_MESSAGES", "12")
    monkeypatch.setenv("BIOMCP_LLM_MAX_CONTEXT_BYTES", "4096")
    limits = limits_from_environment(os.environ)
    assert limits == LLMContextLimits(max_messages=12, max_context_bytes=4096)


def test_context_limits_environment_rejects_invalid_values(monkeypatch):
    monkeypatch.setenv("BIOMCP_LLM_MAX_CONTEXT_MESSAGES", "zero")
    with pytest.raises(ValueError, match="must be integers"):
        limits_from_environment(os.environ)


def test_context_limits_configuration_bounds():
    with pytest.raises(ValueError, match="max_messages"):
        LLMContextLimits(max_messages=0)
    with pytest.raises(ValueError, match="max_context_bytes"):
        LLMContextLimits(max_context_bytes=1023)
