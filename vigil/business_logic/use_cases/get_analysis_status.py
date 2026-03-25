from dataclasses import dataclass
from uuid import UUID

from vigil.business_logic.gateways.analysis_progression_projection import AnalysisProgressionProjection
from vigil.business_logic.gateways.video_repository import VideoRepository


@dataclass(frozen=True)
class AnalysisStatus:
    """Progress report for a video analysis job."""

    analyzed_frames: int
    """Number of frames processed so far."""

    total_frames: int
    """Total number of frames in the video."""


class GetAnalysisStatusUseCase:
    """Return the progress of a video analysis job."""

    def __init__(
        self,
        video_repository: VideoRepository,
        analysis_progression: AnalysisProgressionProjection,
    ) -> None:
        self._video_repository = video_repository
        self._analysis_progression = analysis_progression

    def execute(self, video_id: UUID) -> AnalysisStatus:
        """Return how many frames have been analyzed out of the total."""
        return AnalysisStatus(
            analyzed_frames=self._analysis_progression.count(video_id),
            total_frames=self._video_repository.frame_count(video_id),
        )
