import json

from biomcp.registry_cli import main, validate_registries


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
