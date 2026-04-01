from uuid import UUID

from vigil.embedding.business_logic.gateways.embedded_track_repository import EmbeddedTrackRepository
from vigil.embedding.business_logic.gateways.embedding_model import EmbeddingModel
from vigil.embedding.business_logic.gateways.frame_reader import FrameReader
from vigil.embedding.business_logic.models.detection_ref import DetectionRef
from vigil.embedding.business_logic.models.embedded_track import EmbeddedTrack


class IndexTrackUseCase:
    """Embed all detections of a track and persist the result."""

    def __init__(
        self,
        track_repository: EmbeddedTrackRepository,
        frame_reader: FrameReader,
        model: EmbeddingModel,
    ) -> None:
        self._track_repository = track_repository
        self._frame_reader = frame_reader
        self._model = model

    @staticmethod
    def _sample(detections: list[DetectionRef], n: int) -> list[DetectionRef]:
        if n == 1:
            return [detections[0]]
        step = (len(detections) - 1) / (n - 1)
        return [detections[int(i * step)] for i in range(n)]

    def execute(self, track_id: UUID, video_id: UUID, detections: list[DetectionRef]) -> None:
        """Crop each detection, embed it, and save the embedded track."""
        sampled = self._sample(detections, min(5, len(detections)))
        crops = [self._frame_reader.read_crop(video_id, d.frame_position, d.bbox) for d in sampled]
        embeddings = self._model.embed_images(crops)
        self._track_repository.save(
            EmbeddedTrack(
                id=track_id,
                detections=tuple(embeddings),
            )
        )
