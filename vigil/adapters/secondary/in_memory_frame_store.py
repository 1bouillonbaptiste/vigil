from uuid import UUID

from vigil.business_logic.gateways.frame_store import FrameStore
from vigil.business_logic.models.frame import FrameData, VideoFrame


class InMemoryFrameStore(FrameStore):
    """Implement frame store in memory."""

    def __init__(self) -> None:
        self._data: dict[UUID, FrameData] = {}

    def store(self, frame: VideoFrame, data: FrameData) -> None:
        """Store frame in memory."""
        self._data[frame.id] = data

    def load(self, frame: VideoFrame) -> FrameData:
        """Load frame from memory."""
        return self._data[frame.id]
