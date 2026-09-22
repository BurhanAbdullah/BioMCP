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


def test_run_verify_blocks_non_ready_server(monkeypatch, capsys):
    monkeypatch.setattr(cli, "get_server", lambda _: {"installable": True, "command": "missing"})
    monkeypatch.setattr(cli, "assess_server", lambda _: {"status": "blocked", "reason": "missing dependency"})

    assert main(["run", "--verify", "imagej"]) == 1
    assert '"status": "blocked"' in capsys.readouterr().out


def test_run_without_verify_preserves_existing_launch(monkeypatch):
    monkeypatch.setattr(cli, "get_server", lambda _: {"installable": True, "command": "imagej"})
    monkeypatch.setattr(cli.shutil, "which", lambda command: "/usr/bin/imagej")
    calls = []

    def fake_run(argv, check=False, env=None):
        calls.append((argv, check, env))
        return type("Result", (), {"returncode": 0})()

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    assert main(["run", "imagej", "--", "--headless"]) == 0
    assert calls == [(["imagej", "--headless"], False, {"PATH": cli.os.environ["PATH"]})]
