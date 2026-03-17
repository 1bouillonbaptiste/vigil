from vigil.business_logic.gateways.frame_repository import FrameRepository
from vigil.business_logic.gateways.frame_store import FrameStore
from vigil.business_logic.gateways.video_reader import VideoReader
from vigil.business_logic.models.frame import VideoFrame
from vigil.business_logic.models.video_source import VideoSource
from vigil.business_logic.services.id_factory import IdFactory


class IngestVideoUseCase:
    """Ingest a video."""

    def __init__(self, video_reader: VideoReader, frame_store: FrameStore, frame_repository: FrameRepository) -> None:
        self._video_reader = video_reader
        self._frame_store = frame_store
        self._frame_repository = frame_repository

    def execute(self, source: VideoSource) -> None:
        """Execute the video ingestion."""
        for position, data in enumerate(self._video_reader.read(source)):
            new_frame = VideoFrame(
                id=IdFactory.new_frame_id(video_id=source.video_id, position=position),
                video_id=source.video_id,
                position=position,
            )
            self._frame_repository.save(new_frame)
            self._frame_store.store(frame=new_frame, data=data)
