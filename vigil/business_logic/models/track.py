from dataclasses import dataclass
from uuid import UUID


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

    def is_valid(self) -> bool:
        """Check if the track has enough detections to be tracked."""
        return len(self.detections) > 4
