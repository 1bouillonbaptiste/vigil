from typing import Protocol
from uuid import UUID

from vigil.shared_kernel.models.image import Image


class CropProvider(Protocol):
    """Interface for retrieving cropped image data for a detection."""

    def get_by_detection(self, detection_id: UUID) -> Image:
        """Return the image crop associated with the given detection."""
        ...
