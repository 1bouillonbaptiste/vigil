from typing import Protocol

from vigil.business_logic.models.detection import Detection
from vigil.business_logic.models.track import Track


class Tracker(Protocol):
    """Abstract strategy for tracking objects."""
    def track(self) -> list[Track]:
        """Aggregate detections to tracks."""
        ...