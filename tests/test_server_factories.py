from biomcp_servers.bioimage import create_server as create_bioimage
from biomcp_servers.imagej import create_server as create_imagej
from biomcp_servers.llm import create_server as create_llm


def test_all_installable_server_factories_initialize():
    for factory in (create_bioimage, create_imagej, create_llm):
        server = factory()
        assert server is not None


def test_bioimage_rejects_invalid_element_limit(monkeypatch, tmp_path):
    monkeypatch.setenv("BIOMCP_MAX_IMAGE_ELEMENTS", "0")
    path = tmp_path / "image.tif"
    path.write_bytes(b"not-a-real-tiff")
    from biomcp_servers.bioimage import _load_image
    import pytest
    with pytest.raises(ValueError, match="must be positive"):
        _load_image(path)


def test_imagej_macro_requires_configured_executable(monkeypatch, tmp_path):
    monkeypatch.delenv("BIOMCP_IMAGEJ_EXECUTABLE", raising=False)
    monkeypatch.delenv("IMAGEJ_EXECUTABLE", raising=False)
    path = tmp_path / "image.tif"
    macro = tmp_path / "macro.ijm"
    path.write_bytes(b"x")
    macro.write_text("print('x');", encoding="utf-8")
    server = create_imagej()
    assert server is not None


def test_imagej_timeout_is_structured_and_child_env_is_sanitized(monkeypatch, tmp_path):
    monkeypatch.setenv("BIOMCP_LLM_API_KEY", "do-not-leak")
    monkeypatch.setenv("OPENAI_API_KEY", "do-not-leak")
    monkeypatch.setenv("IMAGEJ_SAFE_OPTION", "keep")
    image = tmp_path / "image.tif"
    macro = tmp_path / "macro.ijm"
    image.write_bytes(b"x")
    macro.write_text("print('x');", encoding="utf-8")

    import subprocess
    from biomcp_servers import imagej

    seen = {}

    def fake_run(*args, **kwargs):
        seen["env"] = kwargs["env"]
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs["timeout"], output="partial", stderr="err")

    monkeypatch.setattr(imagej.subprocess, "run", fake_run)
    value = imagej._run_macro("/usr/bin/fiji", image, macro, 3)
    assert value["timed_out"] is True
    assert value["returncode"] is None
    assert seen["env"]["IMAGEJ_SAFE_OPTION"] == "keep"
    assert "BIOMCP_LLM_API_KEY" not in seen["env"]
    assert "OPENAI_API_KEY" not in seen["env"]


def test_llm_requires_credentials(monkeypatch):
    monkeypatch.delenv("BIOMCP_LLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from biomcp_servers.llm import _headers
    import pytest
    with pytest.raises(RuntimeError, match="API_KEY"):
        _headers()


def test_llm_rejects_unsafe_base_urls(monkeypatch):
    import pytest
    from biomcp_servers.llm import _base

    for value in ("file:///etc/passwd", "ftp://example.org/v1", "https://user:pass@example.org/v1"):
        monkeypatch.setenv("BIOMCP_LLM_BASE_URL", value)
        with pytest.raises(ValueError, match="HTTP\\(S\\) URL"):
            _base()
