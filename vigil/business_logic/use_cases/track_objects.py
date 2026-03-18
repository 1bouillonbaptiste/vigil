from uuid import UUID

from vigil.business_logic.gateways.detection_repository import DetectionRepository
from vigil.business_logic.gateways.track_repository import TrackRepository
from vigil.business_logic.gateways.tracker import Tracker
from vigil.business_logic.models.detection import Detection
from vigil.business_logic.models.frame import FrameId
from vigil.business_logic.models.track import Track
from vigil.business_logic.services.id_factory import IdFactory


class TrackObjectsUseCase:
    """Use case for tracking objects across frames."""

    def __init__(self, detection_repository: DetectionRepository, track_repository: TrackRepository, tracker: Tracker):
        self._detection_repository = detection_repository
        self._track_repository = track_repository
        self._tracker = tracker

    def execute(self, frame_id: FrameId, video_id: UUID) -> None:
        """Update existing tracks on a frame detections."""
        detections = self._detection_repository.get_by_frame_id(frame_id)
        open_tracks = self._track_repository.list_open_tracks(video_id)
        matches = self._tracker.update(tracks=open_tracks, detections=detections)

        for detection in self._orphan_detections(matches, detections):
            self._track_repository.save(Track(id=IdFactory.new_track_id(detection), detections=[detection]))

        for track, detection in matches:
            self._track_repository.save(track.extend(detection))

        for track in self._missed_tracks(matches, open_tracks):
            self._track_repository.save(track.miss())

    @staticmethod
    def _orphan_detections(matches: list[tuple[Track, Detection]], detections: list[Detection]) -> list[Detection]:
        """Detections not matched to any existing track."""
        matched = {detection for _, detection in matches}
        return [d for d in detections if d not in matched]

    @staticmethod
    def _missed_tracks(matches: list[tuple[Track, Detection]], open_tracks: list[Track]) -> list[Track]:
        """Open tracks that received no matching detection this frame."""
        matched_ids = {track.id for track, _ in matches}
        return [t for t in open_tracks if t.id not in matched_ids]
