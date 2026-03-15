from uuid import UUID, uuid4

from vigil.business_logic.models.detection import BoundingBox, ClassLabel, Detection


class DetectionFactory:
    """Factory that creates fake detections for testing purpose.

    The video is constant across all detections.
    The factory generates a detection per frame, starting at frame 0.
    """

    def __init__(self, video_id: UUID, starting_frame: int = 0) -> None:
        self._video_id = video_id
        self._frame_idx = starting_frame
        self._default_bbox = BoundingBox(
            center_x=100, center_y=50, width=10, height=30, confidence=0.8, label=ClassLabel.PEOPLE
        )

    def create(self, bbox: BoundingBox | None = None) -> Detection:
        """Create a new detection."""
        detection = Detection(
            id=uuid4(),
            video_id=self._video_id,
            bbox=bbox or self._default_bbox,
            frame_position=self._frame_idx,
        )
        self._frame_idx += 1
        return detection
