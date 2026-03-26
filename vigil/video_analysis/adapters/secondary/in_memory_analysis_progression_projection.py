from collections import defaultdict
from uuid import UUID

from vigil.video_analysis.business_logic.gateways.analysis_progression_projection import AnalysisProgressionProjection


class InMemoryAnalysisProgressionProjection(AnalysisProgressionProjection):
    """Implement the progression in memory."""

    _counter: dict[UUID, int]

    def __init__(self):
        self._counter: dict[UUID, int] = defaultdict(int)

    def increment(self, video_id: UUID) -> None:
        """Increment the counter."""
        self._counter[video_id] += 1

    def count(self, video_id: UUID) -> int:
        """Get the progression counter."""
        return self._counter[video_id]
