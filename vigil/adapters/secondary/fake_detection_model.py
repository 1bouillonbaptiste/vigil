import numpy as np
import numpy.typing as npt

from vigil.business_logic.gateways.detection_model import DetectionModel
from vigil.business_logic.models.detection import BoundingBox, ClassLabel, Prediction


class FakeDetectionModel(DetectionModel):
    """Detection model for testing purpose."""

    def detect(self, frames: list[npt.NDArray[np.uint8]]) -> list[list[Prediction]]:
        """Detect a person per frame."""
        return [
            [
                Prediction(
                    bbox=BoundingBox(center_x=1, center_y=1, width=1, height=1), confidence=0.8, label=ClassLabel.PERSON
                )
            ]
            for _ in frames
        ]
