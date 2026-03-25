from dataclasses import dataclass
from uuid import UUID

from vigil.business_logic.models.domain_event import DomainEvent
from vigil.business_logic.models.frame import FrameId


@dataclass(frozen=True, kw_only=True)
class FrameAnalyzed(DomainEvent):
    """Emitted after a frame is analyzed."""

    video_id: UUID
    frame_id: FrameId
    position: int
