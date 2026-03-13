from uuid import UUID

from vigil.business_logic.gateways.track_repository import TrackRepository
from vigil.business_logic.models.track import Track


class InMemoryTrackRepository(TrackRepository):
    """Store tracks in memory."""

    def __init__(self) -> None:
        self._tracks: dict[UUID, Track] = {}

    def get_by_id(self, track_id: UUID) -> Track:
        """Retrieves a track by its UUID."""
        if track_id not in self._tracks:
            raise KeyError(f"Track with ID {track_id} not found.")
        return self._tracks[track_id]

    def save(self, track: Track) -> None:
        """Save a track to the repository."""
        self._tracks[track.video_id] = track

    def list_video_tracks(self, video_id: UUID) -> list[Track]:
        """Retrieves a list of tracks for a video."""
        tracks: list[Track] = []
        for track in self._tracks.values():
            if track.video_id == video_id:
                tracks.append(track)
        return tracks
