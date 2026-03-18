from typing import Protocol

from vigil.business_logic.models.detection import Detection
from vigil.business_logic.models.track import Track, TrackAssignments


class Tracker(Protocol):
    """Interface for trackers.

    Each tracker implementation is responsible to match new detections to
    existing tracks.
    """

    def update(self, tracks: list[Track], detections: list[Detection]) -> TrackAssignments:
        """Assign new detections to existing tracks."""
        ...
