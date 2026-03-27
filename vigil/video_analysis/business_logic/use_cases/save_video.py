from uuid import UUID

from vigil.shared_kernel.gateways.domain_event_publisher import DomainEventPublisher
from vigil.video_analysis.business_logic.gateways.video_repository import VideoRepository
from vigil.video_analysis.business_logic.models.video_created import VideoCreated
from vigil.video_analysis.business_logic.models.video_source import VideoSource
from vigil.video_analysis.business_logic.services.id_factory import IdFactory


class SaveVideoUseCase:
    """Persist raw video bytes and return the corresponding video_id."""

    def __init__(self, video_repository: VideoRepository, domain_event_publisher: DomainEventPublisher) -> None:
        self._video_repository = video_repository
        self._domain_event_publisher = domain_event_publisher

    def execute(self, source: VideoSource, data: bytes) -> UUID:
        """Save the video and emit VideoCreated."""
        self._video_repository.save(source, data)
        video_id = IdFactory.new_video_id(source)
        total_frames = self._video_repository.frame_count(video_id)
        self._domain_event_publisher.publish(VideoCreated(video_id=video_id, total_frames=total_frames))
        return video_id
