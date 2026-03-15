from uuid import UUID

from vigil.business_logic.gateways.detection_model import DetectionModel
from vigil.business_logic.gateways.detection_repository import DetectionRepository
from vigil.business_logic.models.raw_frame import RawFrame


class DetectObjectsUseCase:
    """Detect objects in a single video frame and persist the results."""

    def __init__(
        self,
        detection_model: DetectionModel,
        detection_repository: DetectionRepository,
    ) -> None:
        self._detection_model = detection_model
        self._detection_repository = detection_repository

    def execute(self, frame: RawFrame, video_id: UUID) -> None:
        """Run inference on frame and save every detection to the repository."""
        detections = self._detection_model.detect(frame, video_id)
        for detection in detections:
            self._detection_repository.save(detection)
