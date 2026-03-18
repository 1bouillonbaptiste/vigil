from uuid import UUID

from vigil.business_logic.gateways.frame_repository import FrameRepository
from vigil.business_logic.models.frame import VideoFrame


class InMemoryFrameRepository(FrameRepository):
    """Store frames in memory."""

    def __init__(self) -> None:
        self._frames: dict[UUID, VideoFrame] = {}

    def get_by_id(self, frame_id: UUID) -> VideoFrame:
        """Retrieves a frame by its id."""
        return self._frames[frame_id]

    def get_by_video_id(self, video_id: UUID) -> list[VideoFrame]:
        """Retrieves ordered frames from a video."""
        frames: list[VideoFrame] = []
        for frame in self._frames.values():
            if frame.video_id == video_id:
                frames.append(frame)
        return sorted(frames, key=lambda f: f.position)

    def save(self, frame: VideoFrame) -> None:
        """Stores a frame in memory."""
        self._frames[frame.id] = frame
