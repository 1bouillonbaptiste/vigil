from typing import Protocol
from uuid import UUID


class AnalysisProgressionProjection(Protocol):
    """Represent the progression of the video analysis.

    This protocol implements both read and write operations, breaking CQRS
    purity. Avoid an extra indirection because our domain has exactly one reader
    and one writer.
    """

    def increment(self, video_id: UUID) -> None:
        """Increment the progression counter of the given video."""

    def count(self, video_id: UUID) -> int:
        """Get the progression of the given video."""
        ...
