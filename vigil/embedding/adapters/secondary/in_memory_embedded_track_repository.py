from uuid import UUID

from vigil.embedding.business_logic.gateways.embedded_track_repository import EmbeddedTrackRepository
from vigil.embedding.business_logic.models.embedded_track import EmbeddedTrack


class InMemoryEmbeddedTrackRepository(EmbeddedTrackRepository):
    """In-memory implementation of EmbeddedTrackRepository."""

    def __init__(self) -> None:
        self._tracks: dict[UUID, EmbeddedTrack] = {}

    def save(self, track: EmbeddedTrack) -> None:
        """Save `track` to the repository."""
        self._tracks[track.id] = track

    def list_tracks(self) -> list[EmbeddedTrack]:
        """List all embedded tracks."""
        return list(self._tracks.values())
