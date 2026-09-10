import json
from pathlib import Path

import pytest

from biomcp.cli import _write_codex
from biomcp.registry import get_server, installable_servers, load_registry


def test_registry_is_biomcp():
    data = load_registry()
    assert data["product"] == "BioMCP"


def test_registry_has_required_families():
    names = {x["name"] for x in load_registry()["servers"]}
    assert {"bioimage", "imagej", "llm", "bionuclei"} <= names


def test_only_explicit_installable_entries_are_installable():
    for entry in installable_servers():
        assert entry.get("command")
        assert entry.get("package_extra")


def test_bionuclei_is_external_not_duplicated():
    entry = get_server("bionuclei")
    assert entry["external"] is True
    assert entry["installable"] is False


def test_registry_is_valid_json():
    payload = json.loads(Path("biomcp/registry.json").read_text(encoding="utf-8"))
    assert isinstance(payload["servers"], list)


def test_registry_rejects_duplicate_names(tmp_path):
    payload = load_registry()
    payload["servers"].append(dict(payload["servers"][0]))
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate server name"):
        load_registry(path)


def test_registry_rejects_installable_server_without_command(tmp_path):
    payload = load_registry()
    payload["servers"][0].pop("command", None)
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="requires a non-empty command"):
        load_registry(path)


def test_registry_rejects_installable_external_server(tmp_path):
    payload = load_registry()
    payload["servers"][0]["external"] = True
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="both installable and external"):
        load_registry(path)


def test_registry_rejects_missing_transport(tmp_path):
    payload = load_registry()
    payload["servers"][0].pop("transport", None)
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="transport list"):
        load_registry(path)


def test_codex_writer_is_idempotent(tmp_path):
    path = tmp_path / "config.toml"
    servers = {"biomcp_bioimage": {"command": "biomcp-bioimage", "args": []}}
    _write_codex(path, servers)
    _write_codex(path, servers)
    text = path.read_text(encoding="utf-8")
    assert text.count("[mcp_servers.biomcp_bioimage]") == 1
    assert text.count("command = \"biomcp-bioimage\"") == 1


def test_packaged_registry_matches_source_registry():
    root = Path(__file__).resolve().parents[1]
    source = json.loads((root / "biomcp" / "registry.json").read_text(encoding="utf-8"))
    packaged = json.loads((root / "src" / "biomcp" / "registry.json").read_text(encoding="utf-8"))
    assert packaged == source
