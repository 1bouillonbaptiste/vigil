from dataclasses import dataclass
from uuid import UUID

from vigil.monitoring.business_logic.gateways.analysis_job_repository import AnalysisJobRepository


@dataclass(frozen=True)
class AnalysisStatus:
    """Progress report for a video analysis job."""

    analyzed_frames: int
    total_frames: int


class GetAnalysisStatusUseCase:
    """Return the current progress of a video analysis job."""

    def __init__(self, analysis_job_repository: AnalysisJobRepository) -> None:
        self._repository = analysis_job_repository

    def execute(self, video_id: UUID) -> AnalysisStatus:
        """Return how many frames have been analyzed out of the total."""
        job = self._repository.get_by_id(video_id)
        return AnalysisStatus(analyzed_frames=job.analyzed_frames, total_frames=job.total_frames)
