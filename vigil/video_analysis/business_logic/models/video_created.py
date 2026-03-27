from dataclasses import dataclass
from uuid import UUID

from vigil.shared_kernel.models.domain_event import DomainEvent


@dataclass(frozen=True)
class VideoCreated(DomainEvent):
    """Event to indicate that a video has been created."""

    video_id: UUID
    """Id of the created video."""

    total_frames: int
    """Total number of frames in the video."""
