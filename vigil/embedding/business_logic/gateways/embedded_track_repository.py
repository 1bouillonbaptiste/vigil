from typing import Protocol

from vigil.embedding.business_logic.models.embedded_track import EmbeddedTrack


class EmbeddedTrackRepository(Protocol):
    """Interface for storing `EmbeddedTrack` instances in a repository."""

    def save(self, track: EmbeddedTrack) -> None:
        """Save a track to the repository."""
        ...

    def list_tracks(self) -> list[EmbeddedTrack]:
        """List all embedded tracks."""
        ...
