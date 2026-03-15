from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class VideoFrame:
    """Represent a video frame."""

    id: UUID
    """Frame unique identifier."""

    position: int
    """Position of the frame in the video."""

    video_id: UUID
    """Video identifier the frame comes from."""
