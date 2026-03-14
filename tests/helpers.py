from uuid import UUID, uuid4

from vigil.business_logic.models.detection import BoundingBox, Detection


class DetectionFactory:
    """Factory that creates fake detections for testing purpose.

    The video is constant across all detections.
    The factory generates a detection per frame, starting at frame 0.
    """

    def __init__(self, video_id: UUID, starting_frame: int = 0) -> None:
        self._video_id = video_id
        self._frame_idx = starting_frame
        self._default_bbox = BoundingBox(center_x=100, center_y=50, width=10, height=30)

    def create(self, bbox: BoundingBox | None = None, confidence: float = 0.8) -> Detection:
        """Create a new detection."""
        detection = Detection(
            id=uuid4(),
            video_id=self._video_id,
            bbox=bbox or self._default_bbox,
            confidence=confidence,
            frame_index=self._frame_idx,
        )
        self._frame_idx += 1
        return detection
