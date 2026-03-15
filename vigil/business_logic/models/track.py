from dataclasses import dataclass
from uuid import UUID, uuid4

from vigil.business_logic.models.detection import Detection


@dataclass(frozen=True)
class Track:
    """Represent a track."""

    id: UUID
    """Identifier of the track."""

    video_id: UUID
    """Identifier of the video where the track comes from."""

    detections: list[UUID]
    """Identifiers of the detections tracked by the object."""

    thumbnail_id: UUID
    """Identifier of the most representative detection in the track."""

    @classmethod
    def create(cls, video_id: UUID, detections: list[Detection]) -> "Track":
        """Creates a new track instance."""
        return Track(
            id=uuid4(),
            video_id=video_id,
            detections=[detection.id for detection in detections],
            thumbnail_id=_get_most_representative(detections).id,
        )

    def is_valid(self) -> bool:
        """Check if the track has enough detections to be tracked."""
        return len(self.detections) > 4


def _get_most_representative(detections: list[Detection]) -> Detection:
    """Find the most representative detection, first one by default."""
    return max(detections, key=lambda detection: detection.score())
