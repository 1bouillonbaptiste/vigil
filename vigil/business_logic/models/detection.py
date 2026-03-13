from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Detection:
    """Represent an instance detection object."""

    detection_id: UUID
    """Identifier of the detection."""

    video_id: UUID
    """Identifier of the video the detection comes from."""

    frame_index: int
    """Frame index of the detection in the video."""
