from uuid import UUID

from vigil.business_logic.gateways.detection_repository import DetectionRepository
from vigil.business_logic.gateways.frame_repository import FrameRepository
from vigil.business_logic.gateways.track_repository import TrackRepository
from vigil.business_logic.gateways.tracker import Tracker
from vigil.business_logic.models.detection import Detection
from vigil.business_logic.models.track import Track
from vigil.business_logic.services.id_factory import IdFactory


class TrackObjectsUseCase:
    """Use case for tracking objects across frames."""

    def __init__(
        self,
        frame_repository: FrameRepository,
        detection_repository: DetectionRepository,
        tracker: Tracker,
        track_repository: TrackRepository,
    ):
        self._frame_repository = frame_repository
        self._detection_repository = detection_repository
        self._tracker = tracker
        self._tracks_repository = track_repository

    def execute(self, video_id: UUID) -> None:
        """Execute the use case on a video."""
        detections = self._list_video_detections(video_id)
        instances = self._tracker.track(detections)
        for instance_detections in instances:
            if not instance_detections:
                continue
            track_id = IdFactory.new_track_id(video_id=video_id, detection_id=instance_detections[0].id)
            new_track = Track.create(track_id=track_id, video_id=video_id, detections=instance_detections)
            if new_track.is_valid():
                self._tracks_repository.save(new_track)

    def _list_video_detections(self, video_id: UUID) -> list[Detection]:
        """List all the detections belonging to a video."""
        frames = self._frame_repository.get_by_video_id(video_id=video_id)
        result: list[Detection] = []
        for frame in frames:
            result.extend(self._detection_repository.get_by_frame_id(frame.id))
        return result
