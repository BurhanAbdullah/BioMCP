import json

from biomcp.cli import main


def test_catalog_cli_emits_registry_discovery(capsys):
    assert main(["catalog", "imagej"]) == 0

    result = json.loads(capsys.readouterr().out)
    assert result["product"] == "BioMCP"
    assert result["server_count"] == 1
    assert result["servers"][0]["name"] == "imagej"
    assert result["servers"][0]["transport"] == ["stdio"]


def test_catalog_cli_rejects_unknown_server(capsys):
    try:
        main(["catalog", "missing"])
    except SystemExit as exc:
        assert str(exc) == "Unknown BioMCP server: missing"
    else:
        raise AssertionError("expected SystemExit")

    assert capsys.readouterr().out == ""
