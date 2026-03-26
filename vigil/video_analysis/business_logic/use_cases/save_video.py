from uuid import UUID

from vigil.video_analysis.business_logic.gateways.video_repository import VideoRepository
from vigil.video_analysis.business_logic.models.video_source import VideoSource
from vigil.video_analysis.business_logic.services.id_factory import IdFactory


class SaveVideoUseCase:
    """Persist raw video bytes and return the corresponding video_id."""

    def __init__(self, video_repository: VideoRepository) -> None:
        self._video_repository = video_repository

    def execute(self, source: VideoSource, data: bytes) -> UUID:
        """Save the video and return its deterministic id."""
        self._video_repository.save(source, data)
        return IdFactory.new_video_id(source)
