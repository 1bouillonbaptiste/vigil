from typing import Protocol

from vigil.business_logic.models.frame import FrameData, VideoFrame


class FrameStore(Protocol):
    """Store frame data."""

    def load(self, frame: VideoFrame) -> FrameData:
        """Load frame data."""
        ...

    def store(self, frame: VideoFrame, data: FrameData) -> None:
        """Store frame data."""
        ...
