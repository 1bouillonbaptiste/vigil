from uuid import UUID

from vigil.business_logic.gateways.detection_repository import DetectionRepository
from vigil.business_logic.models.detection import Detection


class InMemoryDetectionRepository(DetectionRepository):
    """Store tracks in memory."""

    def __init__(self) -> None:
        self._detections: list[Detection] = []

    def get_by_video_id(self, video_id: UUID) -> list[Detection]:
        """Retrieves the detections associated to a video."""
        detections: list[Detection] = []
        for detection in self._detections:
            if detection.video_id == video_id:
                detections.append(detection)
        return detections

    def add(self, detection: Detection) -> None:
        """Add a detection to the detection repository."""
        self._detections.append(detection)
