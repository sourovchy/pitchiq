"""Shared pytest fixtures for the PitchIQ backend test suite."""

from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from app.config.settings import get_settings
from app.main import app


@pytest.fixture()
def client() -> TestClient:
    test_client = TestClient(app)
    yield test_client
    # Ensure dependency overrides from one test don't leak into the next.
    test_client.app.dependency_overrides.clear()
    get_settings.cache_clear()