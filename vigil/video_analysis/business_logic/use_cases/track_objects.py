from uuid import UUID

from vigil.shared_kernel.gateways.domain_event_publisher import DomainEventPublisher
from vigil.video_analysis.business_logic.gateways.track_repository import TrackRepository
from vigil.video_analysis.business_logic.gateways.tracker import Tracker
from vigil.video_analysis.business_logic.models.detection import Detection
from vigil.video_analysis.business_logic.models.track import Track
from vigil.video_analysis.business_logic.models.track_identified import TrackedDetection, TrackIdentified
from vigil.video_analysis.business_logic.services.id_factory import IdFactory


class TrackObjectsUseCase:
    """Track objects across a video's detections and persist each track."""

    def __init__(
        self,
        tracker: Tracker,
        track_repository: TrackRepository,
        domain_event_publisher: DomainEventPublisher,
    ) -> None:
        self._tracker = tracker
        self._track_repository = track_repository
        self._domain_event_publisher = domain_event_publisher

    def execute(self, video_id: UUID, detections: list[Detection]) -> None:
        """Group detections into tracks and emit TrackIdentified per track."""
        for sequence in self._tracker.track(detections):
            track = Track(
                id=IdFactory.new_track_id(sequence[0]),
                video_id=video_id,
                detections=tuple(sequence),
            )
            self._track_repository.save(track)
            self._domain_event_publisher.publish(
                TrackIdentified(
                    video_id=video_id,
                    track_id=track.id,
                    detections=tuple(
                        TrackedDetection(
                            id=d.id,
                            frame_position=d.frame_position,
                            bbox=d.prediction.bbox,
                        )
                        for d in sequence
                    ),
                )
            )
