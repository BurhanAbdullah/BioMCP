"""Tests for registry-authoritative CLI server launch."""
from __future__ import annotations

from argparse import Namespace

import pytest

from biomcp import cli


def _entry(**overrides):
    entry = {
        "name": "sample",
        "status": "experimental",
        "installable": True,
        "transport": ["stdio"],
        "command": "sample-mcp",
        "args": [],
    }
    entry.update(overrides)
    return entry


def test_run_blocks_deprecated_server_before_launch(monkeypatch):
    monkeypatch.setattr(cli, "get_server", lambda _: _entry(status="deprecated"))
    monkeypatch.setattr(cli.subprocess, "run", pytest.fail)

    with pytest.raises(SystemExit, match="deprecated and cannot be launched"):
        cli.cmd_run(Namespace(server="sample", extra=[], verify=False))


def test_run_launches_registry_declared_stdio_server(monkeypatch):
    monkeypatch.setattr(cli, "get_server", lambda _: _entry(args=["--mode", "stdio"]))
    monkeypatch.setattr(cli.shutil, "which", lambda _: "/usr/local/bin/sample-mcp")
    calls = []

    class Result:
        returncode = 7

    def fake_run(command, check=False, env=None):
        calls.append((command, check, env))
        return Result()

    monkeypatch.setattr(cli.subprocess, "run", fake_run)
    monkeypatch.setenv("SAMPLE_TOKEN", "secret")

    assert cli.cmd_run(
        Namespace(
            server="sample",
            extra=["--stdio"],
            verify=False,
        )
    ) == 7
    assert calls == [
        (["sample-mcp", "--mode", "stdio", "--stdio"], False, {"PATH": cli.os.environ["PATH"]})
    ]


def test_run_passes_only_registry_declared_environment(monkeypatch):
    monkeypatch.setattr(
        cli,
        "get_server",
        lambda _: _entry(config=["SAMPLE_TOKEN", "OPTIONAL_TOKEN"]),
    )
    monkeypatch.setattr(cli.shutil, "which", lambda _: "/usr/local/bin/sample-mcp")
    monkeypatch.setenv("SAMPLE_TOKEN", "secret")
    monkeypatch.setenv("UNDECLARED_TOKEN", "must-not-leak")
    calls = []

    class Result:
        returncode = 0

    def fake_run(command, check=False, env=None):
        calls.append(env)
        return Result()

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    assert cli.cmd_run(Namespace(server="sample", extra=[], verify=False)) == 0
    assert calls == [
        {
            "PATH": cli.os.environ["PATH"],
            "SAMPLE_TOKEN": "secret",
        }
    ]
