from uuid import UUID

from vigil.business_logic.gateways.detection_model import DetectionModel
from vigil.business_logic.gateways.detection_repository import DetectionRepository
from vigil.business_logic.gateways.frame_repository import FrameRepository


class DetectObjectsUseCase:
    """Use case for detecting bboxes in frames."""

    def __init__(
        self,
        frame_repository: FrameRepository,
        detection_model: DetectionModel,
        detection_repository: DetectionRepository,
    ):
        self._frame_repository = frame_repository
        self._detection_model = detection_model
        self._detection_repository = detection_repository

    def execute(self, frame_id: UUID):
        """Execute the use case on a single frame."""
        frame = self._frame_repository.get_by_id(frame_id)
        detections = self._detection_model.detect(frame)
        for detection in detections:
            self._detection_repository.save(detection)
