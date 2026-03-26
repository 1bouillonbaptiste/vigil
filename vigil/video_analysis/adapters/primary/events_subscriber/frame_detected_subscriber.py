from vigil.shared_kernel.gateways.domain_event_publisher import DomainEventPublisher
from vigil.video_analysis.business_logic.gateways.analysis_progression_projection import AnalysisProgressionProjection
from vigil.video_analysis.business_logic.models.frame_detected import FrameDetected


class FrameDetectedSubscriber:
    """Wire FrameDetected events to the AnalysisProgressionProjection."""

    def __init__(self, publisher: DomainEventPublisher, analysis_progression: AnalysisProgressionProjection) -> None:
        self._publisher = publisher
        self._analysis_progression = analysis_progression

    def subscribe(self) -> None:
        """Subscribe to events published."""
        self._publisher.subscribe(self._on_frame_detected)

    def _on_frame_detected(self, event: FrameDetected) -> None:
        self._analysis_progression.increment(event.video_id)
