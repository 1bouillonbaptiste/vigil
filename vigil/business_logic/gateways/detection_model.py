from typing import Protocol

import numpy as np
import numpy.typing as npt

from vigil.business_logic.models.detection import Prediction


class DetectionModel(Protocol):
    """Abstract detection model."""

    def detect(self, frames: list[npt.NDArray[np.uint8]]) -> list[list[Prediction]]:
        """Run the model on a batch of raw frame pixel data.

        Returns one list of Prediction per input frame, in the same order.
        """
        ...
