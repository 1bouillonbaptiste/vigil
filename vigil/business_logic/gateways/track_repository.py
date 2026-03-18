from typing import Protocol
from uuid import UUID

from vigil.business_logic.models.track import Track, TrackId


class TrackRepository(Protocol):
    """Interface for storing `Track` instances in a repository."""

    def save(self, track: Track) -> None:
        """Save a track to the repository."""
        ...

    def get_by_id(self, track_id: TrackId) -> Track:
        """Get a track from the repository."""
        ...

    def list_open_tracks(self, video_id: UUID) -> list[Track]:
        """List all open tracks for a given video."""
        ...
