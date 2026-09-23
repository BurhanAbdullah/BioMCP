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
    monkeypatch.setattr(doctor, "resolve_transport_entry", lambda entry, *, client: "stdio")
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
        "transport": "stdio",
        "transport_error": None,
        "endpoint": None,
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
    monkeypatch.setattr(doctor, "resolve_transport_entry", lambda entry, *, client: "stdio")
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
    assert result[0]["transport"] == "stdio"
    assert result[0]["transport_error"] is None
    assert result[0]["missing_configuration"] == []
    assert result[0]["artifact"]["entry_point"] is True
    assert result[0]["ok"] is True


def test_diagnose_fails_when_registry_transport_is_invalid(monkeypatch):
    entry = {
        "name": "demo",
        "command": "demo-command",
        "status": "experimental",
        "dependencies": [],
        "config": [],
        "installable": True,
    }
    monkeypatch.setattr(doctor, "installable_servers", lambda: [entry])
    monkeypatch.setattr(doctor, "get_server", lambda name: entry)
    monkeypatch.setattr(doctor.shutil, "which", lambda command: "/usr/bin/demo-command")
    monkeypatch.setattr(
        doctor,
        "resolve_transport_entry",
        lambda entry, *, client: (_ for _ in ()).throw(ValueError("invalid transport declaration")),
    )
    monkeypatch.setattr(
        doctor,
        "_installed_artifact",
        lambda entry, command_path: {"distribution": "biomcp", "version": "0.2.0", "entry_point": True, "command_path": command_path, "ok": True},
    )

    result = doctor.diagnose("demo")[0]

    assert result["transport"] is None
    assert result["transport_error"] == "invalid transport declaration"
    assert result["ok"] is False
