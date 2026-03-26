from dataclasses import dataclass
from typing import NewType
from uuid import UUID

from vigil.video_analysis.business_logic.models.detection import Detection

TrackId = NewType("TrackId", UUID)
"""Track unique identifier."""


@dataclass(frozen=True)
class Track:
    """Represent a single object instance over time."""

    id: TrackId
    """Track unique identifier."""

    video_id: UUID
    """Identifier of the video this track belongs to."""

    detections: tuple[Detection, ...]
    """Ordered, immutable sequence of detections associated with this track."""
