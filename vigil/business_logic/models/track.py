from dataclasses import dataclass, field, replace
from typing import NewType
from uuid import UUID

from vigil.business_logic.models.detection import Detection

TrackId = NewType("TrackId", UUID)
"""Track unique identifier."""

_GRACE_PERIOD: int = 5
"""Number of consecutive missed frames before a track is closed."""


@dataclass(frozen=True)
class Track:
    """Represent a single object instance over time."""

    id: TrackId
    """Track unique identifier."""

    video_id: UUID
    """Identifier of the video this track belongs to."""

    detections: tuple[Detection, ...]
    """Ordered, immutable sequence of detections associated with this track."""

    closed: bool = field(default=False)
    """Whether this track is closed (no longer updated)."""

    _missed_frames: int = field(default=0)
    """Consecutive frames for which this track had no matching detection."""

    def extend(self, detection: Detection) -> "Track":
        """Add detection to this track and reset missed-frame counter."""
        return replace(self, detections=(*self.detections, detection), _missed_frames=0)

    def miss(self) -> "Track":
        """Record a missed frame, closing the track after the grace period."""
        missed = self._missed_frames + 1
        return replace(self, _missed_frames=missed, closed=missed >= _GRACE_PERIOD)
