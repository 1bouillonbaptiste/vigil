from uuid import UUID

from vigil.video_analysis.business_logic.gateways.track_repository import TrackRepository
from vigil.video_analysis.business_logic.gateways.tracker import Tracker
from vigil.video_analysis.business_logic.models.detection import Detection
from vigil.video_analysis.business_logic.models.track import Track
from vigil.video_analysis.business_logic.services.id_factory import IdFactory


class TrackObjectsUseCase:
    """Track objects across a video's detections and persist each track."""

    def __init__(self, tracker: Tracker, track_repository: TrackRepository) -> None:
        self._tracker = tracker
        self._track_repository = track_repository

    def execute(self, video_id: UUID, detections: list[Detection]) -> None:
        """Group detections into tracks and save each one."""
        for sequence in self._tracker.track(detections):
            self._track_repository.save(
                Track(
                    id=IdFactory.new_track_id(sequence[0]),
                    video_id=video_id,
                    detections=tuple(sequence),
                )
            )
