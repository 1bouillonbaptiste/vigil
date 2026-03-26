from dataclasses import dataclass
from uuid import UUID

from vigil.shared_kernel.models.domain_event import DomainEvent


@dataclass(frozen=True)
class FrameAnalyzed(DomainEvent):
    """Event to indicate that a frame was analyzed."""

    video_id: UUID
    """Video id where the frame come from."""

    frame_position: int
    """Position of the frame in the video."""
