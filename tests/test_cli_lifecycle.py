import biomcp.cli as cli
from biomcp.cli import main


def test_lifecycle_command_emits_registry_snapshot(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "snapshot",
        lambda server=None: {
            "product": "BioMCP",
            "schema_version": "1.3",
            "server_count": 1,
            "states": {"planned": 0, "experimental": 1, "validated": 0, "deprecated": 0},
            "installable_servers": ["imagej"],
            "external_servers": [],
            "servers": [
                {"name": "imagej", "status": "experimental", "installable": True, "external": False}
            ],
        },
    )

    assert main(["lifecycle", "imagej"]) == 0
    assert '"status": "experimental"' in capsys.readouterr().out


def test_lifecycle_command_rejects_unknown_server(monkeypatch):
    def fail(_):
        raise ValueError("Unknown BioMCP server: missing")

    monkeypatch.setattr(cli, "snapshot", fail)

    try:
        main(["lifecycle", "missing"])
    except SystemExit as exc:
        assert str(exc) == "Unknown BioMCP server: missing"
    else:
        raise AssertionError("expected SystemExit")
