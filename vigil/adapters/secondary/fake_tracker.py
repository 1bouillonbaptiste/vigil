from vigil.business_logic.gateways.tracker import Tracker
from vigil.business_logic.models.detection import Detection
from vigil.business_logic.models.track import Track


class FakeTracker(Tracker):
    """Tracker for testing purpose.

    Matches a track to a detection when their bounding boxes are equal.
    """

    def update(self, tracks: list[Track], detections: list[Detection]) -> list[tuple[Track, Detection]]:
        """Match tracks to detections sharing the same bounding box."""
        return [
            (track, detection)
            for track in tracks
            for detection in detections
            if track.detections[-1].prediction.bbox == detection.prediction.bbox
        ]
