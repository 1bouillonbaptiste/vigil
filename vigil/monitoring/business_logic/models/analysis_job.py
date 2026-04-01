from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True)
class AnalysisJob:
    """Video analysis job tracked by the monitoring context."""

    video_id: UUID
    total_frames: int
    analyzed_frames: int = field(default=0)
