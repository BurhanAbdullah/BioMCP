import json
from pathlib import Path
from biomcp.registry import get_server, installable_servers, load_registry

def test_registry_is_biomcp():
    data = load_registry(); assert data["product"] == "BioMCP"

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
