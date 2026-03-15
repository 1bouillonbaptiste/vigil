from typing import Protocol

from vigil.business_logic.models.detection import Detection
from vigil.business_logic.models.frame import VideoFrame


class DetectionModel(Protocol):
    """Abstract detection model."""

    def detect(self, frame: VideoFrame) -> list[Detection]:
        """Run the model on a single frame."""
        ...
