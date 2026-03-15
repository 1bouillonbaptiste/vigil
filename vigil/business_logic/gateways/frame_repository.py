from typing import Protocol
from uuid import UUID

from vigil.business_logic.models.frame import VideoFrame


class FrameRepository(Protocol):
    """Interface for storing `Frame` instances in a repository."""

    def get_by_id(self, frame_id: UUID) -> VideoFrame:
        """Retrieve a frame by its id."""
        ...
