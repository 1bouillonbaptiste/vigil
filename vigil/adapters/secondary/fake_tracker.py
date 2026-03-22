from vigil.business_logic.gateways.tracker import Tracker
from vigil.business_logic.models.detection import Detection
from vigil.business_logic.models.track import Track


class FakeTracker(Tracker):
    """Tracker for testing purpose."""

    def update(self, tracks: list[Track], detections: list[Detection]) -> list[tuple[Track, Detection]]:
        """Don't match detection, one detection is a new track."""
        return []
