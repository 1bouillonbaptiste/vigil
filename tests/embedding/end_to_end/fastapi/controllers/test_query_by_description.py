from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest
from starlette.testclient import TestClient

from vigil.embedding.adapters.primary.fastapi.app_dependencies import (
    _get_embedded_track_repository,
    _get_embedding_model,
)
from vigil.embedding.adapters.secondary.in_memory_embedded_track_repository import InMemoryEmbeddedTrackRepository
from vigil.embedding.business_logic.gateways.embedding_model import EmbeddingModel
from vigil.embedding.business_logic.models.embedded_track import EmbeddedTrack, Embedding

TRACK_ID = UUID("d1291c59-9e3a-4190-9142-eba82ed0e08f")
TRACK_ID_2 = uuid4()


class FakeEmbeddingModel(EmbeddingModel):
    """Fake embedding model for testing purposes."""

    def embed(self, description: str) -> Embedding:
        """Fake the model output."""
        return Embedding((0.5, 0.5))


@dataclass
class ThisContext:
    """Context for testing query by description controller."""

    embedded_track_repo: InMemoryEmbeddedTrackRepository
    client: TestClient


@pytest.fixture(scope="function")
def this_context(fastapi_client: TestClient) -> ThisContext:
    repo = InMemoryEmbeddedTrackRepository()
    model = FakeEmbeddingModel()

    fastapi_client.app.dependency_overrides[_get_embedded_track_repository] = lambda: repo  # type: ignore
    fastapi_client.app.dependency_overrides[_get_embedding_model] = lambda: model  # type: ignore

    return ThisContext(embedded_track_repo=repo, client=fastapi_client)


def test_can_query_an_existing_track_by_its_description(this_context: ThisContext):
    # Given
    this_context.embedded_track_repo.save(EmbeddedTrack(id=TRACK_ID, detections=(Embedding((0.5, 0.5)),)))

    # When
    response = this_context.client.get("/tracks/by-description", params={"description": "a person walking"})

    # Then
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "content": {"tracks": [str(TRACK_ID)]},
        "error": None,
    }


def test_should_return_all_tracks_on_empty_description(this_context: ThisContext):
    # Given
    this_context.embedded_track_repo.save(EmbeddedTrack(id=TRACK_ID, detections=(Embedding((0.5, 0.5)),)))
    this_context.embedded_track_repo.save(EmbeddedTrack(id=TRACK_ID_2, detections=(Embedding((0.01, 0.99)),)))

    # When
    response = this_context.client.get("/tracks/by-description", params={"description": ""})

    # Then
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "content": {"tracks": [str(TRACK_ID), str(TRACK_ID_2)]},
        "error": None,
    }
