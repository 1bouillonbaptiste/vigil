import pytest
from starlette.testclient import TestClient

from vigil.adapters.primary.fastapi.main import app


@pytest.fixture
def fastapi_client() -> TestClient:
    return TestClient(app)
