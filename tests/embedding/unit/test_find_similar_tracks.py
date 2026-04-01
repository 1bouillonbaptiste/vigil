from dataclasses import dataclass
from uuid import UUID

import pytest

from vigil.embedding.adapters.secondary.fake_embedding_model import FakeEmbeddingModel
from vigil.embedding.adapters.secondary.in_memory_embedded_track_repository import InMemoryEmbeddedTrackRepository
from vigil.embedding.business_logic.models.embedded_track import EmbeddedTrack, Embedding
from vigil.embedding.business_logic.services.embedding_matcher import EmbeddingMatcher
from vigil.embedding.business_logic.use_cases.find_similar_tracks import FindSimilarTracksUseCase

TRACK_ID = UUID("d1291c59-9e3a-4190-9142-eba82ed0e08f")
TRACK_ID_2 = UUID("395634fe-cfa1-4c37-b264-32c6886fd274")

# FakeEmbeddingModel always returns Embedding((0.5, 0.5)) for any description.
# MATCHING_EMBEDDING is aligned with that output  → probability ≈ 1.0.
# NON_MATCHING_EMBEDDING is the opposite direction → probability ≈ 0.0.
# NEUTRAL_EMBEDDING is perpendicular to both      → acts as the neutral baseline.
NEUTRAL_EMBEDDING = Embedding((0.5, -0.5))
MATCHING_EMBEDDING = Embedding((0.5, 0.5))
NON_MATCHING_EMBEDDING = Embedding((-0.5, -0.5))


@dataclass
class ThisContext:
    repository: InMemoryEmbeddedTrackRepository
    use_case: FindSimilarTracksUseCase


@pytest.fixture(scope="function")
def this_context() -> ThisContext:
    repository = InMemoryEmbeddedTrackRepository()
    model = FakeEmbeddingModel()
    matcher = EmbeddingMatcher(neutral_embedding=NEUTRAL_EMBEDDING)
    return ThisContext(
        repository=repository,
        use_case=FindSimilarTracksUseCase(repository=repository, model=model, matcher=matcher),
    )


def test_should_return_matching_track(this_context: ThisContext):
    # Given
    this_context.repository.save(EmbeddedTrack(id=TRACK_ID, detections=(MATCHING_EMBEDDING,)))
    this_context.repository.save(EmbeddedTrack(id=TRACK_ID_2, detections=(NON_MATCHING_EMBEDDING,)))

    # When
    result = this_context.use_case.execute(description="show me something", min_probability=0.9)

    # Then
    assert len(result) == 1
    assert result[0].id == TRACK_ID
    assert result[0].score > 0.9


def test_should_exclude_non_matching_track(this_context: ThisContext):
    # Given
    this_context.repository.save(EmbeddedTrack(id=TRACK_ID, detections=(NON_MATCHING_EMBEDDING,)))

    # When
    result = this_context.use_case.execute(description="show me something", min_probability=0.9)

    # Then
    assert result == []


def test_should_return_all_tracks_on_empty_description(this_context: ThisContext):
    # Given
    this_context.repository.save(EmbeddedTrack(id=TRACK_ID, detections=(MATCHING_EMBEDDING,)))
    this_context.repository.save(EmbeddedTrack(id=TRACK_ID_2, detections=(NON_MATCHING_EMBEDDING,)))

    # When
    result = this_context.use_case.execute(description="")

    # Then
    assert [m.id for m in result] == [TRACK_ID, TRACK_ID_2]
    assert all(m.score == 1.0 for m in result)
