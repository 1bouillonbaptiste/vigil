from uuid import UUID

from vigil.business_logic.gateways.detection_repository import DetectionRepository
from vigil.business_logic.models.detection import Detection


class InMemoryDetectionRepository(DetectionRepository):
    """Store tracks in memory."""

    def __init__(self) -> None:
        self._detections: list[Detection] = []

    def get_by_frame_id(self, frame_id: UUID) -> list[Detection]:
        """Retrieves the detections associated to a frame."""
        detections: list[Detection] = []
        for detection in self._detections:
            if detection.frame_id == frame_id:
                detections.append(detection)
        return detections

    def save(self, detection: Detection) -> None:
        """Add a detection to the detection repository."""
        self._detections.append(detection)
