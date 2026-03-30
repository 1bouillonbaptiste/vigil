from dataclasses import dataclass
from uuid import UUID

from vigil.shared_kernel.models.bounding_box import BoundingBox
from vigil.shared_kernel.models.domain_event import DomainEvent


@dataclass(frozen=True)
class TrackedDetection:
    """Detection data carried by the TrackIdentified event."""

    id: UUID
    """Detection unique identifier."""
    frame_position: int
    """Position of the frame the detection was observed in."""
    bbox: BoundingBox
    """Bounding box of the detection in that frame."""


@dataclass(frozen=True)
class TrackIdentified(DomainEvent):
    """Event emitted when a new track has been identified."""

    video_id: UUID
    """Identifier of the video this track belongs to."""
    track_id: UUID
    """Identifier of the track."""
    detections: tuple[TrackedDetection, ...]
    """Ordered sequence of detections belonging to this track."""
