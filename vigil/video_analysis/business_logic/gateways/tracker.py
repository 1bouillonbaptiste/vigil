from typing import Protocol

from vigil.video_analysis.business_logic.models.detection import Detection
from vigil.video_analysis.business_logic.models.track import Track


class Tracker(Protocol):
    """Interface for trackers.

    Each tracker implementation is responsible to match new detections to
    existing tracks.
    """

    def update(self, tracks: list[Track], detections: list[Detection]) -> list[tuple[Track, Detection]]:
        """Assign new detections to existing open tracks.

        Returns a list of (track, detection) pairs. Each pair means the
        detection continues the track. Tracks absent from the result missed this
        frame; detections absent from the result are orphans that start new
        tracks.
        """
        ...
