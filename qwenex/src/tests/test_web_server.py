"""Tests for web server."""

import pytest
from fastapi.testclient import TestClient
from qwenex.web.server import create_app


def test_create_app():
    """Test app creation."""
    app = create_app()
    assert app is not None


def test_index_route():
    """Test index page."""
    app = create_app()
    client = TestClient(app)
    
    response = client.get("/")
    assert response.status_code == 200
    assert b"Qwenex Dashboard" in response.content


def test_health_route():
    """Test health endpoint."""
    app = create_app()
    client = TestClient(app)
    
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
