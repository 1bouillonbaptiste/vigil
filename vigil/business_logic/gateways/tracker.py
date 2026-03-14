from typing import Protocol

from vigil.business_logic.models.detection import Detection


class Tracker(Protocol):
    """Abstract strategy for tracking objects."""

    def track(self, detections: list[Detection]) -> list[list[Detection]]:
        """Aggregate detections as list of instances, an instance being a list of detections."""
        ...
