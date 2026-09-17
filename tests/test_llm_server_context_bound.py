import pytest

from biomcp.llm_limits import LLMContextLimits
from biomcp_servers.llm import _BoundedProvider


class _Provider:
    def __init__(self):
        self.messages = None

    def chat(self, **kwargs):
        self.messages = kwargs["messages"]
        return {"choices": [{"message": {"content": "ok"}}]}


def test_bounded_provider_revalidates_accumulated_context():
    provider = _Provider()
    bounded = _BoundedProvider(provider, LLMContextLimits(max_messages=2, max_context_bytes=1024))

    bounded.chat(model="test", messages=[{"role": "user", "content": "one"}])
    assert provider.messages == [{"role": "user", "content": "one"}]

    with pytest.raises(ValueError, match="message limit"):
        bounded.chat(
            model="test",
            messages=[
                {"role": "user", "content": "one"},
                {"role": "tool", "content": "two"},
                {"role": "tool", "content": "three"},
            ],
        )


def test_bounded_provider_enforces_serialized_context_limit():
    provider = _Provider()
    bounded = _BoundedProvider(provider, LLMContextLimits(max_messages=64, max_context_bytes=1024))

    with pytest.raises(ValueError, match="context size limit"):
        bounded.chat(model="test", messages=[{"role": "user", "content": "x" * 1100}])
