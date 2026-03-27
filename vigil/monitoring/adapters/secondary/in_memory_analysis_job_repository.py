from uuid import UUID

from vigil.monitoring.business_logic.exceptions import VideoNotFoundError
from vigil.monitoring.business_logic.gateways.analysis_job_repository import AnalysisJobRepository
from vigil.monitoring.business_logic.models.analysis_job import AnalysisJob


class InMemoryAnalysisJobRepository(AnalysisJobRepository):
    """In-memory implementation of AnalysisJobRepository."""

    def __init__(self) -> None:
        self._jobs: dict[UUID, AnalysisJob] = {}

    def create(self, job: AnalysisJob) -> None:
        """Persist a new analysis job."""
        self._jobs[job.video_id] = job

    def get_by_id(self, video_id: UUID) -> AnalysisJob:
        """Return the job for the given video.

        Raises VideoNotFoundError if not found.
        """
        try:
            return self._jobs[video_id]
        except KeyError as err:
            raise VideoNotFoundError(video_id) from err

    def update(self, job: AnalysisJob) -> None:
        """Replace the stored job with the given one."""
        self._jobs[job.video_id] = job
