import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def _list_tools(module: str) -> list[str]:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", module],
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return [tool.name for tool in result.tools]


def test_bioimage_stdio_protocol_exposes_tools():
    names = asyncio.run(_list_tools("biomcp_servers.bioimage"))
    assert names == ["inspect_image", "intensity_summary", "threshold_image"]


def test_imagej_stdio_protocol_exposes_tools():
    names = asyncio.run(_list_tools("biomcp_servers.imagej"))
    assert names == ["imagej_status", "run_macro"]


def test_llm_stdio_protocol_exposes_tools():
    names = asyncio.run(_list_tools("biomcp_servers.llm"))
    assert names == ["list_models", "complete"]
