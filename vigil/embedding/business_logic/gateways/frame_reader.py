from typing import Protocol
from uuid import UUID

from vigil.shared_kernel.models.bounding_box import BoundingBox
from vigil.shared_kernel.models.image import Image


class FrameReader(Protocol):
    """Read a cropped image region from a stored video."""

    def read_crop(self, video_id: UUID, frame_position: int, bbox: BoundingBox) -> Image:
        """Return the image crop at `frame_position` clipped to `bbox`."""
        ...
