from __future__ import annotations

import sys

import pytest
from mcp import Client, StdioServerParameters


@pytest.mark.asyncio
async def test_real_stdio_client_discovers_and_calls_bioimage_tool(tmp_path):
    np = pytest.importorskip("numpy")
    tifffile = pytest.importorskip("tifffile")

    image = tmp_path / "stdio-contract.tif"
    tifffile.imwrite(image, np.array([[0, 1], [2, 3]], dtype=np.uint8))

    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "biomcp_servers.bioimage"],
    )

    async with Client(params) as client:
        listed = await client.list_tools()
        names = [tool.name for tool in listed.tools]
        assert names == ["inspect_image", "intensity_summary", "threshold_image"]

        tool = next(tool for tool in listed.tools if tool.name == "inspect_image")
        schema = getattr(tool, "inputSchema", None)
        if schema is None:
            schema = getattr(tool, "input_schema", None)
        assert isinstance(schema, dict)
        assert "path" in schema.get("properties", {})

        result = await client.call_tool("inspect_image", {"path": str(image)})
        assert result.is_error is False
        assert result.structured_content["shape"] == [2, 2]
        assert result.structured_content["dtype"] == "uint8"
        assert result.structured_content["ndim"] == 2
