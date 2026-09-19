import json

import biomcp.cli as cli
from biomcp.cli import main


def test_install_plan_is_read_only_and_registry_driven(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cli.Path, "home", staticmethod(lambda: tmp_path))
    monkeypatch.setattr(cli, "_missing_dependencies", lambda entry: ["missing_mod"] if entry["name"] == "bioimage" else [])

    assert main(["install", "--servers", "bioimage", "--clients", "generic,codex", "--plan"]) == 0
    result = json.loads(capsys.readouterr().out)

    assert result["product"] == "BioMCP"
    assert [server["name"] for server in result["servers"]] == ["bioimage"]
    assert result["servers"][0]["status"] == "experimental"
    assert result["servers"][0]["transport"] == "stdio"
    assert result["servers"][0]["distribution"] == "biomcp"
    assert result["servers"][0]["package_extra"] == "bioimage"
    assert result["servers"][0]["missing_dependencies"] == ["missing_mod"]
    assert [client["name"] for client in result["clients"]] == ["generic", "codex"]
    assert not list(tmp_path.rglob("mcp.json"))
    assert not list(tmp_path.rglob("config.toml"))


def test_install_plan_rejects_non_installable_before_output(monkeypatch):
    monkeypatch.setattr(cli, "get_server", lambda name: {"name": name, "status": "planned", "installable": False})
    try:
        main(["install", "--servers", "pymol", "--plan"])
    except SystemExit as exc:
        assert str(exc) == "pymol is not installable (status: planned)"
    else:
        raise AssertionError("expected SystemExit")
