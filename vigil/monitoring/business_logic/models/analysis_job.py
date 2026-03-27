from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True)
class AnalysisJob:
    """Video analysis job tracked by the monitoring context."""

    video_id: UUID
    total_frames: int
    last_frame_position: int = field(default=-1)

    @property
    def analyzed_frames(self) -> int:
        """Number of frames analyzed so far (position is 0-indexed)."""
        return self.last_frame_position + 1
