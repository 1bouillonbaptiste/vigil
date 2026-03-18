from vigil.business_logic.gateways.detection_repository import DetectionRepository
from vigil.business_logic.gateways.track_repository import TrackRepository
from vigil.business_logic.gateways.tracker import Tracker
from vigil.business_logic.models.frame import FrameId
from vigil.business_logic.models.track import Track
from vigil.business_logic.services.id_factory import IdFactory


class TrackObjectsUseCase:
    """Use case for tracking objects across frames."""

    def __init__(self, detection_repository: DetectionRepository, track_repository: TrackRepository, tracker: Tracker):
        self._detection_repository = detection_repository
        self._track_repository = track_repository
        self._tracker = tracker

    def execute(self, frame_id: FrameId):
        """Update existing tracks on a frame detections."""
        detections = self._detection_repository.get_by_frame_id(frame_id)
        tracks = self._track_repository.list_tracks()
        assignments = self._tracker.update(tracks=tracks, detections=detections)

        for detection in assignments.orphan_detections:
            new_track = Track(id=IdFactory.new_track_id(detection), detections=[detection])
            self._track_repository.save(new_track)

        for track, detection in assignments.matches:
            updated_track = track.extend(detection)
            self._track_repository.save(updated_track)
