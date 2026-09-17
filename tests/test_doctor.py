import biomcp.doctor as doctor


def test_diagnose_marks_missing_configuration_as_not_ok(monkeypatch):
    monkeypatch.setattr(doctor, "installable_servers", lambda: [{
        "name": "demo",
        "command": "demo-command",
        "dependencies": [],
        "config": ["DEMO_API_KEY"],
        "installable": True,
    }])
    monkeypatch.delenv("DEMO_API_KEY", raising=False)
    monkeypatch.setattr(doctor.shutil, "which", lambda command: "/usr/bin/demo-command")

    result = doctor.diagnose()

    assert result == [{
        "name": "demo",
        "command": "demo-command",
        "command_path": "/usr/bin/demo-command",
        "missing_dependencies": [],
        "missing_configuration": ["DEMO_API_KEY"],
        "ok": False,
    }]


def test_diagnose_is_ok_when_configuration_is_present(monkeypatch):
    monkeypatch.setattr(doctor, "installable_servers", lambda: [{
        "name": "demo",
        "command": "demo-command",
        "dependencies": [],
        "config": ["DEMO_API_KEY"],
        "installable": True,
    }])
    monkeypatch.setenv("DEMO_API_KEY", "configured")
    monkeypatch.setattr(doctor.shutil, "which", lambda command: "/usr/bin/demo-command")

    result = doctor.diagnose()

    assert result[0]["missing_configuration"] == []
    assert result[0]["ok"] is True
