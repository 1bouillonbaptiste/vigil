from uuid import UUID, uuid4

from vigil.business_logic.gateways.detection_repository import DetectionRepository
from vigil.business_logic.gateways.frame_repository import FrameRepository
from vigil.business_logic.models.detection import BoundingBox, ClassLabel, Detection
from vigil.business_logic.models.frame import VideoFrame


class DetectionFactory:
    """Factory that creates fake detections for testing purpose.

    At creation, the factory saves the detection in a repo if provided.
    At creation, the factory creates and saves a new frame in a repo if provided.
    """

    def __init__(
        self, frame_repository: FrameRepository | None = None, detection_repository: DetectionRepository | None = None
    ) -> None:
        self._frame_repository = frame_repository
        self._detection_repository = detection_repository

        self._frame_registry = _FrameRegistry()
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
        frame = self._get_frame(video_id=self._video_id, position=at_position)
        detection = Detection(
            id=uuid4(),
            frame_id=frame.id,
            bbox=bbox or self._default_bbox,
        )
        if self._detection_repository is not None:
            self._detection_repository.save(detection)
        return detection

    def _get_frame(self, video_id: UUID, position: int) -> VideoFrame:
        """Retrieve a frame, optionally create it."""
        frame = self._frame_registry.find(video_id=video_id, position=position)
        if frame is None:
            frame = VideoFrame(
                id=uuid4(),
                video_id=video_id,
                position=position,
            )
            self._frame_registry.register(frame)
            if self._frame_repository is not None:
                self._frame_repository.save(frame)
        return frame


class _FrameRegistry:
    """Store factory video frames."""

    def __init__(self) -> None:
        self._registry: dict[tuple[UUID, int], VideoFrame] = {}  # VideoId, frame_position -> VideoFrame

    def find(self, video_id: UUID, position: int) -> VideoFrame | None:
        """Find a video frame by its position."""
        return self._registry.get((video_id, position))

    def register(self, frame: VideoFrame) -> None:
        """Register a video frame."""
        self._registry[(frame.video_id, frame.position)] = frame
