from vigil.business_logic.gateways.track_repository import TrackRepository
from vigil.business_logic.models.track import Track, TrackId


class InMemoryTrackRepository(TrackRepository):
    """Interface for storing `Track` instances in a repository."""

    def __init__(self):
        self._tracks: dict[TrackId, Track] = {}

    def save(self, track: Track) -> None:
        """Save `track` to the repository."""
        self._tracks[track.id] = track

    def get_by_id(self, track_id: TrackId) -> Track:
        """Get `track` from the repository."""
        return self._tracks[track_id]

    def list_open_tracks(self) -> list[Track]:
        """List all open tracks in the repository."""
        return [track for track in self._tracks.values() if not track.closed]
