from uuid import UUID

from vigil.business_logic.gateways.frame_repository import FrameRepository
from vigil.business_logic.models.frame import VideoFrame


class InMemoryFrameRepository(FrameRepository):
    """Store frames in memory."""

    def __init__(self) -> None:
        self._frames: dict[UUID, VideoFrame] = {}

    def get_by_id(self, frame_id: UUID) -> VideoFrame:
        """Retrieves a frame by its id."""
        if frame_id not in self._frames:
            raise KeyError(f"Frame with ID {frame_id} not found.")
        return self._frames[frame_id]

    def save(self, frame: VideoFrame) -> None:
        """Stores a frame in memory."""
        self._frames[frame.id] = frame
