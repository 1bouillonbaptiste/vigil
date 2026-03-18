from vigil.business_logic.gateways.frame_repository import FrameRepository
from vigil.business_logic.gateways.video_reader import VideoReader
from vigil.business_logic.models.frame import Frame
from vigil.business_logic.models.video_source import VideoSource
from vigil.business_logic.services.id_factory import IdFactory


class IngestVideoUseCase:
    """Ingest a video."""

    def __init__(self, video_reader: VideoReader, frame_repository: FrameRepository) -> None:
        self._video_reader = video_reader
        self._frame_repository = frame_repository

    def execute(self, source: VideoSource) -> None:
        """Execute the video ingestion."""
        for position, data in enumerate(self._video_reader.read(source)):
            self._frame_repository.save(
                Frame(
                    id=IdFactory.new_frame_id(video_id=source.video_id, position=position),
                    video_id=source.video_id,
                    position=position,
                    data=data,
                )
            )
