from typing import Protocol
from uuid import UUID

import numpy as np
import numpy.typing as npt


class CropProvider(Protocol):
    """Interface for retrieving cropped image data for a detection."""

    def get_by_detection(self, detection_id: UUID) -> npt.NDArray[np.uint8]:
        """Return the image crop associated with the given detection."""
        ...
