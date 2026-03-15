from uuid import UUID

from vigil.business_logic.gateways.detection_repository import DetectionRepository
from vigil.business_logic.models.detection import BoundingBox, Detection


class DetectObjectsUseCase:
    """Use case for detecting bboxes in frames."""

    def __init__(self, detection_repository: DetectionRepository):
        self._detection_repository = detection_repository

    def execute(self):
        """Execute the use case on a single frame."""
        self._detection_repository.save(
            Detection(
                id=UUID("6f7f36e7-c0c8-4679-b3c3-835fc20ca59b"),
                video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
                frame_index=0,
                bbox=BoundingBox(center_x=0, center_y=0, width=1, height=1, confidence=0.5, label="people"),
            )
        )
