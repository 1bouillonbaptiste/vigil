from uuid import UUID

from vigil.business_logic.gateways.detection_store import DetectionStore
from vigil.business_logic.models.detection import Detection


class InMemoryDetectionStore(DetectionStore):
    """Store detections in memory."""

    def __init__(self) -> None:
        self._detections: list[Detection] = []

    def get_by_frame_id(self, frame_id: UUID) -> list[Detection]:
        """Retrieves the detections associated to a frame."""
        return [d for d in self._detections if d.frame_id == frame_id]

    def save(self, detection: Detection) -> None:
        """Add a detection to the store."""
        self._detections.append(detection)

    def clear(self) -> None:
        """Clear all detections from the store."""
        self._detections.clear()
