import inspect

from biomcp_servers import llm as llm_server


def test_chat_with_tools_entrypoint_validates_context():
    source = inspect.getsource(llm_server.create_server)
    marker = "def chat_with_tools("
    assert marker in source
    tool_loop = source[source.index(marker):]
    assert "messages = validate_context(" in tool_loop
    assert "limits," in tool_loop


def test_chat_with_tools_entrypoint_keeps_validation_before_broker_creation():
    source = inspect.getsource(llm_server.create_server)
    tool_loop = source[source.index("def chat_with_tools("):]
    assert tool_loop.index("messages = validate_context(") < tool_loop.index("broker = MCPToolBroker(")
