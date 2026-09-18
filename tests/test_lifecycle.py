import pytest

from biomcp.lifecycle import snapshot


def test_snapshot_preserves_registry_lifecycle_truth():
    result = snapshot()

    assert result["product"] == "BioMCP"
    assert result["schema_version"] == "1.3"
    assert result["server_count"] == 7
    assert result["states"] == {
        "planned": 3,
        "experimental": 3,
        "validated": 1,
        "deprecated": 0,
    }
    assert result["installable_servers"] == ["bioimage", "imagej", "llm"]
    assert result["external_servers"] == ["bionuclei"]


def test_snapshot_can_scope_to_one_registered_server():
    assert snapshot("imagej")["servers"] == [
        {"name": "imagej", "status": "experimental", "installable": True, "external": False}
    ]


def test_snapshot_rejects_unknown_server():
    with pytest.raises(ValueError, match="Unknown BioMCP server: missing"):
        snapshot("missing")
