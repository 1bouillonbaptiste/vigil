from vigil.business_logic.gateways.frame_repository import FrameRepository
from vigil.business_logic.gateways.video_reader import VideoReader
from vigil.business_logic.models.video_source import VideoSource


class IngestVideoUseCase:
    """Ingest a video."""

    def __init__(self, video_reader: VideoReader, frame_repository: FrameRepository) -> None:
        self._video_reader = video_reader
        self._frame_repository = frame_repository

    def execute(self, source: VideoSource) -> None:
        """Execute the video ingestion."""
        for frame in self._video_reader.read(source):
            self._frame_repository.save(frame)
