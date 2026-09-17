from argparse import Namespace

from biomcp import cli


def test_install_verify_flag_defaults_false():
    parser = cli.argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("install")
    p.add_argument("--verify", action="store_true")
    args = parser.parse_args(["install"])
    assert args.verify is False


def test_verify_installed_returns_failure_for_non_ready(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "assess_server",
        lambda name: {"status": "drift", "server": name, "evidence": {}},
    )
    assert cli._verify_installed(["bioimage"]) == 1
    assert '"status": "drift"' in capsys.readouterr().out


def test_verify_installed_succeeds_only_for_ready(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "assess_server",
        lambda name: {"status": "ready", "server": name, "evidence": {}},
    )
    assert cli._verify_installed(["bioimage", "llm"]) == 0
    assert capsys.readouterr().out.count('"status": "ready"') == 2
