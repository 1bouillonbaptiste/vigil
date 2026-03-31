from uuid import UUID, uuid4

import pytest
from starlette.testclient import TestClient

from vigil.embedding.adapters.primary.fastapi.app_dependencies import (
    _get_embedded_track_repository,
    _get_embedding_matcher,
    _get_embedding_model,
)
from vigil.embedding.adapters.secondary.fake_embedding_model import FakeEmbeddingModel
from vigil.embedding.adapters.secondary.in_memory_embedded_track_repository import InMemoryEmbeddedTrackRepository
from vigil.embedding.business_logic.models.embedded_track import EmbeddedTrack, Embedding
from vigil.embedding.business_logic.services.embedding_matcher import EmbeddingMatcher

TRACK_ID = UUID("d1291c59-9e3a-4190-9142-eba82ed0e08f")
TRACK_ID_2 = uuid4()

# FakeEmbeddingModel always returns Embedding((0.5, 0.5)).
# Use a neutral embedding perpendicular to that so stored tracks with (0.5, 0.5)
# have probability ≈ 1.0 and are always returned.
_FAKE_NEUTRAL_EMBEDDING = Embedding((0.5, -0.5))


@pytest.fixture(scope="function")
def this_context(fastapi_client: TestClient) -> tuple[InMemoryEmbeddedTrackRepository, TestClient]:
    repo = InMemoryEmbeddedTrackRepository()
    fastapi_client.app.dependency_overrides[_get_embedded_track_repository] = lambda: repo  # type: ignore
    fastapi_client.app.dependency_overrides[_get_embedding_model] = lambda: FakeEmbeddingModel()  # type: ignore
    fastapi_client.app.dependency_overrides[_get_embedding_matcher] = lambda: EmbeddingMatcher(  # type: ignore
        neutral_embedding=_FAKE_NEUTRAL_EMBEDDING
    )
    return repo, fastapi_client


def test_can_query_an_existing_track_by_its_description(
    this_context: tuple[InMemoryEmbeddedTrackRepository, TestClient],
):
    repo, client = this_context
    # Given
    repo.save(EmbeddedTrack(id=TRACK_ID, detections=(Embedding((0.5, 0.5)),)))

    # When
    response = client.get("/tracks/by-description", params={"description": "a person walking"})

    # Then
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "content": {"tracks": [str(TRACK_ID)]},
        "error": None,
    }


def test_should_return_all_tracks_on_empty_description(
    this_context: tuple[InMemoryEmbeddedTrackRepository, TestClient],
):
    repo, client = this_context
    # Given
    repo.save(EmbeddedTrack(id=TRACK_ID, detections=(Embedding((0.5, 0.5)),)))
    repo.save(EmbeddedTrack(id=TRACK_ID_2, detections=(Embedding((0.01, 0.99)),)))

    # When
    response = client.get("/tracks/by-description", params={"description": ""})

    # Then
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "content": {"tracks": [str(TRACK_ID), str(TRACK_ID_2)]},
        "error": None,
    }
