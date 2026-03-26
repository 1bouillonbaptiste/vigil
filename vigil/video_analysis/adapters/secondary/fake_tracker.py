from vigil.video_analysis.business_logic.gateways.tracker import Tracker
from vigil.video_analysis.business_logic.models.detection import BoundingBox, Detection


class FakeTracker(Tracker):
    """Tracker for testing purposes.

    Groups detections by bounding box: detections sharing the same bbox
    across frames are considered the same object.
    """

    def track(self, detections: list[Detection]) -> list[list[Detection]]:
        """Group detections by bbox across frames."""
        groups: dict[BoundingBox, list[Detection]] = {}
        for d in sorted(detections, key=lambda d: d.frame_position):
            groups.setdefault(d.prediction.bbox, []).append(d)
        return list(groups.values())
