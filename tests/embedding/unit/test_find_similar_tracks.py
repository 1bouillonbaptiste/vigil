from dataclasses import dataclass
from uuid import UUID

import pytest

from vigil.embedding.adapters.secondary.in_memory_embedded_track_repository import InMemoryEmbeddedTrackRepository
from vigil.embedding.business_logic.gateways.embedding_model import EmbeddingModel, ImageData
from vigil.embedding.business_logic.models.embedded_track import EmbeddedTrack, Embedding
from vigil.embedding.business_logic.use_cases.find_similar_tracks import FindSimilarTracksUseCase

TRACK_ID = UUID("d1291c59-9e3a-4190-9142-eba82ed0e08f")
TRACK_ID_2 = UUID("395634fe-cfa1-4c37-b264-32c6886fd274")


class FakeEmbeddingModel(EmbeddingModel):
    """Fake embedding model for testing purpose."""

    def __init__(self):
        self._embedding = Embedding((0.5, 0.5))

    def embed(self, description: str) -> Embedding:
        """Fake the model output."""
        return self._embedding

    def embed_image(self, data: ImageData) -> Embedding:
        """Unused stub."""
        raise NotImplementedError


@dataclass
class ThisContext:
    repository: InMemoryEmbeddedTrackRepository
    model: FakeEmbeddingModel
    use_case: FindSimilarTracksUseCase


@pytest.fixture(scope="function")
def this_context() -> ThisContext:
    repository = InMemoryEmbeddedTrackRepository()
    model = FakeEmbeddingModel()
    return ThisContext(
        repository=repository,
        model=model,
        use_case=FindSimilarTracksUseCase(repository=repository, model=model),
    )


def test_should_query_tracks_with_high_similarity(this_context: ThisContext):
    # Given
    this_context.repository.save(EmbeddedTrack(id=TRACK_ID, detections=(Embedding((0.5, 0.5)),)))
    this_context.repository.save(EmbeddedTrack(id=TRACK_ID_2, detections=(Embedding((0.1, 0.9)),)))

    # When
    result = this_context.use_case.execute(description="show me something", min_similarity=0.9)

    # Then
    assert result == [EmbeddedTrack(id=TRACK_ID, detections=(Embedding((0.5, 0.5)),))]


def test_should_return_all_tracks_when_description_is_empty(this_context: ThisContext):
    # Given
    this_context.repository.save(EmbeddedTrack(id=TRACK_ID, detections=(Embedding((0.5, 0.5)),)))
    this_context.repository.save(EmbeddedTrack(id=TRACK_ID_2, detections=(Embedding((0.1, 0.9)),)))

    # When
    result = this_context.use_case.execute(description="")

    # Then
    assert result == [
        EmbeddedTrack(id=TRACK_ID, detections=(Embedding((0.5, 0.5)),)),
        EmbeddedTrack(id=TRACK_ID_2, detections=(Embedding((0.1, 0.9)),)),
    ]


def test_should_query_tracks_with_any_similarity(this_context: ThisContext):
    # Given
    this_context.repository.save(EmbeddedTrack(id=TRACK_ID, detections=(Embedding((0.5, 0.5)),)))
    this_context.repository.save(EmbeddedTrack(id=TRACK_ID_2, detections=(Embedding((0.1, 0.9)),)))

    # When
    result = this_context.use_case.execute(description="show me something", min_similarity=0.5)

    # Then
    assert result == [
        EmbeddedTrack(id=TRACK_ID, detections=(Embedding((0.5, 0.5)),)),
        EmbeddedTrack(id=TRACK_ID_2, detections=(Embedding((0.1, 0.9)),)),
    ]
