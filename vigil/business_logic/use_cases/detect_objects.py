import uuid
from uuid import UUID

from vigil.business_logic.gateways.detection_repository import DetectionRepository
from vigil.business_logic.gateways.frame_repository import FrameRepository
from vigil.business_logic.models.detection import BoundingBox, Detection


class DetectObjectsUseCase:
    """Use case for detecting bboxes in frames."""

    def __init__(self, frame_repository: FrameRepository, detection_repository: DetectionRepository):
        self._frame_repository = frame_repository
        self._detection_repository = detection_repository

    def execute(self, frame_id: UUID):
        """Execute the use case on a single frame."""
        frame = self._frame_repository.get_by_id(frame_id)
        self._detection_repository.save(
            Detection(
                id=uuid.uuid4(),
                video_id=frame.video_id,
                frame_index=frame.position,
                bbox=BoundingBox(center_x=0, center_y=0, width=1, height=1, confidence=0.5, label="people"),
            )
        )
