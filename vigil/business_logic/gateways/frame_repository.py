from typing import Protocol
from uuid import UUID

from vigil.business_logic.models.frame import Frame


class FrameRepository(Protocol):
    """Interface for storing `Frame` instances in a repository."""

    def get_by_id(self, frame_id: UUID) -> Frame:
        """Retrieve a frame by its id."""
        ...

    def get_by_video_id(self, video_id: UUID) -> list[Frame]:
        """List all the frames belonging to a video."""
        ...

    def save(self, frame: Frame) -> None:
        """Save a frame to the repository."""
        ...
