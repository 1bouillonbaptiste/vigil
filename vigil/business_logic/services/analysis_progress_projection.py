from collections import defaultdict
from uuid import UUID

from vigil.business_logic.models.frame_analyzed import FrameAnalyzed


class AnalysisProgressProjection:
    """Subscribe to FrameAnalyzed events and maintain a frame count per video.

    Acts as a callable handler so it can be passed directly to
    DomainEventPublisher.subscribe().
    """

    def __init__(self) -> None:
        self._counts: dict[UUID, int] = defaultdict(int)

    def __call__(self, event: FrameAnalyzed) -> None:
        """Increment the frame count for the event's video."""
        self._counts[event.video_id] += 1

    def count(self, video_id: UUID) -> int:
        """Return the number of analyzed frames for the given video."""
        return self._counts[video_id]
