"""Render host routing must preserve authentication and reject other tenants."""
import importlib

from fastapi.testclient import TestClient
import pytest

from apps.api import main


@pytest.mark.parametrize("hostname", ["taxrora.onrender.com", "taxrora-123.onrender.com"])
def test_render_accepts_only_own_hostname(monkeypatch, hostname):
    monkeypatch.setenv("RENDER_EXTERNAL_HOSTNAME", hostname)
    try:
        app = importlib.reload(main).app
        with TestClient(app, base_url=f"https://{hostname}") as client:
            assert client.get("/health").status_code == 200
            assert client.get("/api/cases").status_code == 401
            assert client.get("/health", headers={"host": "another.onrender.com"}).status_code == 400
            assert client.get("/health", headers={"host": "evil.example"}).status_code == 400
    finally:
        monkeypatch.delenv("RENDER_EXTERNAL_HOSTNAME")
        importlib.reload(main)


def test_render_hostname_cannot_supply_wildcard(monkeypatch):
    monkeypatch.setenv("RENDER_EXTERNAL_HOSTNAME", "*.onrender.com")
    try:
        with TestClient(importlib.reload(main).app) as client:
            assert client.get("/health", headers={"host": "another.onrender.com"}).status_code == 400
    finally:
        monkeypatch.delenv("RENDER_EXTERNAL_HOSTNAME")
        importlib.reload(main)


@pytest.mark.parametrize("revision", ["a" * 40, "", "invalid-runtime-value"])
def test_health_exposes_only_valid_public_revision(monkeypatch, revision):
    monkeypatch.setenv("RENDER_GIT_COMMIT", revision)
    with TestClient(main.app) as client:
        data = client.get("/health").json()
    assert data["status"] == "ok"
    if revision == "a" * 40:
        assert data["revision"] == revision
    else:
        assert "revision" not in data
