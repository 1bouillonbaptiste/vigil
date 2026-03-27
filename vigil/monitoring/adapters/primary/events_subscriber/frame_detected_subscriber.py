import dataclasses

from vigil.monitoring.business_logic.gateways.analysis_job_repository import AnalysisJobRepository
from vigil.shared_kernel.gateways.domain_event_publisher import DomainEventPublisher
from vigil.video_analysis.business_logic.models.frame_detected import FrameDetected


class FrameDetectedSubscriber:
    """Wire FrameDetected events to the AnalysisJobRepository."""

    def __init__(self, publisher: DomainEventPublisher, repository: AnalysisJobRepository) -> None:
        self._publisher = publisher
        self._repository = repository

    def subscribe(self) -> None:
        """Subscribe to FrameDetected events."""
        self._publisher.subscribe(self._on_frame_detected)

    def _on_frame_detected(self, event: FrameDetected) -> None:
        job = self._repository.get_by_id(event.video_id)
        if event.frame_position > job.last_frame_position:
            self._repository.update(dataclasses.replace(job, last_frame_position=event.frame_position))
