import dataclasses

from vigil.monitoring.business_logic.gateways.analysis_job_repository import AnalysisJobRepository
from vigil.shared_kernel.gateways.domain_event_publisher import DomainEventPublisher
from vigil.video_analysis.business_logic.models.tracking_finished import TrackingFinished


class TrackingFinishedSubscriber:
    """Wire TrackingFinished events to the AnalysisJobRepository."""

    def __init__(self, publisher: DomainEventPublisher, repository: AnalysisJobRepository) -> None:
        self._publisher = publisher
        self._repository = repository

    def subscribe(self) -> None:
        """Subscribe to TrackingFinished events."""
        self._publisher.subscribe(self._on_tracking_finished)

    def _on_tracking_finished(self, event: TrackingFinished) -> None:
        job = self._repository.get_by_id(event.video_id)
        self._repository.update(dataclasses.replace(job, analyzed_frames=job.total_frames))
