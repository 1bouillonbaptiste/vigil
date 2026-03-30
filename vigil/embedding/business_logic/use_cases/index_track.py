from uuid import UUID

from vigil.embedding.business_logic.gateways.crop_provider import CropProvider
from vigil.embedding.business_logic.gateways.embedded_track_repository import EmbeddedTrackRepository
from vigil.embedding.business_logic.gateways.embedding_model import EmbeddingModel
from vigil.embedding.business_logic.models.embedded_track import EmbeddedTrack


class IndexTrackUseCase:
    """Index a track in the database."""

    def __init__(
        self,
        track_repository: EmbeddedTrackRepository,
        crop_provider: CropProvider,
        model: EmbeddingModel,
    ) -> None:
        self._track_repository = track_repository
        self._crop_provider = crop_provider
        self._model = model

    def execute(self, track_id: UUID, detections: list[UUID]) -> None:
        """Execute the use case given track data."""
        self._track_repository.save(
            EmbeddedTrack(
                id=track_id,
                detections=tuple(
                    self._model.embed_image(self._crop_provider.get_by_detection(detection_id))
                    for detection_id in detections
                ),
            )
        )
