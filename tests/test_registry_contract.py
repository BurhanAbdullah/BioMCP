import json
from pathlib import Path

import pytest

from biomcp.registry import load_registry


def test_registry_is_valid_and_has_expected_lifecycle_entries():
    data = load_registry()
    assert data["schema_version"] == "1.3"
    names = {entry["name"] for entry in data["servers"]}
    assert {"bioimage", "imagej", "llm", "bionuclei", "pymol", "cellprofiler", "blastplus"} <= names

    installable = [entry for entry in data["servers"] if entry["installable"]]
    assert {entry["name"] for entry in installable} == {"bioimage", "imagej", "llm"}
    assert all(entry["transport"] for entry in installable)
    assert all(entry["command"] for entry in installable)

    llm = next(entry for entry in data["servers"] if entry["name"] == "llm")
    assert {"openai-compatible", "ollama", "vllm"} == set(llm["providers"])
    assert {"model_discovery", "streaming", "structured_output", "tool_calling"} <= set(llm["capabilities"])


def test_duplicate_registry_names_are_rejected(tmp_path: Path):
    source = load_registry()
    source["servers"].append(dict(source["servers"][0]))
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(source), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate server name"):
        load_registry(path)


def test_planned_server_cannot_be_installable(tmp_path: Path):
    source = load_registry()
    source["servers"][0]["status"] = "planned"
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(source), encoding="utf-8")
    with pytest.raises(ValueError, match="must be experimental or validated"):
        load_registry(path)
