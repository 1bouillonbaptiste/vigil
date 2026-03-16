from uuid import UUID, uuid4

from vigil.business_logic.gateways.detection_repository import DetectionRepository
from vigil.business_logic.models.detection import BoundingBox, ClassLabel, Detection


class DetectionFactory:
    """Factory that creates fake detections for testing purpose.

    A creation, the factory saves the detection in a repo if provided.
    """

    def __init__(self, detection_repository: DetectionRepository | None = None) -> None:
        self._detection_repository = detection_repository
        self._video_id: UUID | None = None
        self._default_bbox = BoundingBox(
            center_x=100, center_y=50, width=10, height=30, confidence=0.8, label=ClassLabel.PEOPLE
        )

    def with_video(self, video_id: UUID):
        """Switch the video instances are created."""
        self._video_id = video_id

    def with_default_bbox(self, bbox: BoundingBox):
        """Set the default bounding box."""
        self._default_bbox = bbox

    def create(self, at_position: int, bbox: BoundingBox | None = None) -> Detection:
        """Create a new detection."""
        if self._video_id is None or self._default_bbox is None:
            raise RuntimeError("Set video and bbox before creating new detection.")
        detection = Detection(
            id=uuid4(),
            frame_id=uuid4(),
            video_id=self._video_id,
            bbox=bbox or self._default_bbox,
            frame_position=at_position,
        )
        if self._detection_repository is not None:
            self._detection_repository.save(detection)
        return detection
