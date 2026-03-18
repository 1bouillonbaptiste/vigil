from dataclasses import dataclass, field, replace
from typing import NewType
from uuid import UUID

from vigil.business_logic.models.detection import Detection

TrackId = NewType("TrackId", UUID)
"""Track unique identifier."""


@dataclass(frozen=True)
class Track:
    """Represent a single object instance over time."""

    id: TrackId
    """Track unique identifier."""

    detections: list[Detection]
    """Detections associated with this track."""

    closed: bool = field(default=False)
    """Whether this track is closed (no longer updated)."""

    def extend(self, detection: Detection) -> "Track":
        """Add a new detection to this track."""
        return replace(self, detections=[*self.detections, detection])

    def close(self) -> "Track":
        """Close this track."""
        return replace(self, closed=True)
