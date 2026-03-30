from uuid import UUID, uuid4

import numpy as np

from vigil.embedding.adapters.secondary.in_memory_embedded_track_repository import InMemoryEmbeddedTrackRepository
from vigil.embedding.business_logic.gateways.crop_provider import CropProvider
from vigil.embedding.business_logic.gateways.embedding_model import EmbeddingModel, ImageData
from vigil.embedding.business_logic.models.embedded_track import EmbeddedTrack, Embedding
from vigil.embedding.business_logic.use_cases.index_track import IndexTrackUseCase

TRACK_ID = uuid4()
DETECTION_ID = uuid4()


class FakeCropProvider(CropProvider):
    """Fake crop provider for testing purpose."""

    def __init__(self):
        self._crops: dict[UUID, ImageData] = {}

    def get_by_detection(self, detection_id: UUID) -> ImageData:
        """Fake the crop."""
        return self._crops[detection_id]

    def given(self, detection_id: UUID, data: ImageData) -> None:
        """Register crop in the fake provider."""
        self._crops[detection_id] = data


class FakeEmbeddingModel(EmbeddingModel):
    """Fake embedding model for testing purpose."""

    def __init__(self):
        self._embedding = Embedding((0.5, 0.5))

    def embed(self, description: str) -> Embedding:
        """Unused stub."""
        raise NotImplementedError

    def embed_image(self, data: ImageData) -> Embedding:
        """Fake the model output."""
        return self._embedding


def test_should_index_a_new_track():
    # Given
    track_repository = InMemoryEmbeddedTrackRepository()
    crop_provider = FakeCropProvider()
    crop_provider.given(DETECTION_ID, np.zeros((1, 1, 3), dtype=np.uint8))
    model = FakeEmbeddingModel()
    use_case = IndexTrackUseCase(
        track_repository=track_repository,
        crop_provider=crop_provider,
        model=model,
    )

    # When
    use_case.execute(track_id=TRACK_ID, detections=[DETECTION_ID])

    # Then
    assert track_repository.list_tracks() == [
        EmbeddedTrack(id=TRACK_ID, detections=(Embedding((0.5, 0.5)),)),
    ]
