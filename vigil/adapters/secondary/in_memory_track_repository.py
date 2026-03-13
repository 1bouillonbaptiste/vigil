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
