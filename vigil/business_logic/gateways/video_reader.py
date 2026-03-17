from collections.abc import Iterable
from typing import Protocol

from vigil.business_logic.models.frame import FrameData
from vigil.business_logic.models.video_source import VideoSource


class VideoReader(Protocol):
    """Interface for reading videos from a source."""

    def read(self, source: VideoSource) -> Iterable[FrameData]:
        """Read frames from a video."""
        ...
