from vigil.monitoring.business_logic.gateways.analysis_job_repository import AnalysisJobRepository
from vigil.monitoring.business_logic.models.analysis_job import AnalysisJob
from vigil.shared_kernel.gateways.domain_event_publisher import DomainEventPublisher
from vigil.video_analysis.business_logic.models.video_created import VideoCreated


class VideoCreatedSubscriber:
    """Wire VideoCreated events to the AnalysisJobRepository."""

    def __init__(self, publisher: DomainEventPublisher, repository: AnalysisJobRepository) -> None:
        self._publisher = publisher
        self._repository = repository

    def subscribe(self) -> None:
        """Subscribe to VideoCreated events."""
        self._publisher.subscribe(self._on_video_created)

    def _on_video_created(self, event: VideoCreated) -> None:
        self._repository.create(AnalysisJob(video_id=event.video_id, total_frames=event.total_frames))
