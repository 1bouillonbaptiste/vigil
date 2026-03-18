from dataclasses import dataclass, replace
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

    def extend(self, detection: Detection) -> "Track":
        """Add a new detection to this track."""
        return replace(self, detections=[*self.detections, detection])


@dataclass(frozen=True)
class TrackAssignments:
    """Store detections assigned to tracks."""

    orphan_detections: list[Detection]
    """Detections associated with no tracks."""

    matches: list[tuple[Track, Detection]]
    """Tracks with a matching detection."""
