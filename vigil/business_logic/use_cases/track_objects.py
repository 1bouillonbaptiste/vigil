
from vigil.business_logic.gateways.track_repository import TrackRepository
from vigil.business_logic.gateways.tracker import Tracker


class TrackObjectsUseCase:
    """Use case for tracking objects across frames."""

    def __init__(self, tracker: Tracker, track_repository: TrackRepository):
        self._tracker = tracker
        self._tracks_repository = track_repository

    def execute(self) -> None:
        """Execute the use case on a video."""
        tracks = self._tracker.track()
        for track in tracks:
            if track.is_valid():
                self._tracks_repository.save(track)
