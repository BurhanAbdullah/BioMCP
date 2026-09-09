import json
from pathlib import Path

from biomcp.registry import get_server, installable_servers, load_registry


def test_registry_loads() -> None:
    data = load_registry()
    assert data["product"] == "BioMCP"
    assert any(item["name"] == "bionuclei" for item in data["servers"])


def test_bionuclei_is_installable_and_has_command() -> None:
    server = get_server("bionuclei")
    assert server["installable"] is True
    assert server["command"] == "bionuclei-mcp"


def test_planned_servers_are_not_installable() -> None:
    planned = [x for x in load_registry()["servers"] if x["status"] == "planned"]
    assert planned
    assert all(x.get("installable") is False for x in planned)


def test_registry_file_is_json() -> None:
    payload = json.loads(Path("biomcp/registry.json").read_text(encoding="utf-8"))
    assert isinstance(payload["servers"], list)
