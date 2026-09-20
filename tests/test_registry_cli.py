import json

from biomcp.registry_cli import main, registry_provenance_summary, validate_registries


def test_validate_registries_reports_consistent_installable_set():
    result = validate_registries()
    assert result["product"] == "BioMCP"
    assert result["registry_consistent"] is True
    assert result["installable_servers"] == ["bioimage", "imagej", "llm"]


def test_registry_cli_validate_emits_machine_readable_summary(capsys):
    assert main(["validate"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["registry_consistent"] is True
    assert payload["server_count"] == 7


def test_registry_provenance_is_canonical_and_deterministic():
    result = registry_provenance_summary()
    assert result["source"] == "canonical_registry"
    assert result["schema_version"] == "1.3"
    assert result["server_count"] == 7
    assert len(result["sha256"]) == 64
    assert result["sha256"] == registry_provenance_summary()["sha256"]


def test_registry_cli_provenance_emits_machine_readable_summary(capsys):
    assert main(["provenance"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["source"] == "canonical_registry"
    assert payload["schema_version"] == "1.3"
    assert payload["server_count"] == 7
    assert len(payload["sha256"]) == 64
