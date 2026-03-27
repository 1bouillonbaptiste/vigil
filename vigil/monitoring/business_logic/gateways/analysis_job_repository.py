from typing import Protocol
from uuid import UUID

from vigil.monitoring.business_logic.models.analysis_job import AnalysisJob


class AnalysisJobRepository(Protocol):
    """Interface for storing and retrieving analysis jobs."""

    def create(self, job: AnalysisJob) -> None:
        """Persist a new analysis job."""
        ...

    def get_by_id(self, video_id: UUID) -> AnalysisJob:
        """Return the job for the given video.

        Raises if not found.
        """
        ...

    def update(self, job: AnalysisJob) -> None:
        """Replace the stored job with the given one."""
        ...
