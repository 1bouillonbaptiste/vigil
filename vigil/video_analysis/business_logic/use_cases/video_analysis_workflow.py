from uuid import UUID

from vigil.shared_kernel.gateways.domain_event_publisher import DomainEventPublisher
from vigil.video_analysis.business_logic.gateways.track_repository import TrackRepository
from vigil.video_analysis.business_logic.gateways.tracker import Tracker
from vigil.video_analysis.business_logic.gateways.video_repository import VideoRepository
from vigil.video_analysis.business_logic.models.detection import Detection
from vigil.video_analysis.business_logic.models.frame import Frame
from vigil.video_analysis.business_logic.models.frame_detected import FrameDetected
from vigil.video_analysis.business_logic.models.track import Track
from vigil.video_analysis.business_logic.services.detection_service import DetectionService
from vigil.video_analysis.business_logic.services.id_factory import IdFactory


class VideoAnalysisWorkflow:
    """Track objects across a video.

    Phase 1 — Detection: reads frames in batches, runs the detection service,
    publishes a FrameDetected event per frame.

    Phase 2 — Tracking: passes all detections to the tracker in one call, then
    persists the resulting Track objects.
    """

    def __init__(
        self,
        domain_event_publisher: DomainEventPublisher,
        video_repository: VideoRepository,
        detection_service: DetectionService,
        tracker: Tracker,
        track_repository: TrackRepository,
        batch_size: int,
    ) -> None:
        self._domain_event_publisher = domain_event_publisher
        self._video_repository = video_repository
        self._detection_service = detection_service
        self._tracker = tracker
        self._track_repository = track_repository
        self._batch_size = batch_size

    def execute(self, video_id: UUID) -> None:
        """Run the detection + tracking pipeline for the given video."""
        all_detections: list[Detection] = []
        batch: list[Frame] = []

        for position, data in enumerate(self._video_repository.read(video_id)):
            frame = Frame(
                id=IdFactory.new_frame_id(video_id=video_id, position=position),
                video_id=video_id,
                position=position,
                data=data,
            )
            batch.append(frame)

            if len(batch) == self._batch_size:
                self._flush_detection(batch, all_detections)
                batch = []

        if batch:
            self._flush_detection(batch, all_detections)

        for sequence in self._tracker.track(all_detections):
            self._track_repository.save(
                Track(
                    id=IdFactory.new_track_id(sequence[0]),
                    video_id=video_id,
                    detections=tuple(sequence),
                )
            )

    def _flush_detection(self, batch: list[Frame], all_detections: list[Detection]) -> None:
        detections = self._detection_service.detect(batch)
        all_detections.extend(detections)
        for frame in batch:
            self._domain_event_publisher.publish(FrameDetected(video_id=frame.video_id, frame_position=frame.position))
