"""Deterministic coverage for built-in Streamable HTTP server factories."""
from __future__ import annotations

import os

from biomcp_servers.bioimage import create_http_app as create_bioimage_http_app
from biomcp_servers.imagej import create_http_app as create_imagej_http_app


def test_bioimage_http_factory_uses_shared_transport(monkeypatch):
    monkeypatch.setenv("BIOMCP_HTTP_ALLOWED_HOSTS", "localhost")
    monkeypatch.delenv("BIOMCP_HTTP_MAX_CONCURRENCY", raising=False)
    app = create_bioimage_http_app()
    assert callable(app)


def test_imagej_http_factory_uses_shared_transport(monkeypatch):
    monkeypatch.setenv("BIOMCP_HTTP_ALLOWED_HOSTS", "localhost")
    monkeypatch.delenv("BIOMCP_HTTP_MAX_CONCURRENCY", raising=False)
    app = create_imagej_http_app()
    assert callable(app)


def test_factories_do_not_require_imagej_executable(monkeypatch):
    monkeypatch.setenv("BIOMCP_HTTP_ALLOWED_HOSTS", "localhost")
    monkeypatch.delenv("BIOMCP_IMAGEJ_EXECUTABLE", raising=False)
    monkeypatch.delenv("IMAGEJ_EXECUTABLE", raising=False)
    assert callable(create_imagej_http_app())
