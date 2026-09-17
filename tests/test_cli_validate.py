import biomcp.cli as cli
from biomcp.cli import main


def test_validate_command_returns_failure_for_contract_mismatch(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "validate_server",
        lambda _: {
            "server": "bioimage",
            "status": "experimental",
            "transport": ["stdio"],
            "declared_tools": ["inspect_image"],
            "live_tools": ["different_tool"],
            "missing_tools": ["inspect_image"],
            "unexpected_tools": ["different_tool"],
            "ok": False,
        },
    )

    assert main(["validate", "bioimage"]) == 1
    assert '"ok": false' in capsys.readouterr().out


def test_validate_command_returns_success_for_matching_contract(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "validate_server",
        lambda _: {
            "server": "bioimage",
            "status": "experimental",
            "transport": ["stdio"],
            "declared_tools": ["inspect_image"],
            "live_tools": ["inspect_image"],
            "missing_tools": [],
            "unexpected_tools": [],
            "ok": True,
        },
    )

    assert main(["validate", "bioimage"]) == 0
    assert '"ok": true' in capsys.readouterr().out
