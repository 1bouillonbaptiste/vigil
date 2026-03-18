from typing import Protocol

import numpy as np
import numpy.typing as npt

from vigil.business_logic.models.detection import BoundingBox


class DetectionModel(Protocol):
    """Abstract detection model."""

    def detect(self, data: npt.NDArray[np.uint8]) -> list[BoundingBox]:
        """Run the model on raw frame pixel data."""
        ...
