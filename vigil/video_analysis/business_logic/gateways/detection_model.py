from typing import Protocol

from vigil.shared_kernel.models.image import Image
from vigil.video_analysis.business_logic.models.detection import Prediction


class DetectionModel(Protocol):
    """Abstract detection model."""

    def detect(self, frames: list[Image]) -> list[list[Prediction]]:
        """Run the model on a batch of raw frame pixel data.

        Returns one list of Prediction per input frame, in the same order.
        """
        ...
