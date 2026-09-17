from biomcp import assess


def test_assess_blocks_before_live_validation_when_doctor_fails(monkeypatch):
    monkeypatch.setattr(
        assess,
        "diagnose",
        lambda server: [
            {
                "name": server,
                "command": "example",
                "command_path": None,
                "missing_dependencies": ["missing_module"],
                "missing_configuration": [],
                "ok": False,
            }
        ],
    )
    called = False

    def _unexpected_validation(_):
        nonlocal called
        called = True
        raise AssertionError("live validation must not run when prerequisites fail")

    monkeypatch.setattr(assess, "validate_server", _unexpected_validation)

    result = assess.assess_server("bioimage")
    assert result["status"] == "blocked"
    assert "doctor" in result["evidence"]
    assert called is False


def test_assess_reports_live_contract_drift(monkeypatch):
    monkeypatch.setattr(
        assess,
        "diagnose",
        lambda server: [{"name": server, "command": "server", "ok": True}],
    )
    monkeypatch.setattr(
        assess,
        "validate_server",
        lambda server: {
            "server": server,
            "status": "experimental",
            "transport": ["stdio"],
            "declared_tools": ["a", "b"],
            "live_tools": ["a"],
            "missing_tools": ["b"],
            "unexpected_tools": [],
            "ok": False,
        },
    )

    result = assess.assess_server("bioimage")
    assert result["status"] == "drift"
    assert result["evidence"]["contract"]["missing_tools"] == ["b"]


def test_assess_returns_ready_only_when_contract_is_green(monkeypatch):
    monkeypatch.setattr(
        assess,
        "diagnose",
        lambda server: [{"name": server, "command": "server", "ok": True}],
    )
    monkeypatch.setattr(
        assess,
        "validate_server",
        lambda server: {
            "server": server,
            "status": "experimental",
            "transport": ["stdio"],
            "declared_tools": ["a"],
            "live_tools": ["a"],
            "missing_tools": [],
            "unexpected_tools": [],
            "ok": True,
        },
    )

    result = assess.assess_server("bioimage")
    assert result["status"] == "ready"
    assert result["evidence"]["contract"]["ok"] is True


def test_assess_surfaces_live_validation_errors(monkeypatch):
    monkeypatch.setattr(
        assess,
        "diagnose",
        lambda server: [{"name": server, "command": "server", "ok": True}],
    )

    def _raise(_):
        raise RuntimeError("server handshake failed")

    monkeypatch.setattr(assess, "validate_server", _raise)

    result = assess.assess_server("bioimage")
    assert result["status"] == "error"
    assert result["evidence"]["contract_error"]["type"] == "RuntimeError"
    assert result["evidence"]["contract_error"]["message"] == "server handshake failed"
