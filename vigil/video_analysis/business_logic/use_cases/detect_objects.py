from uuid import UUID

from vigil.shared_kernel.gateways.domain_event_publisher import DomainEventPublisher
from vigil.video_analysis.business_logic.gateways.video_repository import VideoRepository
from vigil.video_analysis.business_logic.models.detection import Detection
from vigil.video_analysis.business_logic.models.frame import Frame
from vigil.video_analysis.business_logic.models.frame_detected import FrameDetected
from vigil.video_analysis.business_logic.services.detection_service import DetectionService
from vigil.video_analysis.business_logic.services.id_factory import IdFactory


class DetectObjectsUseCase:
    """Detect objects across all frames of a video.

    Frames are fed to the detection service in batches. It is the standard
    inference pattern for deep-learning models, where batching amortizes GPU
    overhead. A FrameDetected event is published for each processed frame.
    """

    def __init__(
        self,
        domain_event_publisher: DomainEventPublisher,
        video_repository: VideoRepository,
        detection_service: DetectionService,
        batch_size: int,
    ) -> None:
        self._domain_event_publisher = domain_event_publisher
        self._video_repository = video_repository
        self._detection_service = detection_service
        self._batch_size = batch_size

    def execute(self, video_id: UUID) -> list[Detection]:
        """Run the detection on a single video."""
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
                self._flush(batch, all_detections)
                batch = []

        if batch:
            self._flush(batch, all_detections)

        return all_detections

    def _flush(self, batch: list[Frame], all_detections: list[Detection]) -> None:
        detections = self._detection_service.detect(batch)
        all_detections.extend(detections)
        for frame in batch:
            self._domain_event_publisher.publish(FrameDetected(video_id=frame.video_id, frame_position=frame.position))
