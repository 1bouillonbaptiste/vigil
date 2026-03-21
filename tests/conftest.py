import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from vigil.adapters.primary.fastapi.controllers import video_analysis


@pytest.fixture
def fastapi_client() -> TestClient:

    app = FastAPI()
    app.include_router(video_analysis.router)

    return TestClient(app)
