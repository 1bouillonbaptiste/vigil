from vigil.embedding.business_logic.models.detection_ref import DetectionRef
from vigil.embedding.business_logic.use_cases.index_track import IndexTrackUseCase
from vigil.shared_kernel.gateways.domain_event_publisher import DomainEventPublisher
from vigil.video_analysis.business_logic.models.track_identified import TrackIdentified


class TrackIdentifiedSubscriber:
    """Index a track in the embedding context on TrackIdentified event."""

    def __init__(self, publisher: DomainEventPublisher, use_case: IndexTrackUseCase) -> None:
        self._publisher = publisher
        self._use_case = use_case

    def subscribe(self) -> None:
        """Register the handler with the event publisher."""
        self._publisher.subscribe(self._on_track_identified)

    def _on_track_identified(self, event: TrackIdentified) -> None:
        detection_refs = [
            DetectionRef(
                detection_id=d.id,
                frame_position=d.frame_position,
                bbox=d.bbox,
            )
            for d in event.detections
        ]
        self._use_case.execute(
            track_id=event.track_id,
            video_id=event.video_id,
            detections=detection_refs,
        )
