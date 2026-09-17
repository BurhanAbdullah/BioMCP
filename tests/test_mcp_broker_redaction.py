import json
import os
import sys

from biomcp.mcp_broker import MCPBrokerConfig, MCPToolBroker


SECRET = "super-secret-token-123456789"
SERVER_CODE = """
import os
from mcp.server.mcpserver import MCPServer
mcp = MCPServer('redaction-fixture')
@mcp.tool()
def leak() -> dict:
    secret = os.environ['BIO_TEST_SECRET']
    return {'message': f'credential={secret}', 'nested': {'value': secret}}
mcp.run()
"""


def test_downstream_child_credentials_are_redacted_from_results():
    config = MCPBrokerConfig(
        command=(sys.executable, "-c", SERVER_CODE),
        allowed_executables=frozenset({os.path.realpath(sys.executable)}),
        allowed_tools=frozenset({"leak"}),
        timeout_seconds=10,
        max_result_bytes=1024 * 1024,
        child_env=(("BIO_TEST_SECRET", SECRET),),
    )
    result = MCPToolBroker(config).call_tool("leak", {})
    encoded = json.dumps(result)
    assert SECRET not in encoded
    assert "[REDACTED]" in encoded
    assert "credential=[REDACTED]" in encoded
