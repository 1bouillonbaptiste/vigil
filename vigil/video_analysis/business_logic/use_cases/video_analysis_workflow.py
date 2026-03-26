from uuid import UUID

from vigil.shared_kernel.gateways.domain_event_publisher import DomainEventPublisher
from vigil.video_analysis.business_logic.gateways.video_repository import VideoRepository
from vigil.video_analysis.business_logic.models.frame import Frame
from vigil.video_analysis.business_logic.models.frame_analyzed import FrameAnalyzed
from vigil.video_analysis.business_logic.services.detection_service import DetectionService
from vigil.video_analysis.business_logic.services.id_factory import IdFactory
from vigil.video_analysis.business_logic.use_cases.track_objects import TrackObjectsUseCase


class VideoAnalysisWorkflow:
    """Track objects across a video.

    Orchestrates use cases and services to analyse a video source end-to-end.
    """

    def __init__(
        self,
        domain_event_publisher: DomainEventPublisher,
        video_repository: VideoRepository,
        detection_service: DetectionService,
        track_use_case: TrackObjectsUseCase,
        batch_size: int,
    ) -> None:
        self._domain_event_publisher = domain_event_publisher
        self._video_repository = video_repository
        self._detection_service = detection_service
        self._track_use_case = track_use_case
        self._batch_size = batch_size

    def execute(self, video_id: UUID) -> None:
        """Run the pipeline for the given video."""
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
                self._flush(batch)
                batch = []

        if batch:
            self._flush(batch)

    def _flush(self, batch: list[Frame]) -> None:
        """Process a full batch of frames."""
        detections = self._detection_service.detect(batch)
        for frame in batch:
            frame_detections = [d for d in detections if d.frame_id == frame.id]
            self._track_use_case.execute(video_id=frame.video_id, detections=frame_detections)
            self._domain_event_publisher.publish(
                event=FrameAnalyzed(video_id=frame.video_id, frame_position=frame.position)
            )
