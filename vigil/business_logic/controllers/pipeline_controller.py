from vigil.business_logic.gateways.detection_store import DetectionStore
from vigil.business_logic.gateways.frame_repository import FrameRepository
from vigil.business_logic.gateways.video_reader import VideoReader
from vigil.business_logic.models.frame import Frame
from vigil.business_logic.models.video_source import VideoSource
from vigil.business_logic.services.detection_service import DetectionService
from vigil.business_logic.services.id_factory import IdFactory
from vigil.business_logic.use_cases.track_objects import TrackObjectsUseCase


class PipelineController:
    """Orchestrate the full read-detect-track pipeline over a video source."""

    def __init__(
        self,
        video_reader: VideoReader,
        frame_repository: FrameRepository,
        detection_service: DetectionService,
        detection_store: DetectionStore,
        track_use_case: TrackObjectsUseCase,
        batch_size: int,
    ) -> None:
        self._video_reader = video_reader
        self._frame_repository = frame_repository
        self._detection_service = detection_service
        self._detection_store = detection_store
        self._track_use_case = track_use_case
        self._batch_size = batch_size

    def execute(self, source: VideoSource) -> None:
        """Run the pipeline for a video source."""
        batch: list[Frame] = []

        for position, data in enumerate(self._video_reader.read(source)):
            frame = Frame(
                id=IdFactory.new_frame_id(video_id=source.video_id, position=position),
                video_id=source.video_id,
                position=position,
                data=data,
            )
            self._frame_repository.save(frame)
            batch.append(frame)

            if len(batch) == self._batch_size:
                self._flush(batch)
                batch = []

        if batch:
            self._flush(batch)

    def _flush(self, batch: list[Frame]) -> None:
        """Process a full batch of frames."""
        detections = self._detection_service.detect(batch)
        for detection in detections:
            self._detection_store.save(detection)

        for frame in batch:
            frame_detections = [d for d in detections if d.frame_id == frame.id]
            self._track_use_case.execute(video_id=frame.video_id, detections=frame_detections)
