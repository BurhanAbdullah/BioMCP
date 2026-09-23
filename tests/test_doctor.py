import biomcp.doctor as doctor


def test_diagnose_marks_missing_configuration_as_not_ok(monkeypatch):
    monkeypatch.setattr(doctor, "installable_servers", lambda: [{
        "name": "demo",
        "command": "demo-command",
        "status": "beta",
        "dependencies": [],
        "config": ["DEMO_API_KEY"],
        "installable": True,
    }])
    monkeypatch.delenv("DEMO_API_KEY", raising=False)
    monkeypatch.setattr(doctor.shutil, "which", lambda command: "/usr/bin/demo-command")
    monkeypatch.setattr(
        doctor,
        "_installed_artifact",
        lambda entry, command_path: {
            "distribution": "biomcp",
            "version": "0.2.0",
            "entry_point": True,
            "command_path": command_path,
            "ok": True,
        },
    )

    result = doctor.diagnose()

    assert result == [{
        "name": "demo",
        "lifecycle_status": "beta",
        "command": "demo-command",
        "command_path": "/usr/bin/demo-command",
        "missing_dependencies": [],
        "missing_configuration": ["DEMO_API_KEY"],
        "artifact": {
            "distribution": "biomcp",
            "version": "0.2.0",
            "entry_point": True,
            "command_path": "/usr/bin/demo-command",
            "ok": True,
        },
        "ok": False,
    }]


def test_diagnose_is_ok_when_configuration_and_artifact_are_present(monkeypatch):
    monkeypatch.setattr(doctor, "installable_servers", lambda: [{
        "name": "demo",
        "command": "demo-command",
        "status": "beta",
        "dependencies": [],
        "config": ["DEMO_API_KEY"],
        "installable": True,
    }])
    monkeypatch.setenv("DEMO_API_KEY", "configured")
    monkeypatch.setattr(doctor.shutil, "which", lambda command: "/usr/bin/demo-command")
    monkeypatch.setattr(
        doctor,
        "_installed_artifact",
        lambda entry, command_path: {
            "distribution": "biomcp",
            "version": "0.2.0",
            "entry_point": True,
            "command_path": command_path,
            "ok": True,
        },
    )

    result = doctor.diagnose()

    assert result[0]["lifecycle_status"] == "beta"
    assert result[0]["missing_configuration"] == []
    assert result[0]["artifact"]["entry_point"] is True
    assert result[0]["ok"] is True
