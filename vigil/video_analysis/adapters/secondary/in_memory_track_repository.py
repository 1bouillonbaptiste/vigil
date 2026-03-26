from uuid import UUID

from vigil.video_analysis.business_logic.gateways.track_repository import TrackRepository
from vigil.video_analysis.business_logic.models.track import Track, TrackId


class InMemoryTrackRepository(TrackRepository):
    """In-memory implementation of TrackRepository."""

    def __init__(self):
        self._tracks: dict[TrackId, Track] = {}

    def save(self, track: Track) -> None:
        """Save `track` to the repository."""
        self._tracks[track.id] = track

    def get_by_id(self, track_id: TrackId) -> Track:
        """Get `track` from the repository."""
        return self._tracks[track_id]

    def list_by_video_id(self, video_id: UUID) -> list[Track]:
        """List all tracks for a given video."""
        return [t for t in self._tracks.values() if t.video_id == video_id]

    def list_all(self) -> list[Track]:
        """List all tracks."""
        return list(self._tracks.values())
