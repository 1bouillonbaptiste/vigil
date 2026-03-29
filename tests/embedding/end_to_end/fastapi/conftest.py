from collections.abc import Generator

import pytest
from starlette.testclient import TestClient

from vigil.app.fastapi.main import app


@pytest.fixture(scope="function")
def fastapi_client() -> Generator[TestClient, None, None]:
    yield TestClient(app)
    app.dependency_overrides.clear()
