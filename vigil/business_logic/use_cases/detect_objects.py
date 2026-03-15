from uuid import UUID, uuid4

from vigil.business_logic.gateways.detection_model import DetectionModel
from vigil.business_logic.gateways.detection_repository import DetectionRepository
from vigil.business_logic.gateways.frame_repository import FrameRepository
from vigil.business_logic.models.detection import Detection


class DetectObjectsUseCase:
    """Use case for detecting objects in frames."""

    def __init__(
        self,
        frame_repository: FrameRepository,
        detection_model: DetectionModel,
        detection_repository: DetectionRepository,
    ):
        self._frame_repository = frame_repository
        self._detection_model = detection_model
        self._detection_repository = detection_repository

    def execute(self, frame_id: UUID) -> None:
        """Execute the use case on a single frame."""
        frame = self._frame_repository.get_by_id(frame_id)
        bboxes = self._detection_model.detect(frame)
        for bbox in bboxes:
            self._detection_repository.save(
                Detection(
                    id=uuid4(),
                    video_id=frame.video_id,
                    frame_position=frame.position,
                    bbox=bbox,
                )
            )
