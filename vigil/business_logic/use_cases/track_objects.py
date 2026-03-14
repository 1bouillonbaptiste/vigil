import uuid
from uuid import UUID

from vigil.business_logic.gateways.detection_repository import DetectionRepository
from vigil.business_logic.gateways.track_repository import TrackRepository
from vigil.business_logic.gateways.tracker import Tracker
from vigil.business_logic.models.track import Track


class TrackObjectsUseCase:
    """Use case for tracking objects across frames."""

    def __init__(self, detection_repository: DetectionRepository, tracker: Tracker, track_repository: TrackRepository):
        self._detection_repository = detection_repository
        self._tracker = tracker
        self._tracks_repository = track_repository

    def execute(self, video_id: UUID) -> None:
        """Execute the use case on a video."""
        detections = self._detection_repository.get_by_video_id(video_id)
        instances = self._tracker.track(detections)
        for instance_detections in instances:
            new_track = Track(
                id=uuid.uuid4(),
                video_id=video_id,
                detections=[detection.detection_id for detection in instance_detections],
            )
            if new_track.is_valid():
                self._tracks_repository.save(new_track)
