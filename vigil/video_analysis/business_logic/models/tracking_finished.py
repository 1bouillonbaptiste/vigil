from dataclasses import dataclass
from uuid import UUID

from vigil.shared_kernel.models.domain_event import DomainEvent


@dataclass(frozen=True)
class TrackingFinished(DomainEvent):
    """Event emitted when all tracks have been identified for a video."""

    video_id: UUID
    """Video for which tracking has completed."""
