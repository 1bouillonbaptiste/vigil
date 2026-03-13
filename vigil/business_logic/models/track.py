from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Track:
    """Represent a track."""

    id: UUID
    """Identifier of the track."""

    video_id: UUID
    """Identifier of the video where the track comes from."""
