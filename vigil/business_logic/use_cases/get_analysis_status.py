from dataclasses import dataclass
from uuid import UUID

from vigil.business_logic.gateways.video_repository import VideoRepository
from vigil.business_logic.services.analysis_progress_projection import AnalysisProgressProjection


@dataclass(frozen=True)
class AnalysisStatus:
    """Progress report for a video analysis job."""

    analysed_frames: int
    """Number of frames processed so far."""

    total_frames: int
    """Total number of frames in the video."""


class GetAnalysisStatusUseCase:
    """Return the progress of a video analysis job."""

    def __init__(self, progress_projection: AnalysisProgressProjection, video_repository: VideoRepository) -> None:
        self._progress_projection = progress_projection
        self._video_repository = video_repository

    def execute(self, video_id: UUID) -> AnalysisStatus:
        """Return how many frames have been analysed out of the total."""
        return AnalysisStatus(
            analysed_frames=self._progress_projection.count(video_id),
            total_frames=self._video_repository.frame_count(video_id),
        )
