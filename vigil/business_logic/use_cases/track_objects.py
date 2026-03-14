import uuid
from uuid import UUID

from vigil.business_logic.gateways.detection_repository import DetectionRepository
from vigil.business_logic.gateways.track_repository import TrackRepository
from vigil.business_logic.gateways.tracker import Tracker
from vigil.business_logic.models.detection import Detection
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
            if not instance_detections:
                continue
            new_track = Track(
                id=uuid.uuid4(),
                video_id=video_id,
                detections=[detection.id for detection in instance_detections],
                thumbnail_id=_get_most_representative(instance_detections).id,
            )
            if new_track.is_valid():
                self._tracks_repository.save(new_track)


def _get_most_representative(detections: list[Detection]) -> Detection:
    """Find the most representative detection, first one by default."""
    return max(detections, key=lambda detection: detection.score())
