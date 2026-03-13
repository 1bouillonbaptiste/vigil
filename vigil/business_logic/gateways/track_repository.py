from typing import Protocol
from uuid import UUID

from vigil.business_logic.models.track import Track


class TrackRepository(Protocol):
    """Interface for storing `Track` instances in a repository."""

    def get_by_id(self, track_id: UUID) -> Track:
        """Retrieve a track by its `track_id`."""
        ...
